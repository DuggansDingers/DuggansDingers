from __future__ import annotations

from datetime import date, datetime
from html import escape
from typing import Any

import streamlit as st

from components.ui import logo_data


NAV_ITEMS = [
    {
        "page": "Home",
        "slug": "home",
        "icon": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 11.2 12 3l9 8.2"/><path d="M5.5 10.2V21h13V10.2"/><path d="M9.2 21v-6.4h5.6V21"/></svg>""",
    },
    {
        "page": "Daily Board",
        "slug": "daily-board",
        "icon": """<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h3M14 12h2M8 16h3M14 16h2"/></svg>""",
    },
    {
        "page": "Team Sheets",
        "slug": "team-sheets",
        "icon": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.5h7.2a2.8 2.8 0 0 1 2.8 2.8V20H6a2 2 0 0 1-2-2Z"/><path d="M20 5.5h-3.2A2.8 2.8 0 0 0 14 8.3V20h4a2 2 0 0 0 2-2Z"/><path d="M7.5 9h3M7.5 13h3M16.5 9h1M16.5 13h1"/></svg>""",
    },
    {
        "page": "Weather",
        "slug": "weather",
        "icon": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.65 17.65l1.42 1.42M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.65 6.35l1.42-1.42"/><circle cx="12" cy="12" r="4"/><path d="M6.5 19h10.8a3.2 3.2 0 0 0 .1-6.4A5.6 5.6 0 0 0 6.7 14 2.5 2.5 0 0 0 6.5 19Z"/></svg>""",
    },
    {
        "page": "Sportsbook",
        "slug": "sportsbook",
        "icon": """<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><path d="M14.7 8.2c-.6-.7-1.5-1-2.7-1-1.7 0-2.8.8-2.8 2s1 1.8 2.9 2.2c1.9.4 2.8 1 2.8 2.3s-1.2 2.2-3 2.2c-1.4 0-2.5-.4-3.2-1.3M12 5.5v13"/></svg>""",
    },
    {
        "page": "Parlay Lab",
        "slug": "parlay-lab",
        "icon": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h10M9 3v5l-4.6 8a3 3 0 0 0 2.6 4.5h10a3 3 0 0 0 2.6-4.5L15 8V3"/><path d="M7.2 15h9.6"/><circle cx="10" cy="17.5" r=".8"/><circle cx="14.5" cy="18" r=".8"/></svg>""",
    },
]

NAVIGATION = [item["page"] for item in NAV_ITEMS]
PAGE_TO_SLUG = {item["page"]: item["slug"] for item in NAV_ITEMS}
SLUG_TO_PAGE = {item["slug"]: item["page"] for item in NAV_ITEMS}

ALIASES = {
    "Dashboard": "Home",
    "Rankings": "Daily Board",
    "Team Cheat Sheets": "Team Sheets",
    "Player Profile": "Player Intelligence",
    "Player Profiles": "Player Intelligence",
    "Sportsbook Odds": "Sportsbook",
    "Model Lab": "Parlay Lab",
}

EXTRA_SLUGS = {
    "Player Intelligence": "player-intelligence",
    "Matchups": "matchups",
    "Park Factors": "park-factors",
    "Trends": "trends",
}
SLUG_TO_PAGE.update({slug: page for page, slug in EXTRA_SLUGS.items()})


def init_state() -> None:
    st.session_state.setdefault("page", "Home")
    st.session_state.setdefault("selected_player_id", None)
    st.session_state.setdefault("favorites", [])
    st.session_state.setdefault("slate_date", date.today())
    st.session_state.setdefault("generated_parlay", [])


def _clean_query_value(value: Any) -> str:
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value or "")


def _slug_for_page(page: str) -> str:
    return PAGE_TO_SLUG.get(page) or EXTRA_SLUGS.get(page) or "home"


def go(page: str, player_id: int | None = None) -> None:
    """Navigate programmatically and keep the URL synchronized."""
    target = ALIASES.get(page, page)
    st.session_state.page = target
    st.query_params["view"] = _slug_for_page(target)
    if player_id is not None:
        st.session_state.selected_player_id = int(player_id)
        st.query_params["player"] = str(int(player_id))
    else:
        try:
            del st.query_params["player"]
        except KeyError:
            pass


def render_top_navigation(as_of: str, games: int, hitters: int, updated_at: str = "") -> tuple[str, str]:
    init_state()

    requested_slug = _clean_query_value(st.query_params.get("view"))
    if requested_slug in SLUG_TO_PAGE:
        st.session_state.page = SLUG_TO_PAGE[requested_slug]

    query_player = _clean_query_value(st.query_params.get("player"))
    if query_player.isdigit():
        st.session_state.selected_player_id = int(query_player)

    try:
        current_date = datetime.strptime(as_of, "%Y-%m-%d").date() if as_of else st.session_state.slate_date
    except ValueError:
        current_date = st.session_state.slate_date

    current_page = st.session_state.page
    active_nav_page = current_page if current_page in NAVIGATION else ""

    logo = logo_data()
    left, middle, right = st.columns([2.45, 7.65, 2.15], gap="small", vertical_alignment="center")

    with left:
        st.markdown(
            f'<a class="dd-logo-shell" href="?view=home" target="_self" aria-label="Duggan\'s Dingers home">'
            f'<img src="{logo}" alt="Duggan\'s Dingers"></a>',
            unsafe_allow_html=True,
        )

    nav_links: list[str] = []
    for item in NAV_ITEMS:
        active = " active" if item["page"] == active_nav_page else ""
        nav_links.append(
            f'<a class="dd-nav-link{active}" href="?view={escape(item["slug"])}" target="_self" '
            f'aria-label="{escape(item["page"])}" title="{escape(item["page"])}">'
            f'<span class="dd-nav-icon">{item["icon"]}</span>'
            f'<span class="dd-nav-label">{escape(item["page"])}</span>'
            f'</a>'
        )

    with middle:
        st.markdown(
            '<nav class="dd-top-nav" aria-label="Primary navigation">' + "".join(nav_links) + "</nav>",
            unsafe_allow_html=True,
        )

    with right:
        chosen_date = st.date_input(
            "Slate date",
            value=current_date,
            key="top_slate_date",
            label_visibility="collapsed",
            help="Choose the MLB slate date.",
        )

    st.session_state.slate_date = chosen_date
    return current_page, chosen_date.isoformat()
