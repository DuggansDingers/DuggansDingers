from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from components.ui import image_data

BASE_DIR = Path(__file__).resolve().parents[1]
RENDER_DIR = BASE_DIR / "assets" / "stadium_renders"
SCENE_DIR = BASE_DIR / "assets" / "stadium_scenes"
PHOTO_SCENE_DIR = BASE_DIR / "assets" / "stadium_photo_scenes"
STADIUMS_FILE = BASE_DIR / "data" / "stadiums.json"

TEAM_SCENES = {path.stem.upper(): path for path in SCENE_DIR.glob("*.jpg") if not path.stem.startswith("scene_")}
RENDER_SCENES = {path.stem.upper(): path for path in RENDER_DIR.glob("*.jpg")}
PHOTO_TEAM_SCENES = {path.stem.upper(): path for path in PHOTO_SCENE_DIR.glob("*.jpg")}

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

TEAM_ID_TO_ABBR = {
    109: "ARI", 144: "ATL", 110: "BAL", 111: "BOS", 112: "CHC", 145: "CWS",
    113: "CIN", 114: "CLE", 115: "COL", 116: "DET", 117: "HOU", 118: "KC",
    108: "LAA", 119: "LAD", 146: "MIA", 158: "MIL", 142: "MIN", 121: "NYM",
    147: "NYY", 133: "ATH", 143: "PHI", 134: "PIT", 135: "SD", 137: "SF",
    136: "SEA", 138: "STL", 139: "TB", 140: "TEX", 141: "TOR", 120: "WSH",
}

@lru_cache(maxsize=1)
def _stadium_name_index() -> dict[str, str]:
    try:
        payload = json.loads(STADIUMS_FILE.read_text(encoding="utf-8-sig"))
    except Exception:
        payload = {}
    index: dict[str, str] = {}
    if isinstance(payload, dict):
        for abbr, meta in payload.items():
            names = [meta.get("name"), *(meta.get("aliases") or [])]
            for name in names:
                cleaned = " ".join(str(name or "").upper().replace(".", " ").split())
                if cleaned:
                    index[cleaned] = abbr.upper()
    return index


def _normalize(value: Any) -> str:
    raw = " ".join(str(value or "").upper().replace(".", " ").replace("-", " ").split())
    return TEAM_ALIASES.get(raw, raw)


def _abbr_from_team_id(value: Any) -> str:
    try:
        return TEAM_ID_TO_ABBR.get(int(value), "")
    except Exception:
        return ""


def _abbr_from_venue(value: Any) -> str:
    key = " ".join(str(value or "").upper().replace(".", " ").split())
    return _stadium_name_index().get(key, "")


def _team_key(game: dict[str, Any]) -> str:
    candidates = (
        _abbr_from_team_id(game.get("home_team_id")),
        _abbr_from_team_id(game.get("team_id")),
        _abbr_from_venue(game.get("stadium_name") or game.get("venue_name")),
        game.get("stadium_team"),
        game.get("home_team_abbr"),
        game.get("home_team"),
        game.get("home_team_name"),
    )
    for candidate in candidates:
        key = _normalize(candidate)
        if key and key in set(RENDER_SCENES) | set(TEAM_SCENES) | set(PHOTO_TEAM_SCENES):
            return key
    return ""


@lru_cache(maxsize=256)
def _image_uri(path_str: str) -> str:
    return image_data(Path(path_str))


def stadium_scene_data(game: dict[str, Any], *, detail: bool = False) -> str:
    """Return a stable venue-specific local render.

    Preference order:
    1) assets/stadium_renders/<TEAM>.jpg   (drop-in AI stadium renders)
    2) assets/stadium_scenes/<TEAM>.jpg    (bundled stylized fallback)
    3) assets/stadium_photo_scenes/<TEAM>.jpg

    Unlike earlier versions, this never rotates through random generic scenes.
    """
    team = _team_key(game)
    for collection in (RENDER_SCENES, TEAM_SCENES, PHOTO_TEAM_SCENES):
        path = collection.get(team)
        if path and path.exists():
            return _image_uri(str(path))
    return ""
