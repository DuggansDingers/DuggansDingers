from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from config import NAV_ITEMS
from components.ui import logo_data


def init_state() -> None:
    st.session_state.setdefault("page", "Dashboard")
    st.session_state.setdefault("selected_player_id", None)
    st.session_state.setdefault("favorites", [])
    st.session_state.setdefault("slate_date", date.today())
    st.session_state.setdefault("generated_parlay", [])


def go(page: str, player_id: int | None = None) -> None:
    st.session_state.page = page
    if player_id is not None:
        st.session_state.selected_player_id = player_id


def render_sidebar(as_of: str, games: int, hitters: int, updated_at: str = "") -> tuple[str, str]:
    init_state()
    try:
        current_date = datetime.strptime(as_of, "%Y-%m-%d").date() if as_of else st.session_state.slate_date
    except ValueError:
        current_date = st.session_state.slate_date

    with st.sidebar:
        logo = logo_data()
        if logo:
            st.markdown(f'<img class="dd-sidebar-logo" src="{logo}">', unsafe_allow_html=True)

        st.markdown('<div class="dd-nav-kicker">DUGGANS DINGERS</div><div class="dd-nav-title">Command Center</div><div class="dd-nav-sub">MLB home run intelligence</div>', unsafe_allow_html=True)

        chosen_date = st.date_input(
            "Slate date",
            value=current_date,
            key="sidebar_slate_date",
            help="Load any available Ballpark Pal slate by date.",
        )
        chosen_date_string = chosen_date.isoformat()
        st.session_state.slate_date = chosen_date

        st.markdown('<div class="dd-nav-section">Navigation</div>', unsafe_allow_html=True)
        for label, icon in NAV_ITEMS:
            kind = "primary" if st.session_state.page == label else "secondary"
            if st.button(f"{icon}   {label}", key=f"nav_{label}", use_container_width=True, type=kind):
                go(label)
                st.rerun()

        updated = "Live board"
        if updated_at:
            try:
                updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00")).strftime("%I:%M %p UTC")
            except ValueError:
                updated = "Live board"
        st.markdown(
            f'''
<div class="dd-side-meta">
  <div class="dd-side-meta-label">Slate Date</div><div class="dd-side-meta-value">{chosen_date.strftime('%b %d, %Y')}</div>
  <div class="dd-side-rule"></div>
  <div class="dd-side-meta-label">Data Last Updated</div><div class="dd-side-meta-value">{updated}</div>
  <div class="dd-live-line"><span class="dd-live-dot"></span>Live model board</div>
  <div class="dd-side-counts">{games} games • {hitters} hitters</div>
</div>''',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="dd-nav-section dd-nav-section-bottom">Data controls</div>', unsafe_allow_html=True)
        if st.button("↻ Refresh all data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    return st.session_state.page, chosen_date_string
