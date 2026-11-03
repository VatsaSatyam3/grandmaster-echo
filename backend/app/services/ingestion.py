"""Async service for fetching chess games from Chess.com and Lichess APIs.

Supports rate-limit–aware fetching with exponential backoff, proper timeout
management, and structured logging.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Final

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CHESSCOM_BASE_URL: Final[str] = "https://api.chess.com/pub/player"
LICHESS_BASE_URL: Final[str] = "https://lichess.org/api/games/user"

DEFAULT_TIMEOUT_SECONDS: Final[float] = 30.0
MAX_RETRIES: Final[int] = 5
INITIAL_BACKOFF_SECONDS: Final[float] = 1.0
BACKOFF_MULTIPLIER: Final[float] = 2.0

USER_AGENT: Final[str] = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

SUPPORTED_PLATFORMS: Final[frozenset[str]] = frozenset({"chesscom", "lichess"})


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class IngestionError(Exception):
    """Base exception for game ingestion failures."""


class PlatformNotSupportedError(IngestionError):
    """Raised when an unsupported platform is specified."""


class FetchError(IngestionError):
    """Raised when fetching games from an API fails after all retries."""


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ChessGameIngester:
    """Fetches games from Chess.com or Lichess for a given player.

    Parameters
    ----------
    platform : str
        Either ``"chesscom"`` or ``"lichess"``.
    username : str
        The player's username on the chosen platform.

    Raises
    ------
    PlatformNotSupportedError
        If *platform* is not one of the supported values.

    Examples
    --------
    >>> async with ChessGameIngester("lichess", "DrNykterstein") as ingester:
    ...     pgns = await ingester.fetch_games(max_games=50)
    """

    def __init__(self, platform: str, username: str) -> None:
        raw_platform = platform.lower().strip().replace(".", "")
        if "chess" in raw_platform:
            self.platform = "chesscom"
        elif "lichess" in raw_platform:
            self.platform = "lichess"
        else:
            self.platform = raw_platform
        self.username: str = username.strip()

        if self.platform not in SUPPORTED_PLATFORMS:
            raise PlatformNotSupportedError(
                f"Platform '{self.platform}' is not supported. "
                f"Choose from: {', '.join(sorted(SUPPORTED_PLATFORMS))}"
            )

        self._client: httpx.AsyncClient | None = None
        logger.info(
            "ChessGameIngester created for platform=%s, username=%s",
            self.platform,
            self.username,
        )

    # -- Async context manager ------------------------------------------------

    async def __aenter__(self) -> "ChessGameIngester":
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(DEFAULT_TIMEOUT_SECONDS),
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
            },
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        await self.close()

    async def close(self) -> None:
        """Gracefully close the underlying HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # -- Internal helpers -----------------------------------------------------

    def _ensure_client(self) -> httpx.AsyncClient:
        """Return the active client, creating one if needed."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(DEFAULT_TIMEOUT_SECONDS),
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                },
                follow_redirects=True,
            )
        return self._client

    async def _request_with_retries(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Perform an HTTP GET with exponential backoff on transient failures.

        Retries on 429 (rate-limited) and 5xx server errors up to
        ``MAX_RETRIES`` times.

        Returns
        -------
        httpx.Response
            A successful response (2xx status code).

        Raises
        ------
        FetchError
            If all retries are exhausted or a non-retryable error occurs.
        """
        client = self._ensure_client()
        backoff = INITIAL_BACKOFF_SECONDS

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.debug("GET %s  (attempt %d/%d)", url, attempt, MAX_RETRIES)
                response = await client.get(url, headers=headers or {})

                if response.status_code == 200:
                    return response

                if response.status_code == 404:
                    raise FetchError(
                        f"Resource not found (404): {url}  — check username or URL."
                    )

                if response.status_code == 429 or response.status_code >= 500:
                    retry_after = float(
                        response.headers.get("Retry-After", backoff)
                    )
                    wait = max(retry_after, backoff)
                    logger.warning(
                        "Received %d from %s. Retrying in %.1fs …",
                        response.status_code,
                        url,
                        wait,
                    )
                    await asyncio.sleep(wait)
                    backoff *= BACKOFF_MULTIPLIER
                    continue

                # Non-retryable client error
                raise FetchError(
                    f"HTTP {response.status_code} from {url}: {response.text[:200]}"
                )

            except httpx.TimeoutException as exc:
                logger.warning("Timeout on %s (attempt %d): %s", url, attempt, exc)
                await asyncio.sleep(backoff)
                backoff *= BACKOFF_MULTIPLIER

            except httpx.RequestError as exc:
                logger.warning(
                    "Request error on %s (attempt %d): %s", url, attempt, exc
                )
                await asyncio.sleep(backoff)
                backoff *= BACKOFF_MULTIPLIER

        raise FetchError(f"All {MAX_RETRIES} retries exhausted for {url}")

    # -- Public API -----------------------------------------------------------

    async def fetch_games(self, max_games: int = 200) -> list[str]:
        """Fetch up to *max_games* PGN strings from the configured platform.

        Parameters
        ----------
        max_games : int, optional
            Maximum number of games to retrieve (default ``200``).

        Returns
        -------
        list[str]
            A list of PGN text strings, one per game.
        """
        if max_games < 1:
            raise ValueError("max_games must be >= 1")

        logger.info(
            "Fetching up to %d games for %s on %s",
            max_games,
            self.username,
            self.platform,
        )

        if self.platform == "chesscom":
            return await self._fetch_chesscom_games(max_games)
        return await self._fetch_lichess_games(max_games)

    # -- Chess.com ------------------------------------------------------------

    async def _fetch_chesscom_games(self, max_games: int) -> list[str]:
        """Fetch games from Chess.com's public API.

        Flow
        ----
        1. ``GET /pub/player/{username}/games/archives`` → list of monthly
           archive URLs.
        2. Iterate archives **most-recent-first**, fetching game objects and
           extracting their ``pgn`` field.
        3. Stop as soon as *max_games* PGNs have been collected.
        """
        archives_url = f"{CHESSCOM_BASE_URL}/{self.username}/games/archives"
        archives_resp = await self._request_with_retries(archives_url)
        archive_data = archives_resp.json()

        archive_urls: list[str] = archive_data.get("archives", [])
        if not archive_urls:
            logger.warning("No archives found for Chess.com user '%s'", self.username)
            return []

        # Most recent archives first
        archive_urls = list(reversed(archive_urls))

        pgns: list[str] = []

        for archive_url in archive_urls:
            if len(pgns) >= max_games:
                break

            try:
                resp = await self._request_with_retries(archive_url)
                month_data = resp.json()
            except FetchError:
                logger.warning("Skipping archive %s due to fetch error", archive_url)
                continue

            games: list[dict] = month_data.get("games", [])

            for game in reversed(games):  # most recent game first within month
                pgn_text: str | None = game.get("pgn")
                if pgn_text:
                    pgns.append(pgn_text.strip())
                    if len(pgns) >= max_games:
                        break

        logger.info(
            "Fetched %d Chess.com games for '%s'", len(pgns), self.username
        )
        return pgns

    # -- Lichess --------------------------------------------------------------

    async def _fetch_lichess_games(self, max_games: int) -> list[str]:
        """Fetch games from the Lichess API.

        Flow
        ----
        1. ``GET /api/games/user/{username}?max={max_games}&pgnInBody=true``
           with ``Accept: application/x-chess-pgn``.
        2. Split the response text on double newlines to separate individual
           PGN blocks.
        """
        url = (
            f"{LICHESS_BASE_URL}/{self.username}"
            f"?max={max_games}&pgnInBody=true"
        )
        headers = {"Accept": "application/x-chess-pgn"}

        resp = await self._request_with_retries(url, headers=headers)
        raw_text: str = resp.text.strip()

        if not raw_text:
            logger.warning("No games returned by Lichess for '%s'", self.username)
            return []

        # Lichess PGNs are separated by a blank line between games.
        # Each game's PGN has header lines, an empty line, and the move text.
        # Games are separated by two consecutive newlines after the move text.
        raw_games = raw_text.split("\n\n\n")
        pgns: list[str] = [g.strip() for g in raw_games if g.strip()]

        # If the simple triple-newline split didn't work (some Lichess
        # responses use only double-newline between games), fall back to
        # detecting the start of a new PGN by the "[Event " tag.
        if len(pgns) <= 1 and raw_text.count("[Event ") > 1:
            parts: list[str] = []
            current: list[str] = []
            for line in raw_text.splitlines():
                if line.startswith("[Event ") and current:
                    parts.append("\n".join(current).strip())
                    current = []
                current.append(line)
            if current:
                parts.append("\n".join(current).strip())
            pgns = [p for p in parts if p]

        logger.info(
            "Fetched %d Lichess games for '%s'", len(pgns), self.username
        )
        return pgns[: max_games]
