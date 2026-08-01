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
from components.shell import render_app_header
from data_service import empty_board, load_board, snapshot_available
from views import dashboard, player_profile, rankings, secondary, team_cheatsheets, weather_command, extras, matchup_center, prop_center

apply_theme()
init_state()

page = page_from_query()
stored_date = st.session_state.get("slate_date", date.today())
target_date = stored_date.isoformat() if hasattr(stored_date, "isoformat") else str(stored_date)

page, chosen_date = render_navigation(
    target_date,
    int(st.session_state.get("last_game_count", 0)),
    int(st.session_state.get("last_hitter_count", 0)),
    str(st.session_state.get("last_updated_at", "")),
)
if chosen_date != target_date:
    st.rerun()

include_weather = page in {
    "Home","Daily Board","Team Sheets","Weather","Game Sims","Parlay Lab",
    "Player Intelligence","News & Alerts","Matchups","Park Factors","Props"
}
include_odds = page in {
    "Home","Daily Board","Team Sheets","Sportsbook","Parlay Lab",
    "Player Intelligence","Game Sims","News & Alerts","Props"
}

force_live_refresh = bool(st.session_state.pop("_force_live_refresh", False))
prepared = snapshot_available(target_date) and not force_live_refresh

spinner_text = (
    "Opening today's prepared intelligence board..."
    if prepared
    else {
        "Weather": "Connecting ballpark weather and wind intelligence...",
        "Sportsbook": "Matching DraftKings and FanDuel prices...",
        "Game Sims": "Loading the simulation board...",
    }.get(page, "Refreshing today's home run intelligence...")
)

st.markdown(
    f'<div class="dd-loading-banner"><i></i><span>{spinner_text}</span></div>',
    unsafe_allow_html=True,
)
with st.spinner(spinner_text):
    try:
        board = load_board(
            target_date,
            include_weather=include_weather,
            include_odds=include_odds,
            prefer_prebuilt=not force_live_refresh,
        )
    except Exception as exc:
        board = empty_board(exc, target_date)

st.session_state.last_game_count = int(board.get("games", 0))
st.session_state.last_hitter_count = len(board.get("rankings", []))
st.session_state.last_updated_at = str(board.get("updated_at", ""))
st.session_state.last_fast_start = bool(board.get("fast_start"))

# Counts displayed in the prototype-style sidebar badges.
st.session_state.last_odds_count = int((board.get("odds_summary") or {}).get("live_records", 0) or 0)
try:
    from views.extras import _alerts
    st.session_state.last_alert_count = len(_alerts(board))
except Exception:
    st.session_state.last_alert_count = 0

st.markdown(
    '<style>.dd-loading-banner{display:none!important}</style>',
    unsafe_allow_html=True,
)

if board.get("error"):
    st.error(f"Data could not be refreshed: {board['error']}")

render_app_header(board, page)

if not board.get("fast_start") and board.get("rankings"):
    st.markdown(
        '<div class="dd26-live-ribbon"><i></i><b>LIVE FALLBACK</b><span>A prepared snapshot is not available for this slate. The app is using current live data while the scheduled snapshot catches up.</span></div>',
        unsafe_allow_html=True,
    )

routes = {
    "Home": dashboard.render,
    "Daily Board": rankings.render,
    "Team Sheets": team_cheatsheets.render,
    "Weather": weather_command.render,
    "Sportsbook": secondary.sportsbook_odds,
    "Game Sims": secondary.game_sims,
    "Parlay Lab": secondary.parlay,
    "Player Intelligence": player_profile.render,
    "Matchups": matchup_center.render,
    "Props": prop_center.render,
    "Park Factors": secondary.parks,
    "Trends": secondary.trends,
    "News & Alerts": extras.news_alerts,
    "Settings": extras.settings,
}
routes.get(page, dashboard.render)(board)
