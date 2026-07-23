from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from components.ui import logo_data


NAVIGATION = [
    "Dashboard",
    "Rankings",
    "Weather",
    "Team Sheets",
    "Player Profiles",
    "Matchups",
    "Park Factors",
    "Sportsbook Odds",
    "Parlay Lab",
]


def init_state() -> None:
    st.session_state.setdefault("page", "Dashboard")
    st.session_state.setdefault("selected_player_id", None)
    st.session_state.setdefault("favorites", [])
    st.session_state.setdefault("slate_date", date.today())
    st.session_state.setdefault("generated_parlay", [])


def go(page: str, player_id: int | None = None) -> None:
    aliases = {
        "Team Cheat Sheets": "Team Sheets",
        "Player Profile": "Player Profiles",
    }
    st.session_state.page = aliases.get(page, page)
    if player_id is not None:
        st.session_state.selected_player_id = player_id


def render_top_navigation(as_of: str, games: int, hitters: int, updated_at: str = "") -> tuple[str, str]:
    init_state()
    try:
        current_date = datetime.strptime(as_of, "%Y-%m-%d").date() if as_of else st.session_state.slate_date
    except ValueError:
        current_date = st.session_state.slate_date

    logo = logo_data()
    logo_html = f'<img class="dd-header-logo" src="{logo}">' if logo else '<div class="dd-ballmark">⚾</div>'
    st.markdown(
        f"""
<div class="dd-brand-header">
  <div class="dd-brand-left">{logo_html}</div>
  <div class="dd-brand-center">
    <div class="dd-brand-title">DUGGANS<span>DINGERS</span></div>
    <div class="dd-brand-rule"><i></i><b>HOME RUN INTELLIGENCE</b><i></i></div>
  </div>
  <div class="dd-live-pill"><span></span>{games} GAMES • {hitters} HITTERS</div>
</div>
""",
        unsafe_allow_html=True,
    )

    left, right = st.columns([5.7, 1.3], vertical_alignment="center")
    with left:
        page = st.radio(
            "Primary navigation",
            NAVIGATION,
            index=NAVIGATION.index(st.session_state.page) if st.session_state.page in NAVIGATION else 0,
            horizontal=True,
            label_visibility="collapsed",
            key="top_navigation",
        )
        if page != st.session_state.page:
            st.session_state.page = page
    with right:
        chosen_date = st.date_input(
            "Slate date",
            value=current_date,
            key="top_slate_date",
            label_visibility="collapsed",
            help="Choose the MLB slate date.",
        )
    st.session_state.slate_date = chosen_date

    c1, c2 = st.columns([5.8, 1.2])
    with c1:
        st.markdown(
            f'<div class="dd-status-line"><span class="dd-status-dot"></span> LIVE MODEL BOARD <b>{games} games</b><b>{hitters} ranked hitters</b></div>',
            unsafe_allow_html=True,
        )
    with c2:
        if st.button("↻ Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    return st.session_state.page, chosen_date.isoformat()
