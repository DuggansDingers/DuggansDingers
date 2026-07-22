from __future__ import annotations

from datetime import date

import streamlit as st

from auth import render_logout, require_login

st.set_page_config(
    page_title="DuggansDingers",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded",
)

require_login()

from components.navigation import init_state, render_sidebar
from components.theme import apply_theme
from data_service import empty_board, load_board
from pages import dashboard, player_profile, rankings, secondary, team_cheatsheets

apply_theme()
init_state()

widget_date = st.session_state.get("sidebar_slate_date")
if hasattr(widget_date, "isoformat"):
    target_date = widget_date.isoformat()
else:
    stored_date = st.session_state.get("slate_date", date.today())
    target_date = stored_date.isoformat() if hasattr(stored_date, "isoformat") else str(stored_date)

with st.spinner("Loading the Dinger Board, weather, and live sportsbook odds..."):
    try:
        board = load_board(target_date)
    except Exception as exc:
        board = empty_board(exc, target_date)

page, chosen_date = render_sidebar(
    str(board.get("date", target_date)),
    int(board.get("games", 0)),
    len(board.get("rankings", [])),
    str(board.get("updated_at", "")),
)

render_logout()

# The date widget updates before the next Streamlit run. If its value changed during
# this run, rerun immediately so every page uses the newly selected slate.
if chosen_date != target_date:
    st.rerun()

if board.get("error"):
    st.error(f"Data could not be refreshed: {board['error']}")

routes = {
    "Dashboard": dashboard.render,
    "Rankings": rankings.render,
    "Team Cheat Sheets": team_cheatsheets.render,
    "Player Profile": player_profile.render,
    "Trends": secondary.trends,
    "Matchups": secondary.matchups,
    "Park Factors": secondary.parks,
    "Sportsbook Odds": secondary.sportsbook_odds,
    "Parlay Lab": secondary.parlay,
}
routes.get(page, dashboard.render)(board)
