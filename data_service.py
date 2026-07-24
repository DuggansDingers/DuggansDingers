from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any

import streamlit as st


@st.cache_data(ttl=7200, show_spinner=False)
def _load_model_base(target_date: str | None = None) -> dict[str, Any]:
    """Load projections, MLB history, Statcast, and probable pitchers."""
    from model import get_home_run_rankings

    return get_home_run_rankings(target_date=target_date)


@st.cache_data(ttl=1800, show_spinner=False)
def _load_weather_board(target_date: str | None = None) -> dict[str, Any]:
    """Refresh weather independently from the core hitter board."""
    from services.weather import enrich_board_weather

    return enrich_board_weather(deepcopy(_load_model_base(target_date)))


@st.cache_data(ttl=600, show_spinner=False)
def _load_odds_board(target_date: str | None = None, include_weather: bool = False) -> dict[str, Any]:
    """Refresh sportsbook prices independently from the slower core model."""
    from services.odds import enrich_board_odds

    base = _load_weather_board(target_date) if include_weather else deepcopy(_load_model_base(target_date))
    return enrich_board_odds(deepcopy(base))


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
