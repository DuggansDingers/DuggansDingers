from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from components.ui import image_data

BASE_DIR = Path(__file__).resolve().parents[1]
SCENE_DIR = BASE_DIR / "assets" / "stadium_scenes"
PHOTO_SCENE_DIR = BASE_DIR / "assets" / "stadium_photo_scenes"

SCENES = tuple(sorted(SCENE_DIR.glob("scene_*.jpg")))
TEAM_SCENES = {
    path.stem.upper(): path
    for path in SCENE_DIR.glob("*.jpg")
    if not path.stem.startswith("scene_")
}
PHOTO_TEAM_SCENES = {
    path.stem.upper(): path
    for path in PHOTO_SCENE_DIR.glob("*.jpg")
}

TEAM_ALIASES = {
    "ARIZONA DIAMONDBACKS": "ARI", "DIAMONDBACKS": "ARI",
    "ATLANTA BRAVES": "ATL", "BRAVES": "ATL",
    "BALTIMORE ORIOLES": "BAL", "ORIOLES": "BAL",
    "BOSTON RED SOX": "BOS", "RED SOX": "BOS",
    "CHICAGO CUBS": "CHC", "CUBS": "CHC",
    "CHICAGO WHITE SOX": "CWS", "WHITE SOX": "CWS",
    "CINCINNATI REDS": "CIN", "REDS": "CIN",
    "CLEVELAND GUARDIANS": "CLE", "GUARDIANS": "CLE",
    "COLORADO ROCKIES": "COL", "ROCKIES": "COL",
    "DETROIT TIGERS": "DET", "TIGERS": "DET",
    "HOUSTON ASTROS": "HOU", "ASTROS": "HOU",
    "KANSAS CITY ROYALS": "KC", "ROYALS": "KC", "KCR": "KC",
    "LOS ANGELES ANGELS": "LAA", "ANGELS": "LAA",
    "LOS ANGELES DODGERS": "LAD", "DODGERS": "LAD",
    "MIAMI MARLINS": "MIA", "MARLINS": "MIA",
    "MILWAUKEE BREWERS": "MIL", "BREWERS": "MIL",
    "MINNESOTA TWINS": "MIN", "TWINS": "MIN",
    "NEW YORK METS": "NYM", "METS": "NYM",
    "NEW YORK YANKEES": "NYY", "YANKEES": "NYY",
    "ATHLETICS": "ATH", "OAKLAND ATHLETICS": "ATH", "SACRAMENTO ATHLETICS": "ATH", "OAK": "ATH",
    "PHILADELPHIA PHILLIES": "PHI", "PHILLIES": "PHI",
    "PITTSBURGH PIRATES": "PIT", "PIRATES": "PIT",
    "SAN DIEGO PADRES": "SD", "PADRES": "SD", "SDP": "SD",
    "SAN FRANCISCO GIANTS": "SF", "GIANTS": "SF", "SFG": "SF",
    "SEATTLE MARINERS": "SEA", "MARINERS": "SEA",
    "ST LOUIS CARDINALS": "STL", "ST. LOUIS CARDINALS": "STL", "CARDINALS": "STL",
    "TAMPA BAY RAYS": "TB", "RAYS": "TB", "TBR": "TB",
    "TEXAS RANGERS": "TEX", "RANGERS": "TEX",
    "TORONTO BLUE JAYS": "TOR", "BLUE JAYS": "TOR",
    "WASHINGTON NATIONALS": "WSH", "NATIONALS": "WSH", "WSN": "WSH",
}


def _normalize_team(value: Any) -> str:
    raw = " ".join(str(value or "").replace(".", " ").upper().split())
    return TEAM_ALIASES.get(raw, raw)


def _team_key(game: dict[str, Any]) -> str:
    candidates = (
        game.get("stadium_team"),
        game.get("home_team_abbr"),
        game.get("home_team"),
        game.get("home_team_name"),
    )
    for candidate in candidates:
        key = _normalize_team(candidate)
        if key:
            return key
    return ""


def _seed(game: dict[str, Any]) -> int:
    values = (
        game.get("home_team_id"),
        game.get("venue_id"),
        game.get("stadium_team"),
        game.get("stadium_name"),
        game.get("venue_name"),
        game.get("home_team_name"),
    )
    text = "|".join(str(value or "") for value in values)
    return sum((index + 1) * ord(char) for index, char in enumerate(text))


@lru_cache(maxsize=64)
def _image_uri(path_str: str) -> str:
    return image_data(Path(path_str))


def stadium_scene_data(game: dict[str, Any], *, detail: bool = False) -> str:
    """Return the best local stadium scene for the matchup."""
    team = _team_key(game)

    photo = PHOTO_TEAM_SCENES.get(team)
    if photo:
        return _image_uri(str(photo))

    illustrated = TEAM_SCENES.get(team)
    if illustrated:
        return _image_uri(str(illustrated))

    if not SCENES:
        return ""
    index = _seed(game) % len(SCENES)
    return _image_uri(str(SCENES[index]))
