from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any

import streamlit as st


@st.cache_data(ttl=7200, show_spinner=False)
def _load_model_base(target_date: str | None = None) -> dict[str, Any]:
    """Load projections and MLB/Statcast data on a two-hour cache."""
    from model import get_home_run_rankings

    return get_home_run_rankings(target_date=target_date)


@st.cache_data(ttl=1800, show_spinner=False)
def _load_weather_board(target_date: str | None = None) -> dict[str, Any]:
    """Refresh weather every 30 minutes without rebuilding the full model."""
    from services.weather import enrich_board_weather

    board = deepcopy(_load_model_base(target_date))
    return enrich_board_weather(board)


def load_board(target_date: str | None = None) -> dict[str, Any]:
    """Build the board from independently cached model, weather, and odds data."""
    from services.odds import enrich_board_odds

    board = deepcopy(_load_weather_board(target_date))
    return enrich_board_odds(board)


def _clear_all() -> None:
    _load_weather_board.clear()
    _load_model_base.clear()


# Preserve compatibility with existing refresh controls.
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
