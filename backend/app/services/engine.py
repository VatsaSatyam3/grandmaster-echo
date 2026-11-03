"""Stockfish analysis engine service.

Wraps python-chess's ``chess.engine.SimpleEngine`` to evaluate full games,
compute centipawn-loss metrics, and identify blunders / mistakes /
inaccuracies by game phase.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Final

import chess
import chess.engine

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_STOCKFISH_PATH: Final[str] = "/usr/bin/stockfish"
DEFAULT_DEPTH: Final[int] = 18
DEFAULT_THREADS: Final[int] = 2
DEFAULT_HASH_MB: Final[int] = 256

BLUNDER_THRESHOLD: Final[float] = 2.0   # pawns
MISTAKE_THRESHOLD: Final[float] = 1.0
INACCURACY_THRESHOLD: Final[float] = 0.5

# Phase thresholds
OPENING_MAX_MOVE: Final[int] = 10
OPENING_MIN_PIECES: Final[int] = 28
ENDGAME_MAX_PIECES: Final[int] = 12

# Rough ELO estimation based on average centipawn loss (ACPL)
# Source: lichess / community heuristics
ACPL_TO_ELO: Final[list[tuple[float, int]]] = [
    (10, 2800),
    (20, 2500),
    (30, 2200),
    (50, 1900),
    (75, 1600),
    (100, 1400),
    (150, 1200),
    (200, 1000),
    (300, 800),
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class MoveEvaluation:
    """Evaluation of a single half-move."""

    move_number: int
    fen: str
    eval_score: float    # in pawns, from the player's perspective
    eval_diff: float     # drop from previous eval (positive = lost advantage)
    is_blunder: bool
    best_move: str       # UCI notation
    played_move: str     # UCI notation
    phase: str           # 'opening', 'middlegame', 'endgame'


@dataclass(slots=True)
class GameAnalysis:
    """Aggregated analysis result for a single game."""

    game_id: str
    evaluations: list[MoveEvaluation]
    avg_centipawn_loss: float
    blunder_count: int
    mistake_count: int      # 1.0 < diff <= 2.0
    inaccuracy_count: int   # 0.5 < diff <= 1.0
    phase_blunders: dict[str, int] = field(
        default_factory=lambda: {"opening": 0, "middlegame": 0, "endgame": 0}
    )


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class EngineError(Exception):
    """Raised when the Stockfish engine encounters a fatal error."""


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class StockfishAnalyzer:
    """Analyzes chess positions using Stockfish via the UCI protocol.

    Parameters
    ----------
    stockfish_path : str
        Filesystem path to the Stockfish binary.
    depth : int
        Search depth (higher = slower but more accurate).
    threads : int
        Number of CPU threads for the engine.
    hash_size : int
        Hash table size in MB.

    Usage
    -----
    >>> with StockfishAnalyzer() as analyzer:
    ...     result = analyzer.analyze_game(fens, moves, "game1", "white")
    """

    def __init__(
        self,
        stockfish_path: str = DEFAULT_STOCKFISH_PATH,
        depth: int = DEFAULT_DEPTH,
        threads: int = DEFAULT_THREADS,
        hash_size: int = DEFAULT_HASH_MB,
    ) -> None:
        self.stockfish_path: str = stockfish_path
        self.depth: int = depth
        self.threads: int = threads
        self.hash_size: int = hash_size
        self._engine: chess.engine.SimpleEngine | None = None

    # -- Context manager & lifecycle ------------------------------------------

    def __enter__(self) -> "StockfishAnalyzer":
        self._start_engine()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        self.close()

    def __del__(self) -> None:
        self.close()

    def _start_engine(self) -> None:
        """Start the Stockfish process if not already running."""
        if self._engine is not None:
            return
        try:
            self._engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
            self._engine.configure(
                {"Threads": self.threads, "Hash": self.hash_size}
            )
            logger.info(
                "Stockfish engine started (path=%s, depth=%d, threads=%d, hash=%dMB)",
                self.stockfish_path,
                self.depth,
                self.threads,
                self.hash_size,
            )
        except Exception as exc:
            raise EngineError(
                f"Failed to start Stockfish at '{self.stockfish_path}': {exc}"
            ) from exc

    def close(self) -> None:
        """Shut down the Stockfish engine process gracefully."""
        if self._engine is not None:
            try:
                self._engine.quit()
            except chess.engine.EngineTerminatedError:
                pass
            except Exception:
                logger.debug("Non-critical error closing engine", exc_info=True)
            finally:
                self._engine = None
                logger.info("Stockfish engine closed")

    def _ensure_engine(self) -> chess.engine.SimpleEngine:
        """Return the running engine, starting it if necessary."""
        if self._engine is None:
            self._start_engine()
        assert self._engine is not None
        return self._engine

    # -- Core analysis --------------------------------------------------------

    def analyze_game(
        self,
        fens: list[str],
        moves: list[str],
        game_id: str,
        player_color: str,
    ) -> GameAnalysis:
        """Analyze every position in a game from the specified player's POV.

        Only the *player's own moves* are evaluated (every other half-move).
        Evaluations are normalized so that a positive score always favours the
        player.

        Parameters
        ----------
        fens : list[str]
            FEN strings after each half-move (length == len(moves)).
        moves : list[str]
            UCI move strings for every half-move.
        game_id : str
            Unique identifier for the game.
        player_color : str
            ``"white"`` or ``"black"``.

        Returns
        -------
        GameAnalysis
        """
        engine = self._ensure_engine()

        evaluations: list[MoveEvaluation] = []
        total_cp_loss: float = 0.0
        blunder_count: int = 0
        mistake_count: int = 0
        inaccuracy_count: int = 0
        phase_blunders: dict[str, int] = {"opening": 0, "middlegame": 0, "endgame": 0}

        # Determine which half-move indices belong to the player:
        # White moves at indices 0, 2, 4, …  Black moves at 1, 3, 5, …
        player_offset: int = 0 if player_color == "white" else 1
        is_white: bool = player_color == "white"

        prev_score: float | None = None

        for idx in range(len(moves)):
            is_player_move = (idx % 2) == player_offset

            # We need the FEN *before* the move was played to run analysis.
            if idx == 0:
                fen_before = chess.STARTING_FEN
            else:
                fen_before = fens[idx - 1]

            if not is_player_move:
                # Still update prev_score for continuity.
                try:
                    board = chess.Board(fen_before)
                    info = engine.analyse(board, chess.engine.Limit(depth=self.depth))
                    raw = self._score_to_pawns(info.get("score"))
                    prev_score = raw if is_white else -raw
                except Exception:
                    logger.debug("Skipped eval for opponent move idx %d", idx)
                continue

            move_number = (idx // 2) + 1

            try:
                board = chess.Board(fen_before)

                # Analyse the position before the move
                info = engine.analyse(
                    board,
                    chess.engine.Limit(depth=self.depth),
                )
                raw_score = self._score_to_pawns(info.get("score"))
                player_score_before = raw_score if is_white else -raw_score

                best_move_obj = info.get("pv", [None])[0]
                best_move_uci = best_move_obj.uci() if best_move_obj else moves[idx]

                # Analyse the position after the played move
                board_after = chess.Board(fens[idx])
                info_after = engine.analyse(
                    board_after,
                    chess.engine.Limit(depth=self.depth),
                )
                raw_score_after = self._score_to_pawns(info_after.get("score"))
                # After the move it's the opponent's turn, so flip sign
                player_score_after = -(raw_score_after) if is_white else raw_score_after

                eval_diff = max(0.0, player_score_before - player_score_after)

                is_blunder = eval_diff >= BLUNDER_THRESHOLD
                is_mistake = MISTAKE_THRESHOLD <= eval_diff < BLUNDER_THRESHOLD
                is_inaccuracy = INACCURACY_THRESHOLD <= eval_diff < MISTAKE_THRESHOLD

                phase = self._determine_phase(fen_before, move_number)

                evaluations.append(
                    MoveEvaluation(
                        move_number=move_number,
                        fen=fen_before,
                        eval_score=round(player_score_after, 2),
                        eval_diff=round(eval_diff, 2),
                        is_blunder=is_blunder,
                        best_move=best_move_uci,
                        played_move=moves[idx],
                        phase=phase,
                    )
                )

                total_cp_loss += eval_diff * 100  # convert to centipawns
                if is_blunder:
                    blunder_count += 1
                    phase_blunders[phase] += 1
                elif is_mistake:
                    mistake_count += 1
                elif is_inaccuracy:
                    inaccuracy_count += 1

                prev_score = player_score_after

            except chess.engine.EngineTerminatedError:
                logger.error("Engine crashed during analysis of game %s", game_id)
                self._engine = None
                self._start_engine()
                break
            except Exception:
                logger.warning(
                    "Error evaluating move %d in game %s", move_number, game_id,
                    exc_info=True,
                )
                continue

        num_evaluated = len(evaluations) or 1
        avg_cp_loss = round(total_cp_loss / num_evaluated, 1)

        return GameAnalysis(
            game_id=game_id,
            evaluations=evaluations,
            avg_centipawn_loss=avg_cp_loss,
            blunder_count=blunder_count,
            mistake_count=mistake_count,
            inaccuracy_count=inaccuracy_count,
            phase_blunders=phase_blunders,
        )

    # -- Batch analysis -------------------------------------------------------

    def analyze_batch(
        self,
        games: list[Any],
        max_games: int | None = None,
    ) -> list[GameAnalysis]:
        """Analyze multiple games.

        Parameters
        ----------
        games : list
            Each element must have ``fens``, ``moves``, ``game_id``, and
            ``played_as`` attributes (i.e. :class:`ParsedGame` objects).
        max_games : int | None
            Cap the number of games to analyse.  ``None`` means all.

        Returns
        -------
        list[GameAnalysis]
        """
        subset = games[:max_games] if max_games is not None else games
        results: list[GameAnalysis] = []

        for idx, game in enumerate(subset):
            logger.info(
                "Analyzing game %d/%d (id=%s) …",
                idx + 1,
                len(subset),
                game.game_id,
            )
            try:
                analysis = self.analyze_game(
                    fens=game.fens,
                    moves=game.moves,
                    game_id=game.game_id,
                    player_color=game.played_as,
                )
                results.append(analysis)
            except EngineError:
                logger.error("Engine error on game %s; stopping batch", game.game_id)
                break
            except Exception:
                logger.exception("Skipping game %s due to error", game.game_id)
                continue

        logger.info("Batch analysis complete: %d / %d games", len(results), len(subset))
        return results

    # -- Phase detection ------------------------------------------------------

    def _determine_phase(self, fen: str, move_number: int) -> str:
        """Classify a position into opening, middlegame, or endgame.

        Heuristics
        ----------
        * **Opening**: ``move_number <= 10`` *or* there are ≥ 28 pieces on the
          board.
        * **Endgame**: ≤ 12 pieces on the board *or* no queens remain.
        * **Middlegame**: everything else.
        """
        board = chess.Board(fen)
        piece_count = len(board.piece_map())
        has_queens = bool(board.queens)

        if move_number <= OPENING_MAX_MOVE or piece_count >= OPENING_MIN_PIECES:
            return "opening"
        if piece_count <= ENDGAME_MAX_PIECES or not has_queens:
            return "endgame"
        return "middlegame"

    # -- Player-wide statistics -----------------------------------------------

    def compute_player_stats(self, analyses: list[GameAnalysis]) -> dict:
        """Aggregate statistics across all analysed games.

        Returns
        -------
        dict
            Keys: ``overall_avg_centipawn_loss``, ``overall_blunder_rate``,
            ``phase_weakness``, ``consistency_score``, ``estimated_elo``.
        """
        if not analyses:
            return {
                "overall_avg_centipawn_loss": 0.0,
                "overall_blunder_rate": 0.0,
                "phase_weakness": "unknown",
                "consistency_score": 0.0,
                "estimated_elo": 0,
            }

        total_acpl = sum(a.avg_centipawn_loss for a in analyses)
        overall_acpl = round(total_acpl / len(analyses), 1)

        total_blunders = sum(a.blunder_count for a in analyses)
        blunder_rate = round(total_blunders / len(analyses), 2)

        # Phase weakness: which phase has the most blunders overall
        phase_totals: dict[str, int] = {"opening": 0, "middlegame": 0, "endgame": 0}
        for a in analyses:
            for phase, count in a.phase_blunders.items():
                phase_totals[phase] += count
        phase_weakness = max(phase_totals, key=phase_totals.get)  # type: ignore[arg-type]

        # Consistency: standard deviation of ACPL across games
        mean_acpl = overall_acpl
        variance = sum((a.avg_centipawn_loss - mean_acpl) ** 2 for a in analyses) / len(analyses)
        consistency = round(math.sqrt(variance), 1)

        estimated_elo = self._estimate_elo(overall_acpl)

        return {
            "overall_avg_centipawn_loss": overall_acpl,
            "overall_blunder_rate": blunder_rate,
            "phase_weakness": phase_weakness,
            "consistency_score": consistency,
            "estimated_elo": estimated_elo,
        }

    # -- Private helpers ------------------------------------------------------

    @staticmethod
    def _score_to_pawns(score: chess.engine.PovScore | None) -> float:
        """Convert a ``PovScore`` to a float in *pawns* from White's POV.

        Mate scores are clamped to ±100.
        """
        if score is None:
            return 0.0

        white_score = score.white()

        if white_score.is_mate():
            mate_in = white_score.mate()
            # Positive mate_in = White is winning
            return 100.0 if mate_in > 0 else -100.0  # type: ignore[return-value]

        cp = white_score.score()
        if cp is None:
            return 0.0
        return cp / 100.0

    @staticmethod
    def _estimate_elo(acpl: float) -> int:
        """Rough ELO estimation based on average centipawn loss."""
        for threshold, elo in ACPL_TO_ELO:
            if acpl <= threshold:
                return elo
        return 600  # very high ACPL → beginner
