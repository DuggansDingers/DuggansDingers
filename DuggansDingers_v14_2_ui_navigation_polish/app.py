from __future__ import annotations

from datetime import date

import streamlit as st

st.set_page_config(
    page_title="Duggan's Dingers",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded",
)

from components.navigation import init_state, page_from_query, render_navigation
from components.theme import apply_theme
from data_service import empty_board, load_board
from views import dashboard, player_profile, rankings, secondary, team_cheatsheets

apply_theme()
init_state()

page = page_from_query()
stored_date = st.session_state.get("slate_date", date.today())
target_date = stored_date.isoformat() if hasattr(stored_date, "isoformat") else str(stored_date)

# Render the navigation immediately so a cold data refresh never leaves the
# visitor staring at an empty screen. The last known counts update on reruns.
page, chosen_date = render_navigation(
    target_date,
    int(st.session_state.get("last_game_count", 0)),
    int(st.session_state.get("last_hitter_count", 0)),
    str(st.session_state.get("last_updated_at", "")),
)
if chosen_date != target_date:
    st.rerun()

include_weather = page in {"Home", "Daily Board", "Team Sheets", "Weather", "Game Sims", "Parlay Lab", "Player Intelligence"}
include_odds = page in {"Home", "Daily Board", "Team Sheets", "Sportsbook", "Parlay Lab", "Player Intelligence", "Game Sims"}
spinner_text = {
    "Weather": "Connecting ballpark weather and wind intelligence...",
    "Sportsbook": "Matching DraftKings and FanDuel prices...",
    "Game Sims": "Loading the simulation board...",
}.get(page, "Loading today's home run intelligence...")

st.markdown(f'<div class="dd-loading-banner"><i></i><span>{spinner_text}</span></div>', unsafe_allow_html=True)
with st.spinner(spinner_text):
    try:
        board = load_board(target_date, include_weather=include_weather, include_odds=include_odds)
    except Exception as exc:
        board = empty_board(exc, target_date)

st.session_state.last_game_count = int(board.get("games", 0))
st.session_state.last_hitter_count = len(board.get("rankings", []))
st.session_state.last_updated_at = str(board.get("updated_at", ""))

# Remove the custom loading strip after the board is available.
st.markdown('<style>.dd-loading-banner{display:none!important}</style>', unsafe_allow_html=True)

if board.get("error"):
    st.error(f"Data could not be refreshed: {board['error']}")

routes = {
    "Home": dashboard.render,
    "Daily Board": rankings.render,
    "Team Sheets": team_cheatsheets.render,
    "Weather": secondary.weather_center,
    "Sportsbook": secondary.sportsbook_odds,
    "Game Sims": secondary.game_sims,
    "Parlay Lab": secondary.parlay,
    "Player Intelligence": player_profile.render,
    "Matchups": secondary.matchups,
    "Park Factors": secondary.parks,
    "Trends": secondary.trends,
}
routes.get(page, dashboard.render)(board)
