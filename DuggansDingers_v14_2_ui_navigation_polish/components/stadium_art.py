from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from components.ui import image_data

BASE_DIR = Path(__file__).resolve().parents[1]
RENDER_DIR = BASE_DIR / "assets" / "stadium_v25"
STADIUMS_FILE = BASE_DIR / "data" / "stadiums.json"

TEAM_ID_TO_ABBR = {
    109:"ARI",144:"ATL",110:"BAL",111:"BOS",112:"CHC",145:"CWS",
    113:"CIN",114:"CLE",115:"COL",116:"DET",117:"HOU",118:"KC",
    108:"LAA",119:"LAD",146:"MIA",158:"MIL",142:"MIN",121:"NYM",
    147:"NYY",133:"ATH",143:"PHI",134:"PIT",135:"SD",137:"SF",
    136:"SEA",138:"STL",139:"TB",140:"TEX",141:"TOR",120:"WSH",
}

TEAM_ALIASES = {
    "ARIZONA DIAMONDBACKS":"ARI","DIAMONDBACKS":"ARI",
    "ATLANTA BRAVES":"ATL","BRAVES":"ATL",
    "BALTIMORE ORIOLES":"BAL","ORIOLES":"BAL",
    "BOSTON RED SOX":"BOS","RED SOX":"BOS",
    "CHICAGO CUBS":"CHC","CUBS":"CHC",
    "CHICAGO WHITE SOX":"CWS","WHITE SOX":"CWS",
    "CINCINNATI REDS":"CIN","REDS":"CIN",
    "CLEVELAND GUARDIANS":"CLE","GUARDIANS":"CLE",
    "COLORADO ROCKIES":"COL","ROCKIES":"COL",
    "DETROIT TIGERS":"DET","TIGERS":"DET",
    "HOUSTON ASTROS":"HOU","ASTROS":"HOU",
    "KANSAS CITY ROYALS":"KC","ROYALS":"KC","KCR":"KC",
    "LOS ANGELES ANGELS":"LAA","ANGELS":"LAA",
    "LOS ANGELES DODGERS":"LAD","DODGERS":"LAD",
    "MIAMI MARLINS":"MIA","MARLINS":"MIA",
    "MILWAUKEE BREWERS":"MIL","BREWERS":"MIL",
    "MINNESOTA TWINS":"MIN","TWINS":"MIN",
    "NEW YORK METS":"NYM","METS":"NYM",
    "NEW YORK YANKEES":"NYY","YANKEES":"NYY",
    "ATHLETICS":"ATH","OAKLAND ATHLETICS":"ATH","SACRAMENTO ATHLETICS":"ATH","OAK":"ATH",
    "PHILADELPHIA PHILLIES":"PHI","PHILLIES":"PHI",
    "PITTSBURGH PIRATES":"PIT","PIRATES":"PIT",
    "SAN DIEGO PADRES":"SD","PADRES":"SD","SDP":"SD",
    "SAN FRANCISCO GIANTS":"SF","GIANTS":"SF","SFG":"SF",
    "SEATTLE MARINERS":"SEA","MARINERS":"SEA",
    "ST LOUIS CARDINALS":"STL","ST. LOUIS CARDINALS":"STL","CARDINALS":"STL",
    "TAMPA BAY RAYS":"TB","RAYS":"TB","TBR":"TB",
    "TEXAS RANGERS":"TEX","RANGERS":"TEX",
    "TORONTO BLUE JAYS":"TOR","BLUE JAYS":"TOR",
    "WASHINGTON NATIONALS":"WSH","NATIONALS":"WSH","WSN":"WSH",
}

RENDERS = {path.stem.upper(): path for path in RENDER_DIR.glob("*.jpg")}

@lru_cache(maxsize=1)
def _venue_index() -> dict[str, str]:
    try:
        data = json.loads(STADIUMS_FILE.read_text(encoding="utf-8-sig"))
    except Exception:
        data = {}
    index: dict[str, str] = {}
    if isinstance(data, dict):
        for abbr, stadium in data.items():
            names = [stadium.get("name"), *(stadium.get("aliases") or [])]
            for name in names:
                key = " ".join(str(name or "").upper().replace(".", " ").split())
                if key:
                    index[key] = abbr.upper()
    return index


def _normalize(value: Any) -> str:
    raw = " ".join(str(value or "").upper().replace(".", " ").split())
    return TEAM_ALIASES.get(raw, raw)


def _team_key(game: dict[str, Any]) -> str:
    for key_name in ("home_team_id", "team_id"):
        try:
            team = TEAM_ID_TO_ABBR.get(int(game.get(key_name)))
        except Exception:
            team = None
        if team in RENDERS:
            return team

    venue = " ".join(str(game.get("stadium_name") or game.get("venue_name") or "").upper().replace(".", " ").split())
    team = _venue_index().get(venue)
    if team in RENDERS:
        return team

    for value in (
        game.get("stadium_team"),
        game.get("home_team_abbr"),
        game.get("home_team"),
        game.get("home_team_name"),
    ):
        team = _normalize(value)
        if team in RENDERS:
            return team
    return ""


@lru_cache(maxsize=64)
def _uri(path: str) -> str:
    return image_data(Path(path))


def stadium_scene_data(game: dict[str, Any], *, detail: bool = False) -> str:
    team = _team_key(game)
    path = RENDERS.get(team)
    return _uri(str(path)) if path else ""
