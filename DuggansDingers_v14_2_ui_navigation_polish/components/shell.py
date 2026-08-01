from __future__ import annotations

from html import escape
from pathlib import Path

import streamlit as st

from components.ui import image_data


def render_app_header(board: dict, page: str) -> None:
    brand = image_data(Path(__file__).resolve().parents[1] / "assets" / "header_brand_v29.png")
    alerts = int(st.session_state.get("last_alert_count", 0))
    games = len(board.get("games_meta", []) or [])
    hitters = len(board.get("rankings", []) or [])
    slate = str(board.get("date") or "Today")
    source = "FAST START" if board.get("fast_start") else "LIVE"
    weather_count = sum(1 for game in (board.get("games_meta", []) or []) if game.get("weather_available"))
    priced_count = sum(1 for player in (board.get("rankings", []) or []) if player.get("best_odds") is not None)

    html = (
        '<header class="dd29-app-header">'
          '<div class="dd29-header-glow"></div>'
          f'<div class="dd29-header-context"><span>{escape(page)}</span><b><i></i>{source} DATA</b></div>'
          f'<a class="dd29-brand-lockup" href="?view=home" target="_self"><img src="{brand}" alt="DuggansDingers Home Run Intelligence"></a>'
          '<div class="dd29-header-actions">'
            '<a class="props" href="?view=props" target="_self"><span>&#9670;</span><b>PROP COMMAND</b><em>NEW</em></a>'
            f'<a class="alerts" href="?view=news-alerts" target="_self"><span>&#9831;</span><b>{alerts}</b></a>'
          '</div>'
          '<div class="dd29-header-strip">'
            f'<div><span>SLATE</span><b>{escape(slate)}</b></div>'
            f'<div><span>GAMES</span><b>{games}</b></div>'
            f'<div><span>HITTERS</span><b>{hitters}</b></div>'
            f'<div><span>WEATHER</span><b>{weather_count} LIVE</b></div>'
            f'<div><span>PRICED PROPS</span><b>{priced_count}</b></div>'
            '<div class="pulse"><span>MODEL STATUS</span><b><i></i> ONLINE</b></div>'
          '</div>'
        '</header>'
    )
    st.markdown(html, unsafe_allow_html=True)
