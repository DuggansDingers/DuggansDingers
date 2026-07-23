from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from components.ui import logo_data


NAVIGATION = [
    "Home",
    "Daily Board",
    "Team Sheets",
    "Weather",
    "Sportsbook",
    "Model Lab",
]


def init_state() -> None:
    st.session_state.setdefault("page", "Home")
    st.session_state.setdefault("nav_choice", st.session_state.page)
    st.session_state.setdefault("selected_player_id", None)
    st.session_state.setdefault("favorites", [])
    st.session_state.setdefault("slate_date", date.today())
    st.session_state.setdefault("generated_parlay", [])


def go(page: str, player_id: int | None = None) -> None:
    aliases = {
        "Dashboard": "Home",
        "Rankings": "Daily Board",
        "Team Cheat Sheets": "Team Sheets",
        "Player Profile": "Player Intelligence",
        "Player Profiles": "Player Intelligence",
        "Sportsbook Odds": "Sportsbook",
        "Parlay Lab": "Model Lab",
    }
    target = aliases.get(page, page)
    st.session_state.page = target
    if target in NAVIGATION:
        st.session_state.nav_choice = target
    else:
        st.session_state.pending_page = target
    if player_id is not None:
        st.session_state.selected_player_id = player_id


def render_top_navigation(as_of: str, games: int, hitters: int, updated_at: str = "") -> tuple[str, str]:
    init_state()
    try:
        current_date = datetime.strptime(as_of, "%Y-%m-%d").date() if as_of else st.session_state.slate_date
    except ValueError:
        current_date = st.session_state.slate_date

    if st.session_state.page in NAVIGATION and st.session_state.get("nav_choice") != st.session_state.page:
        st.session_state.nav_choice = st.session_state.page

    logo = logo_data()
    left, middle, right = st.columns([2.35, 7.4, 2.25], gap="small", vertical_alignment="center")

    with left:
        st.markdown(
            f'<div class="dd-logo-shell"><img src="{logo}" alt="Duggan\'s Dingers"></div>',
            unsafe_allow_html=True,
        )

    with middle:
        selected = st.radio(
            "Primary navigation",
            NAVIGATION,
            horizontal=True,
            label_visibility="collapsed",
            key="nav_choice",
        )
        pending = st.session_state.pop("pending_page", None)
        st.session_state.page = pending or selected

    with right:
        chosen_date = st.date_input(
            "Slate date",
            value=current_date,
            key="top_slate_date",
            label_visibility="collapsed",
            help="Choose the MLB slate date.",
        )

    st.session_state.slate_date = chosen_date
    return st.session_state.page, chosen_date.isoformat()
