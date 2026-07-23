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


def render_top_navigation(as_of: str, games: int, hitters: int, updated_at: str = "") -> tuple[str, str]:
    init_state()
    try:
        current_date = datetime.strptime(as_of, "%Y-%m-%d").date() if as_of else st.session_state.slate_date
    except ValueError:
        current_date = st.session_state.slate_date

    logo = logo_data()
    logo_html = f'<img class="dd-top-logo" src="{logo}">' if logo else '<div class="dd-logo-text">DUGGAN\'S <span>DINGERS</span></div>'
    st.markdown(
        f'<div class="dd-app-header">{logo_html}<div class="dd-header-status"><span class="dd-live-dot"></span>{games} games &bull; {hitters} hitters</div></div>',
        unsafe_allow_html=True,
    )

    nav_labels = [label for label, _ in NAV_ITEMS]
    icon_map = {label: icon for label, icon in NAV_ITEMS}
    current = st.session_state.page if st.session_state.page in nav_labels else "Dashboard"
    selected = st.segmented_control(
        "Navigation",
        nav_labels,
        default=current,
        format_func=lambda label: f"{icon_map.get(label, '')} {label}",
        label_visibility="collapsed",
        key="dd_top_nav",
    )
    if selected and selected != st.session_state.page:
        st.session_state.page = selected
        st.rerun()

    control_cols = st.columns([1.4, 1, 1, 5])
    chosen_date = control_cols[0].date_input("Slate date", value=current_date, key="sidebar_slate_date", label_visibility="collapsed")
    st.session_state.slate_date = chosen_date
    if control_cols[1].button("↻ Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    updated = "Live"
    if updated_at:
        try:
            updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00")).strftime("%I:%M %p")
        except ValueError:
            pass
    control_cols[2].markdown(f'<div class="dd-updated">Updated<br><b>{updated}</b></div>', unsafe_allow_html=True)
    return st.session_state.page, chosen_date.isoformat()
