from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from components.ui import image_data

BASE_DIR = Path(__file__).resolve().parents[1]
SCENE_DIR = BASE_DIR / "assets" / "stadium_scenes"
SCENES = tuple(sorted(SCENE_DIR.glob("scene_*.jpg")))
TEAM_SCENES = {path.stem.upper(): path for path in SCENE_DIR.glob("*.jpg") if not path.stem.startswith("scene_")}


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


@lru_cache(maxsize=16)
def _scene_uri(index: int) -> str:
    if not SCENES:
        return ""
    return image_data(SCENES[index % len(SCENES)])


def stadium_scene_data(game: dict[str, Any], *, detail: bool = False) -> str:
    """Return a cinematic AI-illustrated stadium scene, never aerial imagery."""
    team = str(
        game.get("stadium_team")
        or game.get("home_team_name")
        or ""
    ).upper().replace(".", "").strip()
    aliases = {"OAK": "ATH", "KCR": "KC", "SDP": "SD", "SFG": "SF", "TBR": "TB", "WSN": "WSH"}
    team = aliases.get(team, team)
    team_path = TEAM_SCENES.get(team)
    if team_path and not detail:
        return image_data(team_path)
    if not SCENES:
        return ""
    index = 6 if detail and len(SCENES) >= 7 else _seed(game) % len(SCENES)
    return _scene_uri(index)
