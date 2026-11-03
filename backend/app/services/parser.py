"""PGN parsing service using python-chess.

Converts raw PGN text into structured ``ParsedGame`` objects with opening
statistics and colour-split win-rate aggregations.
"""

from __future__ import annotations

import hashlib
import io
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Final

import chess
import chess.pgn

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

UNKNOWN: Final[str] = "Unknown"
RESULT_WIN: Final[str] = "win"
RESULT_DRAW: Final[str] = "draw"
RESULT_LOSS: Final[str] = "loss"
RESULT_UNKNOWN: Final[str] = "unknown"

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ParsedGame:
    """Structured representation of a parsed chess game."""

    game_id: str
    pgn: str
    opening_eco: str
    opening_name: str
    result: str          # 'win', 'draw', 'loss', or 'unknown'
    time_control: str
    played_as: str       # 'white' or 'black'
    num_moves: int
    moves: list[str]     # UCI move strings
    fens: list[str]      # FEN after each half-move


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class PGNParseError(Exception):
    """Raised when a PGN string cannot be parsed."""


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class PGNParser:
    """Parses PGN strings into structured game data.

    Parameters
    ----------
    player_username : str
        The username of the player whose perspective we adopt when
        determining ``played_as`` and ``result``.
    """

    def __init__(self, player_username: str) -> None:
        self.player_username: str = player_username.lower().strip()

    # -- Single game parsing --------------------------------------------------

    def parse_game(self, pgn_text: str) -> ParsedGame | None:
        """Parse a single PGN string into a :class:`ParsedGame`.

        Returns ``None`` if the PGN cannot be parsed.
        """
        try:
            game = chess.pgn.read_game(io.StringIO(pgn_text))
            if game is None:
                logger.warning("chess.pgn.read_game returned None")
                return None

            headers = game.headers

            # --- Determine played_as ---
            white_player: str = headers.get("White", UNKNOWN).lower().strip()
            black_player: str = headers.get("Black", UNKNOWN).lower().strip()

            if self.player_username in white_player or white_player in self.player_username:
                played_as = "white"
            elif self.player_username in black_player or black_player in self.player_username:
                played_as = "black"
            else:
                # Fall back to exact match on raw casing
                if headers.get("White", "").lower() == self.player_username:
                    played_as = "white"
                elif headers.get("Black", "").lower() == self.player_username:
                    played_as = "black"
                else:
                    logger.debug(
                        "Player '%s' not found in White='%s' / Black='%s'; defaulting to white",
                        self.player_username,
                        headers.get("White", ""),
                        headers.get("Black", ""),
                    )
                    played_as = "white"

            # --- Result ---
            raw_result: str = headers.get("Result", "*")
            result = self._interpret_result(raw_result, played_as)

            # --- Walk the mainline ---
            moves: list[str] = []
            fens: list[str] = []

            board = game.board()
            for move in game.mainline_moves():
                moves.append(move.uci())
                board.push(move)
                fens.append(board.fen())

            num_moves = (len(moves) + 1) // 2  # full moves

            # --- Game ID ---
            site: str = headers.get("Site", "")
            date: str = headers.get("Date", "")
            game_id = self._compute_game_id(site, date, white_player, black_player, pgn_text)

            eco = headers.get("ECO", UNKNOWN).strip()
            opening_name = self._extract_opening_name(headers, eco)

            return ParsedGame(
                game_id=game_id,
                pgn=pgn_text,
                opening_eco=eco,
                opening_name=opening_name,
                result=result,
                time_control=headers.get("TimeControl", UNKNOWN),
                played_as=played_as,
                num_moves=num_moves,
                moves=moves,
                fens=fens,
            )

        except Exception:
            logger.exception("Failed to parse PGN")
            return None

    @staticmethod
    def _extract_opening_name(headers: chess.pgn.Headers, eco: str) -> str:
        """Resolve a clean, descriptive opening name from PGN headers and ECO."""
        from app.utils import eco_to_opening_name

        # 1. Check ECOUrl header (used by Chess.com, e.g. "https://www.chess.com/openings/Queen-Pawn-Opening-London-System")
        eco_url = headers.get("ECOUrl", "").strip()
        if eco_url:
            slug = eco_url.rstrip("/").split("/")[-1]
            cleaned = slug.replace("-", " ")
            if "..." in cleaned:
                cleaned = cleaned.split("...")[0].rstrip(" 0123456789.")
            if cleaned and not cleaned.replace(" ", "").isdigit():
                return cleaned.strip()

        # 2. Check Opening header if present and not a generic event string
        raw_opening = headers.get("Opening", "").strip()
        generic_names = {
            "live chess", "unknown", "rated blitz game", "rated rapid game",
            "rated bullet game", "casual blitz game", "casual rapid game"
        }
        if raw_opening and raw_opening.lower() not in generic_names:
            return raw_opening

        # 3. Lookup standard name via ECO table
        if eco and eco != UNKNOWN:
            return eco_to_opening_name(eco)

        return "Queen's Pawn Game" if eco.startswith("D") else f"Opening {eco}" if eco != UNKNOWN else "Custom Game"

    # -- Batch parsing --------------------------------------------------------

    def parse_batch(self, pgn_texts: list[str]) -> list[ParsedGame]:
        """Parse multiple PGNs, silently skipping failures.

        Parameters
        ----------
        pgn_texts : list[str]
            Raw PGN strings to parse.

        Returns
        -------
        list[ParsedGame]
            Successfully parsed games.
        """
        parsed: list[ParsedGame] = []
        for idx, pgn in enumerate(pgn_texts):
            game = self.parse_game(pgn)
            if game is not None:
                parsed.append(game)
            else:
                logger.debug("Skipped unparsable PGN at index %d", idx)
        logger.info(
            "Parsed %d / %d PGNs successfully", len(parsed), len(pgn_texts)
        )
        return parsed

    # -- Aggregate statistics -------------------------------------------------

    @staticmethod
    def compute_opening_stats(games: list[ParsedGame]) -> list[dict]:
        """Aggregate opening statistics grouped by ECO code.

        Returns a list of dicts sorted by frequency (most played first)::

            [
                {
                    "eco": "B90",
                    "name": "Sicilian Najdorf",
                    "count": 15,
                    "win_rate": 0.60,
                    "draw_rate": 0.20,
                    "loss_rate": 0.20,
                    "avg_moves": 38.5,
                },
                ...
            ]
        """
        buckets: dict[str, dict] = defaultdict(
            lambda: {
                "name": UNKNOWN,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "total": 0,
                "total_moves": 0,
            }
        )

        for game in games:
            eco = game.opening_eco or UNKNOWN
            bucket = buckets[eco]
            if bucket["name"] == UNKNOWN or bucket["name"].lower() == "live chess":
                bucket["name"] = game.opening_name
            elif game.opening_name and game.opening_name != UNKNOWN and game.opening_name.lower() != "live chess":
                bucket["name"] = game.opening_name
            bucket["total"] += 1
            bucket["total_moves"] += game.num_moves

            if game.result == RESULT_WIN:
                bucket["wins"] += 1
            elif game.result == RESULT_DRAW:
                bucket["draws"] += 1
            elif game.result == RESULT_LOSS:
                bucket["losses"] += 1

        stats: list[dict] = []
        from app.utils import eco_to_opening_name
        for eco, b in buckets.items():
            total = b["total"]
            name = b["name"]
            if name == UNKNOWN or name.lower() == "live chess":
                name = eco_to_opening_name(eco)
            stats.append(
                {
                    "eco": eco,
                    "name": name,
                    "count": total,
                    "games": total,
                    "win_rate": round(b["wins"] / total, 4) if total else 0.0,
                    "draw_rate": round(b["draws"] / total, 4) if total else 0.0,
                    "loss_rate": round(b["losses"] / total, 4) if total else 0.0,
                    "avg_moves": round(b["total_moves"] / total, 1) if total else 0.0,
                }
            )

        stats.sort(key=lambda s: s["count"], reverse=True)
        return stats

    @staticmethod
    def compute_color_stats(games: list[ParsedGame]) -> dict:
        """Return win/draw/loss stats split by colour.

        Returns
        -------
        dict
            ``{"white": {...}, "black": {...}}`` each containing
            ``games``, ``wins``, ``draws``, ``losses``, ``win_rate``.
        """
        template = lambda: {"games": 0, "wins": 0, "draws": 0, "losses": 0}
        data: dict[str, dict[str, int]] = {
            "white": template(),
            "black": template(),
        }

        for game in games:
            color = game.played_as
            bucket = data[color]
            bucket["games"] += 1
            if game.result == RESULT_WIN:
                bucket["wins"] += 1
            elif game.result == RESULT_DRAW:
                bucket["draws"] += 1
            elif game.result == RESULT_LOSS:
                bucket["losses"] += 1

        result: dict = {}
        for color in ("white", "black"):
            b = data[color]
            total = b["games"]
            result[color] = {
                **b,
                "win_rate": round(b["wins"] / total, 4) if total else 0.0,
            }
        return result

    # -- Private helpers ------------------------------------------------------

    @staticmethod
    def _interpret_result(raw_result: str, played_as: str) -> str:
        """Map a PGN ``Result`` header to win/draw/loss from the player's POV."""
        if raw_result == "1/2-1/2":
            return RESULT_DRAW
        if raw_result == "1-0":
            return RESULT_WIN if played_as == "white" else RESULT_LOSS
        if raw_result == "0-1":
            return RESULT_WIN if played_as == "black" else RESULT_LOSS
        return RESULT_UNKNOWN

    @staticmethod
    def _compute_game_id(
        site: str,
        date: str,
        white: str,
        black: str,
        pgn_text: str,
    ) -> str:
        """Produce a deterministic ID for a game.

        If the ``Site`` header contains a URL (common on Chess.com / Lichess),
        it already serves as a unique identifier.  Otherwise, a SHA-256 digest
        of the full PGN text is used.
        """
        if site.startswith("http"):
            return site.rsplit("/", 1)[-1] if "/" in site else site

        digest_input = f"{site}|{date}|{white}|{black}|{pgn_text}"
        return hashlib.sha256(digest_input.encode()).hexdigest()[:16]
