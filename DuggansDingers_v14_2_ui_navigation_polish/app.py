from __future__ import annotations

from datetime import date

import streamlit as st

st.set_page_config(
    page_title="Duggan's Dingers",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from components.navigation import init_state, render_top_navigation
from components.theme import apply_theme
from data_service import empty_board, load_board
from pages import dashboard, player_profile, rankings, secondary, team_cheatsheets

apply_theme()
init_state()

stored_date = st.session_state.get("slate_date", date.today())
target_date = stored_date.isoformat() if hasattr(stored_date, "isoformat") else str(stored_date)

with st.spinner("Loading today's home run intelligence..."):
    try:
        board = load_board(target_date)
    except Exception as exc:
        board = empty_board(exc, target_date)

page, chosen_date = render_top_navigation(
    str(board.get("date", target_date)),
    int(board.get("games", 0)),
    len(board.get("rankings", [])),
    str(board.get("updated_at", "")),
)

if chosen_date != target_date:
    st.rerun()

if board.get("error"):
    st.error(f"Data could not be refreshed: {board['error']}")

routes = {
    "Home": dashboard.render,
    "Daily Board": rankings.render,
    "Team Sheets": team_cheatsheets.render,
    "Weather": secondary.weather_center,
    "Sportsbook": secondary.sportsbook_odds,
    "Parlay Lab": secondary.parlay,
    "Player Intelligence": player_profile.render,
    "Matchups": secondary.matchups,
    "Park Factors": secondary.parks,
    "Trends": secondary.trends,
}
routes.get(page, dashboard.render)(board)
