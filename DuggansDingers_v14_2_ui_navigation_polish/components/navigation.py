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
        "label": "Dashboard",
        "description": "Top picks and live board",
        "icon": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 11.2 12 3l9 8.2"/><path d="M5.5 10.2V21h13V10.2"/><path d="M9.2 21v-6.4h5.6V21"/></svg>""",
    },
    {
        "page": "Daily Board",
        "slug": "daily-board",
        "label": "Player Rankings",
        "description": "Full hitter intelligence",
        "icon": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4h14v16H5z"/><path d="M8 8h8M8 12h8M8 16h5"/><circle cx="3" cy="8" r="1"/><circle cx="3" cy="12" r="1"/><circle cx="3" cy="16" r="1"/></svg>""",
    },
    {
        "page": "Player Intelligence",
        "slug": "player-intelligence",
        "label": "Player Profiles",
        "description": "Deep player breakdowns",
        "icon": """<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4.5 21a7.5 7.5 0 0 1 15 0"/></svg>""",
    },
    {
        "page": "Team Sheets",
        "slug": "team-sheets",
        "label": "Team Sheets",
        "description": "Side-by-side matchup boards",
        "icon": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.5h7.2a2.8 2.8 0 0 1 2.8 2.8V20H6a2 2 0 0 1-2-2Z"/><path d="M20 5.5h-3.2A2.8 2.8 0 0 0 14 8.3V20h4a2 2 0 0 0 2-2Z"/><path d="M7.5 9h3M7.5 13h3M16.5 9h1M16.5 13h1"/></svg>""",
    },
    {
        "page": "Weather",
        "slug": "weather",
        "label": "Ballpark Weather",
        "description": "Wind and carry by field",
        "icon": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.65 17.65l1.42 1.42M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.65 6.35l1.42-1.42"/><circle cx="12" cy="12" r="4"/><path d="M6.5 19h10.8a3.2 3.2 0 0 0 .1-6.4A5.6 5.6 0 0 0 6.7 14 2.5 2.5 0 0 0 6.5 19Z"/></svg>""",
    },
    {
        "page": "Game Sims",
        "slug": "game-sims",
        "label": "Game Sims",
        "description": "Scores, hits, HR, K and SB",
        "icon": """<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 17V9l8-5 8 5v8l-8 5Z"/><path d="m4 9 8 5 8-5M12 14v8"/><circle cx="12" cy="9" r="2"/></svg>""",
    },
    {
        "page": "Sportsbook",
        "slug": "sportsbook",
        "label": "Sportsbook Odds",
        "description": "DraftKings and FanDuel",
        "icon": """<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><path d="M14.7 8.2c-.6-.7-1.5-1-2.7-1-1.7 0-2.8.8-2.8 2s1 1.8 2.9 2.2c1.9.4 2.8 1 2.8 2.3s-1.2 2.2-3 2.2c-1.4 0-2.5-.4-3.2-1.3M12 5.5v13"/></svg>""",
    },
    {
        "page": "Parlay Lab",
        "slug": "parlay-lab",
        "label": "Parlay Lab",
        "description": "Build and reroll locked legs",
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


def page_from_query() -> str:
    init_state()
    requested_slug = _clean_query_value(st.query_params.get("view"))
    if requested_slug in SLUG_TO_PAGE:
        st.session_state.page = SLUG_TO_PAGE[requested_slug]
    query_player = _clean_query_value(st.query_params.get("player"))
    if query_player.isdigit():
        st.session_state.selected_player_id = int(query_player)
    return str(st.session_state.page)


def _slug_for_page(page: str) -> str:
    return PAGE_TO_SLUG.get(page) or EXTRA_SLUGS.get(page) or "home"


def go(page: str, player_id: int | None = None) -> None:
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


def render_navigation(as_of: str, games: int, hitters: int, updated_at: str = "") -> tuple[str, str]:
    current_page = page_from_query()
    try:
        current_date = datetime.strptime(as_of, "%Y-%m-%d").date() if as_of else st.session_state.slate_date
    except ValueError:
        current_date = st.session_state.slate_date

    logo = logo_data()
    with st.sidebar:
        st.markdown(
            f'<a class="dd-side-logo" href="?view=home" target="_self"><img src="{logo}" alt="Duggan\'s Dingers"></a>',
            unsafe_allow_html=True,
        )
        links: list[str] = []
        for item in NAV_ITEMS:
            active = " active" if item["page"] == current_page else ""
            links.append(
                f'<a class="dd-side-link{active}" href="?view={escape(item["slug"])}" target="_self">'
                f'<span class="dd-side-icon">{item["icon"]}</span>'
                f'<span class="dd-side-copy"><b>{escape(item["label"])}</b><small>{escape(item["description"])}</small></span>'
                f'</a>'
            )
        st.markdown('<nav class="dd-side-nav">' + "".join(links) + '</nav>', unsafe_allow_html=True)
        st.markdown('<div class="dd-side-divider"></div>', unsafe_allow_html=True)
        chosen_date = st.date_input(
            "Slate date",
            value=current_date,
            key="sidebar_slate_date",
            help="Choose the MLB slate date.",
        )
        updated = str(updated_at or "")
        if updated:
            try:
                updated = datetime.fromisoformat(updated.replace("Z", "+00:00")).strftime("%I:%M %p")
            except ValueError:
                pass
        st.markdown(
            f'''<div class="dd-side-status">
              <div><span>Full MLB Slate</span><b>{games} games</b></div>
              <div><span>Ranked Hitters</span><b>{hitters}</b></div>
              <div><span>Data Updated</span><b>{escape(updated or 'Live')}</b></div>
              <i><em></em> LIVE MODEL</i>
            </div>''',
            unsafe_allow_html=True,
        )

    st.session_state.slate_date = chosen_date
    return current_page, chosen_date.isoformat()


# Compatibility with prior app.py imports.
render_top_navigation = render_navigation
