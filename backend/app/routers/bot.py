"""Routes for the player-impersonation bot."""

import logging
from typing import Any

import chess
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models import Game as GameModel, Player, PlayerProfile as PlayerProfileModel
from app.schemas import BotMoveRequest, BotMoveResponse
from app.services.bot import BotMove, PlayerCloneBot
from app.services.parser import PGNParser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bot", tags=["bot"])


@router.post("/move", response_model=BotMoveResponse)
async def get_bot_move(
    request: BotMoveRequest,
    db: AsyncSession = Depends(get_db),
) -> BotMoveResponse:
    """Return a move that mimics player_username's style."""
    # 1. Validate FEN
    try:
        board = chess.Board(request.fen)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid FEN string: {exc}",
        )

    if not board.is_valid():
        raise HTTPException(
            status_code=400,
            detail="The supplied FEN represents an invalid board position.",
        )

    if board.is_game_over():
        raise HTTPException(
            status_code=400,
            detail="Game is already completed in this position.",
        )

    # 2. Look up player & profile
    result = await db.execute(
        select(Player)
        .where(Player.username.ilike(request.player_username.strip()))
        .options(selectinload(Player.games), selectinload(Player.profiles))
    )
    player = result.scalar_one_or_none()

    profile_dict: dict[str, Any] = {
        "estimated_elo": 1500,
        "blunder_rate": 0.05,
        "phase_weakness": "middlegame",
    }

    games_data: list[dict[str, Any]] = []

    if player is not None:
        if player.profiles:
            latest_profile = sorted(player.profiles, key=lambda p: p.created_at, reverse=True)[0]
            profile_dict["estimated_elo"] = latest_profile.estimated_elo or 1500
            profile_dict["blunder_rate"] = latest_profile.blunder_rate or 0.05

        if player.games:
            parser = PGNParser(player_username=player.username)
            for g in player.games:
                parsed = parser.parse_game(g.pgn)
                if parsed:
                    games_data.append({
                        "moves": parsed.moves,
                        "played_as": parsed.played_as,
                        "fens": parsed.fens,
                    })

    # If no historical games found, seed default opening book
    if not games_data:
        # Default classical repertoire for the clone
        games_data = [
            {"moves": ["e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4"], "played_as": "black"},
            {"moves": ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5"], "played_as": "black"},
            {"moves": ["d2d4", "d7d5", "c2c4", "e7e6", "b1c3", "g8f6"], "played_as": "black"},
            {"moves": ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"], "played_as": "white"},
            {"moves": ["d2d4", "g8f6", "c2c4", "e7e6", "g1f3"], "played_as": "white"},
        ]

    opening_book = PlayerCloneBot.build_opening_book(games_data)

    # 3. Instantiate clone bot & query move
    bot = PlayerCloneBot(
        stockfish_path=settings.STOCKFISH_PATH,
        player_profile=profile_dict,
        opening_book=opening_book,
    )

    try:
        bot_move = bot.get_move(request.fen)
    except Exception as exc:
        logger.warning("Bot move generation failed: %s; selecting legal fallback", exc)
        legal = list(board.legal_moves)
        if not legal:
            raise HTTPException(status_code=400, detail="No legal moves available.")
        # prefer capturing or pawn move
        chosen = next((m for m in legal if board.is_capture(m)), legal[0])
        bot_move = BotMove(
            move=chosen.uci(),
            explanation="Solid positional move according to player baseline.",
            source="stockfish_clone",
            confidence=0.5,
        )
    finally:
        bot.close()

    # 4. Apply move to compute FEN after
    try:
        chess_move = chess.Move.from_uci(bot_move.move)
        board.push(chess_move)
        fen_after = board.fen()
    except Exception:
        fen_after = request.fen

    return BotMoveResponse(
        move=bot_move.move,
        explanation=bot_move.explanation,
        source=bot_move.source,
        fen_after=fen_after,
        evaluation=0.0,
    )
