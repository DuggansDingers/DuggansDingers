from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any

import streamlit as st


@st.cache_data(ttl=7200, show_spinner=False)
def _load_board_base(target_date: str | None = None) -> dict[str, Any]:
    """Load the slower model/weather data on a two-hour cache."""
    from model import get_home_run_rankings
    from services.weather import enrich_board_weather

    board = get_home_run_rankings(target_date=target_date)
    return enrich_board_weather(board)


def load_board(target_date: str | None = None) -> dict[str, Any]:
    """Build the page board and attach sportsbook odds automatically.

    The base model remains cached for two hours. Sportsbook odds are checked on
    every page load, while services.odds keeps its own one-hour successful cache
    and retries empty/error results after five minutes. No button press is needed.
    """
    from services.odds import enrich_board_odds

    board = deepcopy(_load_board_base(target_date))
    return enrich_board_odds(board)


# Preserve compatibility with the existing manual refresh button.
load_board.clear = _load_board_base.clear  # type: ignore[attr-defined]


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
