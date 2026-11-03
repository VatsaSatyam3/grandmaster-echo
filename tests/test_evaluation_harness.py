"""Evaluation Harness: Verifies deterministic-to-stochastic grounding.

Tests 20 sample player profiles to verify that opening preference assertions,
ECO distributions, and calculated win rates strictly align with the mathematical
output of the python-chess parser.
"""

import pytest
import chess
import chess.pgn
import io
from app.services.parser import PGNParser, ParsedGame
from app.services.bot import PlayerCloneBot

# 20 distinct player archetypes with controlled opening repertoires
PLAYER_ARCHETYPES = [
    {"name": "Kasparov_Clone", "fav_white": "B90", "fav_black": "E60", "style": "tactical"},
    {"name": "Karpov_Clone", "fav_white": "D37", "fav_black": "B12", "style": "positional"},
    {"name": "Carlsen_Clone", "fav_white": "C50", "fav_black": "B30", "style": "universal"},
    {"name": "Fischer_Clone", "fav_white": "B97", "fav_black": "E99", "style": "concrete"},
    {"name": "Tal_Clone", "fav_white": "C00", "fav_black": "B99", "style": "sacrificial"},
    {"name": "Petrosian_Clone", "fav_white": "A10", "fav_black": "A04", "style": "prophylactic"},
    {"name": "Nakamura_Clone", "fav_white": "B06", "fav_black": "C20", "style": "blitz_swindler"},
    {"name": "Capablanca_Clone", "fav_white": "C65", "fav_black": "D10", "style": "clarity"},
    {"name": "Alekhine_Clone", "fav_white": "B02", "fav_black": "C10", "style": "complex"},
    {"name": "Botvinnik_Clone", "fav_white": "D43", "fav_black": "E20", "style": "scientific"},
    {"name": "Smyslov_Clone", "fav_white": "A20", "fav_black": "B17", "style": "harmonic"},
    {"name": "Spassky_Clone", "fav_white": "C54", "fav_black": "A80", "style": "universal"},
    {"name": "Korchnoi_Clone", "fav_white": "C02", "fav_black": "E15", "style": "counter-puncher"},
    {"name": "Anand_Clone", "fav_white": "B80", "fav_black": "C88", "style": "lightning_prep"},
    {"name": "Kramnik_Clone", "fav_white": "E04", "fav_black": "C67", "style": "berlin_wall"},
    {"name": "Topalov_Clone", "fav_white": "D43", "fav_black": "B90", "style": "initiative"},
    {"name": "Caruana_Clone", "fav_white": "C84", "fav_black": "B33", "style": "deep_calculation"},
    {"name": "Ding_Clone", "fav_white": "D37", "fav_black": "E00", "style": "dynamic_solid"},
    {"name": "Giri_Clone", "fav_white": "C53", "fav_black": "B92", "style": "ironclad"},
    {"name": "Nepo_Clone", "fav_white": "C50", "fav_black": "B90", "style": "hyper_aggressive"},
]


def generate_synthetic_pgn(white: str, black: str, eco: str, result: str, moves_count: int = 10) -> str:
    """Generate valid syntactically sound PGN string."""
    headers = f"""[Event "Evaluation Match"]
[Site "GrandmasterEcho"]
[White "{white}"]
[Black "{black}"]
[Result "{result}"]
[ECO "{eco}"]
[Opening "Test Repertoire Opening {eco}"]

"""
    # Simple legal opening moves: 1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5
    moves = "1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. d3 Nf6 5. O-O O-O "
    return headers + moves + result


@pytest.mark.parametrize("archetype", PLAYER_ARCHETYPES)
def test_player_opening_preference_alignment(archetype):
    """Verify that python-chess parser extracts exact mathematical frequencies

    matching the player's true game history for 20 sample profiles.
    """
    player_name = archetype["name"]
    fav_white = archetype["fav_white"]
    fav_black = archetype["fav_black"]

    # Synthesize 15 games:
    # 8 as White: 6 with fav_white (4 wins, 2 draws), 2 with secondary A00
    # 7 as Black: 5 with fav_black (3 wins, 1 draw, 1 loss), 2 with secondary B00
    pgns = []
    
    # White games
    for _ in range(4):
        pgns.append(generate_synthetic_pgn(player_name, "Opponent", fav_white, "1-0"))
    for _ in range(2):
        pgns.append(generate_synthetic_pgn(player_name, "Opponent", fav_white, "1/2-1/2"))
    for _ in range(2):
        pgns.append(generate_synthetic_pgn(player_name, "Opponent", "A00", "0-1"))

    # Black games
    for _ in range(3):
        pgns.append(generate_synthetic_pgn("Opponent", player_name, fav_black, "0-1"))
    for _ in range(1):
        pgns.append(generate_synthetic_pgn("Opponent", player_name, fav_black, "1/2-1/2"))
    for _ in range(1):
        pgns.append(generate_synthetic_pgn("Opponent", player_name, fav_black, "1-0"))
    for _ in range(2):
        pgns.append(generate_synthetic_pgn("Opponent", player_name, "B00", "1-0"))

    # 1. Parse using PGNParser
    parser = PGNParser(player_username=player_name)
    parsed_games = parser.parse_batch(pgns)

    assert len(parsed_games) == 15, f"Expected 15 parsed games for {player_name}"

    # 2. Check Color Split
    color_stats = PGNParser.compute_color_stats(parsed_games)
    assert color_stats["white"]["games"] == 8
    assert color_stats["black"]["games"] == 7

    # White Win Rate: 4 wins out of 8 games = 0.50
    assert color_stats["white"]["wins"] == 4
    assert pytest.approx(color_stats["white"]["win_rate"], 0.01) == 0.50

    # Black Win Rate: 3 wins out of 7 games = ~0.428
    assert color_stats["black"]["wins"] == 3
    assert pytest.approx(color_stats["black"]["win_rate"], 0.01) == 3 / 7

    # 3. Check Opening Repertoire Frequencies
    white_games = [g for g in parsed_games if g.played_as == "white"]
    black_games = [g for g in parsed_games if g.played_as == "black"]

    white_opening_stats = PGNParser.compute_opening_stats(white_games)
    black_opening_stats = PGNParser.compute_opening_stats(black_games)

    # Top opening as White MUST strictly be fav_white
    assert white_opening_stats[0]["eco"] == fav_white
    assert white_opening_stats[0]["count"] == 6
    # 4 wins out of 6 games = 0.667
    assert pytest.approx(white_opening_stats[0]["win_rate"], 0.01) == 4 / 6
    assert pytest.approx(white_opening_stats[0]["draw_rate"], 0.01) == 2 / 6
    assert white_opening_stats[0]["loss_rate"] == 0.0

    # Top opening as Black MUST strictly be fav_black
    assert black_opening_stats[0]["eco"] == fav_black
    assert black_opening_stats[0]["count"] == 5
    # 3 wins out of 5 games = 0.60
    assert pytest.approx(black_opening_stats[0]["win_rate"], 0.01) == 0.60


def test_opening_book_matcher_accuracy():
    """Verify that PlayerCloneBot builds an opening book that mirrors move frequencies."""
    games_data = [
        {"moves": ["e2e4", "e7e5", "g1f3"], "played_as": "white"},
        {"moves": ["e2e4", "c7c5", "g1f3"], "played_as": "white"},
        {"moves": ["e2e4", "e7e5", "f1c4"], "played_as": "white"},
        {"moves": ["d2d4", "d7d5", "c2c4"], "played_as": "white"},
    ]

    book = PlayerCloneBot.build_opening_book(games_data)
    start_board = chess.Board()
    start_key = PlayerCloneBot._simplify_fen(start_board.fen())

    assert start_key in book
    # e2e4 was played 3 times, d2d4 was played 1 time
    assert book[start_key]["e2e4"] == 3
    assert book[start_key]["d2d4"] == 1

