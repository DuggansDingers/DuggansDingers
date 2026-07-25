from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timezone
import json
from pathlib import Path
from typing import Any

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
SNAPSHOT_DIR = BASE_DIR / "data" / "cache"


def _snapshot_path(target_date: str | None, mode: str) -> Path:
    safe_date = str(target_date or date.today().isoformat()).replace("/", "-")
    return SNAPSHOT_DIR / f"board_{safe_date}_{mode}.json"


def _read_snapshot(target_date: str | None, mode: str, max_age_seconds: int) -> dict[str, Any] | None:
    path = _snapshot_path(target_date, mode)
    try:
        age = datetime.now(timezone.utc).timestamp() - path.stat().st_mtime
        if age > max_age_seconds:
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) and payload.get("rankings") else None
    except (OSError, json.JSONDecodeError):
        return None


def _write_snapshot(target_date: str | None, mode: str, payload: dict[str, Any]) -> None:
    try:
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        _snapshot_path(target_date, mode).write_text(json.dumps(payload), encoding="utf-8")
    except (OSError, TypeError, ValueError):
        pass


@st.cache_data(ttl=7200, show_spinner=False)
def _load_model_base(target_date: str | None = None) -> dict[str, Any]:
    """Load projections, MLB history, Statcast, and probable pitchers."""
    cached = _read_snapshot(target_date, "base", 60 * 60)
    if cached:
        cached["snapshot_status"] = "disk cache"
        return cached
    from model import get_home_run_rankings

    payload = get_home_run_rankings(target_date=target_date)
    _write_snapshot(target_date, "base", payload)
    return payload


@st.cache_data(ttl=1800, show_spinner=False)
def _load_weather_board(target_date: str | None = None) -> dict[str, Any]:
    """Refresh weather independently from the core hitter board."""
    cached = _read_snapshot(target_date, "weather", 20 * 60)
    if cached:
        cached["snapshot_status"] = "weather disk cache"
        return cached
    from services.weather import enrich_board_weather

    payload = enrich_board_weather(deepcopy(_load_model_base(target_date)))
    _write_snapshot(target_date, "weather", payload)
    return payload


@st.cache_data(ttl=600, show_spinner=False)
def _load_odds_board(target_date: str | None = None, include_weather: bool = False) -> dict[str, Any]:
    """Refresh sportsbook prices independently from the slower core model."""
    mode = "odds_weather" if include_weather else "odds"
    cached = _read_snapshot(target_date, mode, 8 * 60)
    if cached:
        cached["snapshot_status"] = "odds disk cache"
        return cached
    from services.odds import enrich_board_odds

    base = _load_weather_board(target_date) if include_weather else deepcopy(_load_model_base(target_date))
    payload = enrich_board_odds(deepcopy(base))
    _write_snapshot(target_date, mode, payload)
    return payload


def load_board(
    target_date: str | None = None,
    *,
    include_weather: bool = False,
    include_odds: bool = False,
) -> dict[str, Any]:
    """Load only the expensive feeds needed by the active page.

    Home, Rankings, Team Sheets, Game Sims, and Player Intelligence can render
    without waiting for weather. Weather is loaded only for Weather and player
    detail views. Odds are loaded only where sportsbook prices are displayed.
    """
    if include_odds:
        return deepcopy(_load_odds_board(target_date, include_weather))
    if include_weather:
        return deepcopy(_load_weather_board(target_date))
    return deepcopy(_load_model_base(target_date))


def _clear_all() -> None:
    _load_odds_board.clear()
    _load_weather_board.clear()
    _load_model_base.clear()


load_board.clear = _clear_all  # type: ignore[attr-defined]


def empty_board(error: Exception | None = None, target_date: str | None = None) -> dict[str, Any]:
    return {
        "date": target_date or date.today().isoformat(),
        "updated_at": "",
        "games": 0,
        "games_meta": [],
        "teams": [],
        "rankings": [],
        "data_sources": {},
        "error": str(error) if error else "",
    }
