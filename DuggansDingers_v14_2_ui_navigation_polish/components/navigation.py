from __future__ import annotations

from datetime import date, datetime
from html import escape
from typing import Any

import streamlit as st

from components.ui import logo_data

NAV_ITEMS = [
    ("Home","home","Dashboard","home",""),
    ("Daily Board","daily-board","Player Rankings","rank","hitters"),
    ("Team Sheets","team-sheets","Team Sheets","sheet",""),
    ("Weather","weather","Ballpark Weather","weather",""),
    ("Game Sims","game-sims","Game Sims","cube","games"),
    ("Sportsbook","sportsbook","Sportsbook Odds","money","odds"),
    ("Props","props","Prop Command","props","props"),
    ("The Kitchen","the-kitchen","The Kitchen","lab","parlay"),
    ("Player Intelligence","player-intelligence","Player Profiles","user",""),
    ("Park Factors","park-factors","Park Factors","park",""),
    ("Matchups","matchups","Matchups","matchup","games"),
    ("News & Alerts","news-alerts","News & Alerts","bell","alerts"),
    ("Settings","settings","Settings","settings",""),
]

ICONS = {
    "home":'<svg viewBox="0 0 24 24"><path d="M3 11.2 12 3l9 8.2"/><path d="M5.5 10.2V21h13V10.2"/><path d="M9.2 21v-6.4h5.6V21"/></svg>',
    "rank":'<svg viewBox="0 0 24 24"><path d="M4 20V11h4v9M10 20V6h4v14M16 20V3h4v17"/></svg>',
    "sheet":'<svg viewBox="0 0 24 24"><path d="M5 3h14v18H5z"/><path d="M8 7h8M8 11h8M8 15h8"/></svg>',
    "weather":'<svg viewBox="0 0 24 24"><path d="M12 2v2M4.9 4.9l1.4 1.4M2 12h2M20 12h2M17.7 6.3l1.4-1.4"/><circle cx="12" cy="12" r="4"/><path d="M5.8 20h11.5a3.2 3.2 0 0 0 .1-6.4A5.7 5.7 0 0 0 6.8 15 2.6 2.6 0 0 0 5.8 20Z"/></svg>',
    "cube":'<svg viewBox="0 0 24 24"><path d="M4 17V9l8-5 8 5v8l-8 5Z"/><path d="m4 9 8 5 8-5M12 14v8"/></svg>',
    "money":'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5"/><path d="M15 8.2c-.7-.7-1.6-1-2.9-1-1.8 0-3 .8-3 2.1s1 1.8 3 2.2c2 .4 3 1.1 3 2.4s-1.2 2.2-3.1 2.2c-1.5 0-2.6-.4-3.4-1.3M12 5.3v13.4"/></svg>',
    "lab":'<svg viewBox="0 0 24 24"><path d="M7 3h10M9 3v5l-4.6 8a3 3 0 0 0 2.6 4.5h10a3 3 0 0 0 2.6-4.5L15 8V3"/><path d="M7.2 15h9.6"/></svg>',
    "props":'<svg viewBox="0 0 24 24"><path d="M4 18V9M9 18V5M14 18v-7M19 18V3"/><path d="M3 20h18"/><circle cx="9" cy="5" r="1.5"/><circle cx="19" cy="3" r="1.5"/></svg>',
    "user":'<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4.5 21a7.5 7.5 0 0 1 15 0"/></svg>',
    "park":'<svg viewBox="0 0 24 24"><path d="M3 18V7l9-4 9 4v11l-9 3Z"/><path d="M7 16V9h10v7M12 7v12"/></svg>',
    "matchup":'<svg viewBox="0 0 24 24"><path d="m4 4 16 16M20 4 4 20"/><path d="m3 6 3-3 2 2M21 18l-3 3-2-2M18 3l3 3-2 2M6 21l-3-3 2-2"/></svg>',
    "bell":'<svg viewBox="0 0 24 24"><path d="M6 17h12l-1.5-2.2V10a4.5 4.5 0 1 0-9 0v4.8Z"/><path d="M10 20h4"/></svg>',
    "settings":'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19 13.5v-3l2-1.2-2-3.4-2.2 1a8 8 0 0 0-2.6-1.5L14 3h-4l-.2 2.4a8 8 0 0 0-2.6 1.5l-2.2-1-2 3.4 2 1.2v3l-2 1.2 2 3.4 2.2-1a8 8 0 0 0 2.6 1.5L10 21h4l.2-2.4a8 8 0 0 0 2.6-1.5l2.2 1 2-3.4Z"/></svg>',
}

PAGE_TO_SLUG = {page:slug for page,slug,_,_,_ in NAV_ITEMS}
SLUG_TO_PAGE = {slug:page for page,slug,_,_,_ in NAV_ITEMS}
ALIASES = {
    "Dashboard":"Home","Rankings":"Daily Board","Team Cheat Sheets":"Team Sheets",
    "Player Profile":"Player Intelligence","Player Profiles":"Player Intelligence",
    "Sportsbook Odds":"Sportsbook","Model Lab":"The Kitchen","Parlay Lab":"The Kitchen",
}


def init_state() -> None:
    st.session_state.setdefault("page","Home")
    st.session_state.setdefault("selected_player_id",None)
    st.session_state.setdefault("favorites",[])
    st.session_state.setdefault("slate_date",date.today())
    st.session_state.setdefault("generated_parlay",[])


def _query_value(value: Any) -> str:
    if isinstance(value,list):
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
    return PAGE_TO_SLUG.get(ALIASES.get(page,page),"home")


def go(page: str, player_id: int | None = None) -> None:
    page = ALIASES.get(page,page)
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


def render_navigation(as_of: str, games: int, hitters: int, updated_at: str = "") -> tuple[str,str]:
    current_page = page_from_query()
    try:
        current_date = datetime.strptime(as_of,"%Y-%m-%d").date() if as_of else st.session_state.slate_date
    except ValueError:
        current_date = st.session_state.slate_date

    counts = {
        "games": int(games or 0),
        "hitters": int(hitters or 0),
        "odds": int(st.session_state.get("last_odds_count",0)),
        "parlay": len(st.session_state.get("generated_parlay",[]) or []),
        "alerts": int(st.session_state.get("last_alert_count",0)),
        "props": int(st.session_state.get("last_prop_count",0)),
    }

    with st.sidebar:
        st.markdown(
            f'<a class="dd25-side-logo" href="?view=home" target="_self"><img src="{logo_data()}" alt="DuggansDingers"></a>',
            unsafe_allow_html=True,
        )
        links = []
        for page,slug,label,icon_name,count_key in NAV_ITEMS:
            active = " active" if page == current_page else ""
            count = counts.get(count_key,0) if count_key else 0
            badge = f'<em>{count}</em>' if count else ""
            links.append(
                f'<a class="dd25-side-link{active}" href="?view={escape(slug)}" target="_self">'
                f'<span class="dd25-side-icon">{ICONS[icon_name]}</span><b>{escape(label)}</b>{badge}</a>'
            )
        st.markdown('<nav class="dd25-side-nav">'+"".join(links)+"</nav>",unsafe_allow_html=True)
        st.markdown('<div class="dd25-side-spacer"></div>',unsafe_allow_html=True)
        chosen_date = st.date_input("Slate date",value=current_date,key="sidebar_slate_date")
        if st.button("↻ Refresh live data",key="sidebar_force_live",use_container_width=True):
            from data_service import load_board
            load_board.clear()
            st.session_state["_force_live_refresh"] = True
            st.rerun()

        updated = str(updated_at or "")
        if updated:
            try:
                updated = datetime.fromisoformat(updated.replace("Z","+00:00")).strftime("%I:%M %p ET")
            except ValueError:
                pass
        st.markdown(
            f'<div class="dd25-side-status"><span>DATA SOURCE</span><b>WeatherAPI / NWS</b><i><em></em> Live Updated</i><small>{escape(updated or "LIVE")}</small></div>',
            unsafe_allow_html=True,
        )

    # iPhone/mobile navigation: the desktop sidebar is intentionally replaced by
    # a thumb-friendly fixed navigation dock. All app sections remain reachable.
    mobile_links = []
    for page, slug, label, icon_name, count_key in NAV_ITEMS:
        active = " active" if page == current_page else ""
        short_label = {
            "Player Rankings": "Rankings",
            "Ballpark Weather": "Weather",
            "Sportsbook Odds": "Odds",
            "Player Profiles": "Players",
            "News & Alerts": "Alerts",
            "Prop Command": "Props",
            "The Kitchen": "Kitchen",
        }.get(label, label)
        count = counts.get(count_key, 0) if count_key else 0
        badge = f'<em>{count}</em>' if count else ""
        mobile_links.append(
            f'<a class="dd27-mobile-link{active}" href="?view={escape(slug)}" target="_self">'
            f'<span>{ICONS[icon_name]}</span><b>{escape(short_label)}</b>{badge}</a>'
        )
    st.markdown(
        '<nav class="dd27-mobile-nav" aria-label="Mobile navigation">'
        '<div class="dd27-mobile-nav-scroll">' + "".join(mobile_links) + '</div></nav>',
        unsafe_allow_html=True,
    )

    st.session_state.slate_date = chosen_date
    return current_page, chosen_date.isoformat()


render_top_navigation = render_navigation
