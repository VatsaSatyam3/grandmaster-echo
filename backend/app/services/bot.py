"""Clone bot service that mimics a specific player's chess style.

Combines an opening book derived from the player's actual games with
Stockfish limited-strength play and probabilistic blunder injection to
produce moves that *feel* like the original player.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import Any, Final

import chess
import chess.engine

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_STOCKFISH_PATH: Final[str] = "/usr/bin/stockfish"
OPENING_BOOK_DEPTH: Final[int] = 15       # half-moves from each game to record
MULTIPV_COUNT: Final[int] = 5             # number of engine lines for clone move
DEFAULT_MOVE_TIME: Final[float] = 0.5     # seconds per move for Stockfish
MIN_ELO_LIMIT: Final[int] = 1320          # UCI_Elo lower bound in Stockfish
MAX_ELO_LIMIT: Final[int] = 3190          # UCI_Elo upper bound in Stockfish

MOVE_SOURCE_BOOK: Final[str] = "opening_book"
MOVE_SOURCE_CLONE: Final[str] = "stockfish_clone"
MOVE_SOURCE_ENGINE: Final[str] = "engine"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BotMove:
    """A move returned by the clone bot."""

    move: str           # UCI notation
    explanation: str    # Human-readable explanation
    source: str         # 'opening_book', 'stockfish_clone', or 'engine'
    confidence: float   # 0.0 – 1.0


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class BotError(Exception):
    """Raised when the bot encounters an unrecoverable error."""


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class PlayerCloneBot:
    """A chess bot that mimics a specific player's style.

    Strategy
    --------
    1. **Opening Book** – If the current position matches a position from the
       player's historical games, play their most frequent move, weighted by
       frequency.
    2. **Stockfish Clone** – Out of book, use Stockfish with
       ``UCI_LimitStrength`` / ``UCI_Elo`` matching the player's estimated
       rating.  Blunders are injected probabilistically to match the player's
       observed blunder rate.
    3. **Fallback** – Pure Stockfish at limited strength if anything else
       fails.

    Parameters
    ----------
    stockfish_path : str
        Filesystem path to the Stockfish binary.
    player_profile : dict
        Must contain at least ``estimated_elo`` (int) and ``blunder_rate``
        (float, 0–1).  Optionally ``phase_weakness``.
    opening_book : dict[str, dict[str, int]]
        Maps a *simplified FEN* → ``{uci_move: frequency_count}``.
        Can be empty; use :meth:`build_opening_book` to populate.
    """

    def __init__(
        self,
        stockfish_path: str,
        player_profile: dict[str, Any],
        opening_book: dict[str, dict[str, int]],
    ) -> None:
        self.stockfish_path: str = stockfish_path
        self.player_profile: dict[str, Any] = player_profile
        self.opening_book: dict[str, dict[str, int]] = opening_book

        self._estimated_elo: int = int(player_profile.get("estimated_elo", 1500))
        self._blunder_rate: float = float(player_profile.get("blunder_rate", 0.05))
        self._phase_weakness: str = str(player_profile.get("phase_weakness", "middlegame"))

        self._engine: chess.engine.SimpleEngine | None = None
        try:
            self._start_engine()
        except Exception as exc:
            logger.warning("Stockfish engine not available at %s (%s). Will use opening book and heuristic fallbacks.", self.stockfish_path, exc)

        logger.info(
            "PlayerCloneBot initialised (elo=%d, blunder_rate=%.2f, book_positions=%d)",
            self._estimated_elo,
            self._blunder_rate,
            len(self.opening_book),
        )

    # -- Context manager & lifecycle ------------------------------------------

    def __enter__(self) -> "PlayerCloneBot":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        self.close()

    def __del__(self) -> None:
        self.close()

    def _start_engine(self) -> None:
        """Start and configure the Stockfish process."""
        if self._engine is not None:
            return
        try:
            self._engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
            clamped_elo = max(MIN_ELO_LIMIT, min(self._estimated_elo, MAX_ELO_LIMIT))
            self._engine.configure(
                {
                    "UCI_LimitStrength": True,
                    "UCI_Elo": clamped_elo,
                    "Threads": 1,
                    "Hash": 64,
                }
            )
            logger.info("Stockfish engine started for bot (elo_limit=%d)", clamped_elo)
        except Exception as exc:
            raise BotError(f"Failed to start Stockfish: {exc}") from exc

    def close(self) -> None:
        """Shut down the engine process."""
        if self._engine is not None:
            try:
                self._engine.quit()
            except chess.engine.EngineTerminatedError:
                pass
            except Exception:
                logger.debug("Non-critical error closing bot engine", exc_info=True)
            finally:
                self._engine = None
                logger.info("Bot engine closed")

    def _ensure_engine(self) -> chess.engine.SimpleEngine:
        if self._engine is None:
            self._start_engine()
        assert self._engine is not None
        return self._engine

    # -- Public API -----------------------------------------------------------

    def get_move(self, fen: str) -> BotMove:
        """Return the bot's move for the given position.

        Parameters
        ----------
        fen : str
            A valid FEN string.

        Returns
        -------
        BotMove
        """
        # 1. Check opening book
        book_move = self._check_opening_book(fen)
        if book_move is not None:
            logger.debug("Book move found: %s", book_move.move)
            return book_move

        # 2. Stockfish clone (with blunder injection)
        try:
            clone_move = self._stockfish_clone_move(fen)
            logger.debug("Clone move: %s (source=%s)", clone_move.move, clone_move.source)
            return clone_move
        except Exception:
            logger.warning("Clone move failed; falling back to pure engine", exc_info=True)

        # 3. Fallback – pure engine
        return self._fallback_engine_move(fen)

    # -- Opening book ---------------------------------------------------------

    def _check_opening_book(self, fen: str) -> BotMove | None:
        """Look up *fen* in the opening book.

        If multiple moves exist, one is selected with probability
        proportional to its observed frequency.
        """
        key = self._simplify_fen(fen)
        move_freqs = self.opening_book.get(key)
        if not move_freqs:
            return None

        # Validate that at least one move is legal
        board = chess.Board(fen)
        legal_uci = {m.uci() for m in board.legal_moves}
        valid_moves = {m: c for m, c in move_freqs.items() if m in legal_uci}
        if not valid_moves:
            return None

        # Weighted random selection
        moves = list(valid_moves.keys())
        weights = list(valid_moves.values())
        total = sum(weights)
        chosen_move = random.choices(moves, weights=weights, k=1)[0]
        chosen_freq = valid_moves[chosen_move]

        confidence = min(1.0, chosen_freq / max(total, 1))

        return BotMove(
            move=chosen_move,
            explanation=(
                f"Opening book move (seen {chosen_freq}/{total} times in player's games)"
            ),
            source=MOVE_SOURCE_BOOK,
            confidence=round(confidence, 2),
        )

    # -- Clone move -----------------------------------------------------------

    def _stockfish_clone_move(self, fen: str) -> BotMove:
        """Use Stockfish at limited strength, optionally injecting a blunder.

        With probability equal to the player's blunder rate, a suboptimal move
        is chosen from the top ``MULTIPV_COUNT`` engine lines.
        """
        engine = self._ensure_engine()
        board = chess.Board(fen)

        # Get multiple principal variations
        results = engine.analyse(
            board,
            chess.engine.Limit(time=DEFAULT_MOVE_TIME),
            multipv=MULTIPV_COUNT,
        )

        if not results:
            raise BotError("Engine returned no results")

        # Ensure results is a list
        if not isinstance(results, list):
            results = [results]

        # Extract moves and scores
        candidate_moves: list[tuple[str, float]] = []
        for info in results:
            pv = info.get("pv")
            score = info.get("score")
            if pv and score:
                move_uci = pv[0].uci()
                # Score from the side to move
                cp = score.relative.score(mate_score=10000)
                candidate_moves.append((move_uci, cp if cp is not None else 0))

        if not candidate_moves:
            raise BotError("No candidate moves extracted from engine")

        best_move_uci = candidate_moves[0][0]

        # Decide whether to inject a blunder
        inject_blunder = (
            len(candidate_moves) > 1 and random.random() < self._blunder_rate
        )

        if inject_blunder:
            # Pick a non-best move, weighted toward worse options
            non_best = candidate_moves[1:]
            # Higher weight for worse moves (lower index in sorted-by-score = better)
            weights = [i + 1 for i in range(len(non_best))]
            chosen_move, chosen_score = random.choices(non_best, weights=weights, k=1)[0]
            explanation = (
                f"Intentional sub-optimal move to match player blunder pattern "
                f"(best was {best_move_uci})"
            )
            source = MOVE_SOURCE_CLONE
            # Confidence is lower for injected blunders
            confidence = round(0.3 + random.random() * 0.2, 2)
        else:
            chosen_move = best_move_uci
            explanation = f"Stockfish clone move at ~{self._estimated_elo} ELO"
            source = MOVE_SOURCE_CLONE
            confidence = round(0.7 + random.random() * 0.25, 2)

        return BotMove(
            move=chosen_move,
            explanation=explanation,
            source=source,
            confidence=confidence,
        )

    # -- Fallback engine move -------------------------------------------------

    def _fallback_engine_move(self, fen: str) -> BotMove:
        """Pure Stockfish move as a last resort."""
        try:
            engine = self._ensure_engine()
            board = chess.Board(fen)
            result = engine.play(board, chess.engine.Limit(time=DEFAULT_MOVE_TIME))
            move_uci = result.move.uci() if result.move else "0000"

            return BotMove(
                move=move_uci,
                explanation="Fallback engine move (no book or clone available)",
                source=MOVE_SOURCE_ENGINE,
                confidence=0.5,
            )
        except Exception as exc:
            # Absolute last resort: pick a random legal move
            logger.error("Engine fallback failed: %s", exc)
            board = chess.Board(fen)
            legal = list(board.legal_moves)
            if not legal:
                raise BotError("No legal moves in position") from exc
            move = random.choice(legal)
            return BotMove(
                move=move.uci(),
                explanation="Random legal move (engine unavailable)",
                source=MOVE_SOURCE_ENGINE,
                confidence=0.1,
            )

    # -- Opening book builder -------------------------------------------------

    @staticmethod
    def build_opening_book(
        games_data: list[dict[str, Any]],
    ) -> dict[str, dict[str, int]]:
        """Build an opening book from the player's parsed games.

        For each game, the player's moves in the first
        ``OPENING_BOOK_DEPTH`` half-moves are recorded as
        ``simplified_fen → {uci_move: count}`` mappings.

        Parameters
        ----------
        games_data : list[dict]
            Each dict must have ``"moves"`` (list of UCI strings),
            ``"played_as"`` (``"white"`` or ``"black"``), and optionally
            ``"fens"`` (list of FEN strings after each move).

        Returns
        -------
        dict[str, dict[str, int]]
            The opening book mapping.
        """
        book: dict[str, dict[str, int]] = {}

        for game in games_data:
            moves: list[str] = game.get("moves", [])
            played_as: str = game.get("played_as", "white")
            fens: list[str] = game.get("fens", [])

            player_offset = 0 if played_as == "white" else 1
            board = chess.Board()

            limit = min(len(moves), OPENING_BOOK_DEPTH)
            for idx in range(limit):
                move_uci = moves[idx]
                is_player_move = (idx % 2) == player_offset

                if is_player_move:
                    fen_key = PlayerCloneBot._simplify_fen(board.fen())
                    if fen_key not in book:
                        book[fen_key] = {}
                    book[fen_key][move_uci] = book[fen_key].get(move_uci, 0) + 1

                try:
                    board.push_uci(move_uci)
                except (chess.IllegalMoveError, chess.InvalidMoveError):
                    logger.debug(
                        "Illegal move '%s' at index %d; stopping book build for this game",
                        move_uci,
                        idx,
                    )
                    break

        logger.info(
            "Opening book built: %d unique positions, %d total move entries",
            len(book),
            sum(sum(v.values()) for v in book.values()),
        )
        return book

    # -- Helpers --------------------------------------------------------------

    @staticmethod
    def _simplify_fen(fen: str) -> str:
        """Strip the move counters from a FEN to improve position matching.

        A full FEN has 6 space-separated fields.  The last two (half-move
        clock and full-move number) are irrelevant for opening-book look-ups.

        Example::

            "rnbqkbnr/pppppppp/… w KQkq - 0 1"
            → "rnbqkbnr/pppppppp/… w KQkq -"
        """
        parts = fen.split()
        return " ".join(parts[:4]) if len(parts) >= 4 else fen
