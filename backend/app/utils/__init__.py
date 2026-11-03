"""Shared utility functions for Grandmaster Echo."""

import chess

# ── ECO lookup table (common codes) ──────────────────────────────────────────

ECO_NAMES: dict[str, str] = {
    "A00": "Uncommon Opening",
    "A01": "Nimzovich-Larsen Attack",
    "A02": "Bird's Opening",
    "A04": "Réti Opening",
    "A05": "Réti Opening",
    "A06": "Réti Opening",
    "A07": "King's Indian Attack",
    "A10": "English Opening",
    "A13": "English Opening",
    "A15": "English Opening: Anglo-Indian Defense",
    "A16": "English Opening",
    "A20": "English Opening",
    "A30": "English Opening: Symmetrical Variation",
    "A40": "Queen's Pawn Opening",
    "A41": "Queen's Pawn Game",
    "A43": "Old Benoni Defense",
    "A44": "Old Benoni Defense",
    "A45": "Queen's Pawn Game: Trompowsky Attack",
    "A46": "Queen's Pawn Game",
    "A48": "King's Indian Defense: London System",
    "A50": "Indian Defense",
    "A51": "Budapest Defense",
    "A52": "Budapest Defense",
    "A53": "Old Indian Defense",
    "A56": "Benoni Defense",
    "A57": "Benko Gambit",
    "A80": "Dutch Defense",
    "A85": "Dutch Defense",
    "A90": "Dutch Defense",
    "B00": "Uncommon King's Pawn Opening",
    "B01": "Scandinavian Defense",
    "B02": "Alekhine's Defense",
    "B06": "Modern Defense",
    "B07": "Pirc Defense",
    "B10": "Caro-Kann Defense",
    "B12": "Caro-Kann Defense",
    "B13": "Caro-Kann Defense: Exchange Variation",
    "B15": "Caro-Kann Defense",
    "B17": "Caro-Kann Defense: Steinitz Variation",
    "B20": "Sicilian Defense",
    "B21": "Sicilian Defense: Smith-Morra Gambit",
    "B22": "Sicilian Defense: Alapin Variation",
    "B23": "Sicilian Defense: Closed Variation",
    "B27": "Sicilian Defense",
    "B30": "Sicilian Defense",
    "B33": "Sicilian Defense: Sveshnikov Variation",
    "B40": "Sicilian Defense",
    "B44": "Sicilian Defense: Taimanov Variation",
    "B50": "Sicilian Defense",
    "B52": "Sicilian Defense: Canal-Sokolsky Attack",
    "B54": "Sicilian Defense",
    "B56": "Sicilian Defense",
    "B60": "Sicilian Defense: Richter-Rauzer",
    "B72": "Sicilian Defense: Dragon Variation",
    "B80": "Sicilian Defense: Scheveningen Variation",
    "B85": "Sicilian Defense: Scheveningen, Classical",
    "B90": "Sicilian Defense: Najdorf Variation",
    "B96": "Sicilian Defense: Najdorf",
    "C00": "French Defense",
    "C01": "French Defense: Exchange Variation",
    "C02": "French Defense: Advance Variation",
    "C03": "French Defense: Tarrasch Variation",
    "C10": "French Defense",
    "C11": "French Defense: Classical Variation",
    "C20": "King's Pawn Game",
    "C21": "Center Game",
    "C23": "Bishop's Opening",
    "C24": "Bishop's Opening: Berlin Defense",
    "C25": "Vienna Game",
    "C30": "King's Gambit",
    "C40": "King's Knight Opening",
    "C41": "Philidor Defense",
    "C42": "Petrov's Defense",
    "C44": "Scotch Game",
    "C45": "Scotch Game",
    "C46": "Three Knights Opening",
    "C47": "Four Knights Game",
    "C50": "Italian Game",
    "C51": "Evans Gambit",
    "C53": "Italian Game: Giuoco Piano",
    "C54": "Italian Game: Classical Variation",
    "C55": "Two Knights Defense",
    "C57": "Two Knights Defense: Traxler Counterattack",
    "C60": "Ruy López",
    "C62": "Ruy López: Steinitz Defense",
    "C63": "Ruy López: Schliemann Defense",
    "C65": "Ruy López: Berlin Defense",
    "C67": "Ruy López: Berlin, Open Variation",
    "C68": "Ruy López: Exchange Variation",
    "C70": "Ruy López",
    "C78": "Ruy López: Morphy Defense",
    "C80": "Ruy López: Open Variation",
    "C84": "Ruy López: Closed Variation",
    "C88": "Ruy López: Closed",
    "C89": "Ruy López: Marshall Attack",
    "C96": "Ruy López: Closed, Chigorin",
    "D00": "Queen's Pawn Game",
    "D01": "Richter-Veresov Attack",
    "D02": "Queen's Pawn Game: London System",
    "D04": "Queen's Pawn Game: Colle System",
    "D06": "Queen's Gambit",
    "D07": "Queen's Gambit: Chigorin Defense",
    "D10": "Queen's Gambit Declined: Slav Defense",
    "D13": "Queen's Gambit Declined: Slav, Exchange",
    "D15": "Queen's Gambit Declined: Slav",
    "D20": "Queen's Gambit Accepted",
    "D30": "Queen's Gambit Declined",
    "D31": "Queen's Gambit Declined",
    "D35": "Queen's Gambit Declined: Exchange Variation",
    "D37": "Queen's Gambit Declined",
    "D43": "Queen's Gambit Declined: Semi-Slav",
    "D45": "Queen's Gambit Declined: Semi-Slav",
    "D50": "Queen's Gambit Declined",
    "D52": "Queen's Gambit Declined: Cambridge Springs",
    "D60": "Queen's Gambit Declined: Orthodox Defense",
    "D70": "Neo-Grünfeld Defense",
    "D76": "Neo-Grünfeld Defense",
    "D80": "Grünfeld Defense",
    "D85": "Grünfeld Defense: Exchange Variation",
    "D90": "Grünfeld Defense",
    "E00": "Queen's Pawn Game: Catalan",
    "E04": "Catalan Opening: Open Defense",
    "E06": "Catalan Opening: Closed Variation",
    "E10": "Queen's Pawn Game",
    "E11": "Bogo-Indian Defense",
    "E12": "Queen's Indian Defense",
    "E15": "Queen's Indian Defense",
    "E17": "Queen's Indian Defense",
    "E20": "Nimzo-Indian Defense",
    "E21": "Nimzo-Indian Defense: Three Knights",
    "E32": "Nimzo-Indian Defense: Classical Variation",
    "E40": "Nimzo-Indian Defense",
    "E46": "Nimzo-Indian Defense",
    "E50": "Nimzo-Indian Defense",
    "E60": "King's Indian Defense",
    "E61": "King's Indian Defense",
    "E62": "King's Indian Defense: Fianchetto Variation",
    "E70": "King's Indian Defense",
    "E73": "King's Indian Defense",
    "E76": "King's Indian Defense: Four Pawns Attack",
    "E80": "King's Indian Defense: Sämisch Variation",
    "E90": "King's Indian Defense",
    "E97": "King's Indian Defense: Classical, Main Line",
    "E99": "King's Indian Defense: Classical, Main Line",
}


def determine_game_phase(fen: str) -> str:
    """Classify a position as *opening*, *middlegame*, or *endgame*.

    Heuristic
    ---------
    * Move number ≤ 10 → ``opening``
    * Fewer than 12 non-pawn, non-king pieces → ``endgame``
    * Otherwise → ``middlegame``
    """
    try:
        board = chess.Board(fen)
    except ValueError:
        return "middlegame"

    # Extract fullmove number from FEN (field 6, 1-indexed)
    fullmove = board.fullmove_number
    if fullmove <= 10:
        return "opening"

    # Count non-pawn, non-king pieces on the board
    piece_count = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is not None and piece.piece_type not in (chess.PAWN, chess.KING):
            piece_count += 1

    if piece_count < 6:
        return "endgame"

    return "middlegame"


def eco_to_opening_name(eco: str) -> str:
    """Return a human-readable opening name for an ECO code.

    Falls back to ``"Unknown Opening (<eco>)"`` when the code is not in the
    built-in lookup table.
    """
    return ECO_NAMES.get(eco.upper(), f"Unknown Opening ({eco})")
