from __future__ import annotations

from datetime import date

import streamlit as st

st.set_page_config(
    page_title="DuggansDingers",
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

with st.spinner("Loading the Dinger Board, weather, Statcast, and sportsbook odds..."):
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
    "Dashboard": dashboard.render,
    "Rankings": rankings.render,
    "Weather": secondary.weather_center,
    "Team Sheets": team_cheatsheets.render,
    "Player Profiles": player_profile.render,
    "Trends": secondary.trends,
    "Matchups": secondary.matchups,
    "Park Factors": secondary.parks,
    "Sportsbook Odds": secondary.sportsbook_odds,
    "Parlay Lab": secondary.parlay,
}
routes.get(page, dashboard.render)(board)
