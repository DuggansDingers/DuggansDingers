from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "duggans_dingers_logo.png"
STADIUMS_DIR = ASSETS_DIR / "stadiums"
EXPORTS_DIR = BASE_DIR / "data" / "exports"

APP_NAME = "DuggansDingers"
APP_TAGLINE = "MLB Home Run Intelligence"

NAV_ITEMS = (
    ("Dashboard", "⌂"),
    ("Rankings", "▤"),
    ("Team Cheat Sheets", "★"),
    ("Player Profile", "◉"),
    ("Trends", "↗"),
    ("Matchups", "⚔"),
    ("Park Factors", "◇"),
    ("Sportsbook Odds", "$"),
    ("Parlay Lab", "✦"),
)

TEAM_COLORS = {
    "NYY": ("#0C2340", "#C4CED4"), "BOS": ("#BD3039", "#0C2340"),
    "BAL": ("#DF4601", "#000000"), "TB": ("#092C5C", "#8FBCE6"),
    "TOR": ("#134A8E", "#E8291C"), "CLE": ("#00385D", "#E50022"),
    "DET": ("#0C2340", "#FA4616"), "CWS": ("#27251F", "#C4CED4"),
    "KC": ("#004687", "#BD9B60"), "MIN": ("#002B5C", "#D31145"),
    "HOU": ("#002D62", "#EB6E1F"), "SEA": ("#0C2C56", "#005C5C"),
    "TEX": ("#003278", "#C0111F"), "LAA": ("#BA0021", "#003263"),
    "OAK": ("#003831", "#EFB21E"), "ATH": ("#003831", "#EFB21E"),
    "ATL": ("#CE1141", "#13274F"), "NYM": ("#002D72", "#FF5910"),
    "PHI": ("#E81828", "#002D72"), "WSH": ("#AB0003", "#14225A"),
    "MIA": ("#00A3E0", "#EF3340"), "CHC": ("#0E3386", "#CC3433"),
    "STL": ("#C41E3A", "#0C2340"), "MIL": ("#12284B", "#FFC52F"),
    "CIN": ("#C6011F", "#000000"), "PIT": ("#FDB827", "#27251F"),
    "LAD": ("#005A9C", "#EF3E42"), "SF": ("#FD5A1E", "#27251F"),
    "SD": ("#2F241D", "#FFC425"), "ARI": ("#A71930", "#E3D4AD"),
    "COL": ("#33006F", "#C4CED4"),
}
