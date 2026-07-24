from __future__ import annotations

from datetime import date, datetime
from html import escape
from typing import Any

import streamlit as st

from components.ui import logo_data

NAV_ITEMS = [
    ("Home", "home", "Dashboard", "home"),
    ("Daily Board", "daily-board", "Player Rankings", "rank"),
    ("Player Intelligence", "player-intelligence", "Player Profiles", "user"),
    ("Team Sheets", "team-sheets", "Team Sheets", "sheet"),
    ("Weather", "weather", "Ballpark Weather", "weather"),
    ("Game Sims", "game-sims", "Game Sims", "cube"),
    ("Sportsbook", "sportsbook", "Sportsbook Odds", "money"),
    ("Parlay Lab", "parlay-lab", "Parlay Lab", "lab"),
]

ICONS = {
    "home": '<svg viewBox="0 0 24 24"><path d="M3 11.2 12 3l9 8.2"/><path d="M5.5 10.2V21h13V10.2"/><path d="M9.2 21v-6.4h5.6V21"/></svg>',
    "rank": '<svg viewBox="0 0 24 24"><path d="M5 4h14v16H5z"/><path d="M8 8h8M8 12h8M8 16h5"/><path d="M2.5 8h1M2.5 12h1M2.5 16h1"/></svg>',
    "user": '<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4.5 21a7.5 7.5 0 0 1 15 0"/></svg>',
    "sheet": '<svg viewBox="0 0 24 24"><path d="M4 5.5h7.2A2.8 2.8 0 0 1 14 8.3V20H6a2 2 0 0 1-2-2Z"/><path d="M20 5.5h-3.2A2.8 2.8 0 0 0 14 8.3V20h4a2 2 0 0 0 2-2Z"/></svg>',
    "weather": '<svg viewBox="0 0 24 24"><path d="M12 2v2M4.9 4.9l1.4 1.4M2 12h2M20 12h2M17.7 6.3l1.4-1.4"/><circle cx="12" cy="12" r="4"/><path d="M5.8 20h11.5a3.2 3.2 0 0 0 .1-6.4A5.7 5.7 0 0 0 6.8 15 2.6 2.6 0 0 0 5.8 20Z"/></svg>',
    "cube": '<svg viewBox="0 0 24 24"><path d="M4 17V9l8-5 8 5v8l-8 5Z"/><path d="m4 9 8 5 8-5M12 14v8"/></svg>',
    "money": '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5"/><path d="M15 8.2c-.7-.7-1.6-1-2.9-1-1.8 0-3 .8-3 2.1s1 1.8 3 2.2c2 .4 3 1.1 3 2.4s-1.2 2.2-3.1 2.2c-1.5 0-2.6-.4-3.4-1.3M12 5.3v13.4"/></svg>',
    "lab": '<svg viewBox="0 0 24 24"><path d="M7 3h10M9 3v5l-4.6 8a3 3 0 0 0 2.6 4.5h10a3 3 0 0 0 2.6-4.5L15 8V3"/><path d="M7.2 15h9.6"/></svg>',
}

PAGE_TO_SLUG = {page: slug for page, slug, _, _ in NAV_ITEMS}
SLUG_TO_PAGE = {slug: page for page, slug, _, _ in NAV_ITEMS}
SLUG_TO_PAGE.update({"matchups": "Matchups", "park-factors": "Park Factors", "trends": "Trends"})
ALIASES = {
    "Dashboard": "Home",
    "Rankings": "Daily Board",
    "Team Cheat Sheets": "Team Sheets",
    "Player Profile": "Player Intelligence",
    "Player Profiles": "Player Intelligence",
    "Sportsbook Odds": "Sportsbook",
    "Model Lab": "Parlay Lab",
}


def init_state() -> None:
    st.session_state.setdefault("page", "Home")
    st.session_state.setdefault("selected_player_id", None)
    st.session_state.setdefault("favorites", [])
    st.session_state.setdefault("slate_date", date.today())
    st.session_state.setdefault("generated_parlay", [])


def _query_value(value: Any) -> str:
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value or "")


def page_from_query() -> str:
    init_state()
    slug = _query_value(st.query_params.get("view"))
    if slug in SLUG_TO_PAGE:
        st.session_state.page = SLUG_TO_PAGE[slug]
    player = _query_value(st.query_params.get("player"))
    if player.isdigit():
        st.session_state.selected_player_id = int(player)
    return str(st.session_state.page)


def _slug_for_page(page: str) -> str:
    return PAGE_TO_SLUG.get(ALIASES.get(page, page), "home")


def go(page: str, player_id: int | None = None) -> None:
    page = ALIASES.get(page, page)
    st.session_state.page = page
    st.query_params["view"] = _slug_for_page(page)
    if player_id is not None:
        st.session_state.selected_player_id = int(player_id)
        st.query_params["player"] = str(int(player_id))
    else:
        try:
            del st.query_params["player"]
        except KeyError:
            pass


def render_navigation(as_of: str, games: int, hitters: int, updated_at: str = "") -> tuple[str, str]:
    current_page = page_from_query()
    try:
        current_date = datetime.strptime(as_of, "%Y-%m-%d").date() if as_of else st.session_state.slate_date
    except ValueError:
        current_date = st.session_state.slate_date

    logo = logo_data()
    with st.sidebar:
        st.markdown(
            f'<a class="dd19-side-logo" href="?view=home" target="_self"><img src="{logo}" alt="DuggansDingers"></a>',
            unsafe_allow_html=True,
        )
        links: list[str] = []
        for page, slug, label, icon_name in NAV_ITEMS:
            active = " active" if page == current_page else ""
            links.append(
                f'<a class="dd19-side-link{active}" href="?view={escape(slug)}" target="_self">'
                f'<span class="dd19-side-icon">{ICONS[icon_name]}</span><b>{escape(label)}</b></a>'
            )
        st.markdown('<nav class="dd19-side-nav">' + "".join(links) + "</nav>", unsafe_allow_html=True)
        st.markdown('<div class="dd19-side-spacer"></div>', unsafe_allow_html=True)
        chosen_date = st.date_input("Slate date", value=current_date, key="sidebar_slate_date")
        updated = str(updated_at or "")
        if updated:
            try:
                updated = datetime.fromisoformat(updated.replace("Z", "+00:00")).strftime("%I:%M %p ET")
            except ValueError:
                pass
        st.markdown(
            f'<div class="dd19-side-status"><span>DATA LAST UPDATED</span><b>{escape(updated or "LIVE")}</b><i><em></em> Live</i></div>',
            unsafe_allow_html=True,
        )
    st.session_state.slate_date = chosen_date
    return current_page, chosen_date.isoformat()


render_top_navigation = render_navigation
