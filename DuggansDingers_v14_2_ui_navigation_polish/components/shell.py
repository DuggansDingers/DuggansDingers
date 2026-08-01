from __future__ import annotations

from html import escape
from pathlib import Path

import streamlit as st

from components.ui import image_data


def render_app_header(board: dict, page: str) -> None:
    brand = image_data(Path(__file__).resolve().parents[1] / "assets" / "header_wordmark_v30.png")
    alerts = int(st.session_state.get("last_alert_count", 0))
    games = len(board.get("games_meta", []) or [])
    hitters = len(board.get("rankings", []) or [])
    weather_count = sum(
        1 for game in (board.get("games_meta", []) or [])
        if game.get("weather_available")
    )
    priced_count = sum(
        1 for player in (board.get("rankings", []) or [])
        if player.get("best_odds") is not None
    )
    source = "FAST START" if board.get("fast_start") else "LIVE"
    slate = str(board.get("date") or "Today")

    html = (
        '<header class="dd30-app-header">'
          '<div class="dd30-header-main">'
            '<nav class="dd30-header-left">'
              '<a class="weather" href="?view=weather" target="_self"><span>☀</span><b>WEATHER</b><em>LIVE</em></a>'
              '<a class="kitchen" href="?view=the-kitchen" target="_self"><span>♨</span><b>THE KITCHEN</b><em>COOK</em></a>'
            '</nav>'
            f'<a class="dd30-brand-lockup" href="?view=home" target="_self"><img src="{brand}" alt="DuggansDingers Home Run Intelligence"></a>'
            '<nav class="dd30-header-right">'
              '<a class="props" href="?view=props" target="_self"><span>◆</span><b>PROP COMMAND</b><em>HOT</em></a>'
              f'<a class="alerts" href="?view=news-alerts" target="_self"><span>♧</span><b>{alerts}</b></a>'
            '</nav>'
          '</div>'
          '<div class="dd30-header-strip">'
            f'<div><span>PAGE</span><b>{escape(page)}</b></div>'
            f'<div><span>SLATE</span><b>{escape(slate)}</b></div>'
            f'<div><span>GAMES</span><b>{games}</b></div>'
            f'<div><span>HITTERS</span><b>{hitters}</b></div>'
            f'<div><span>WEATHER</span><b>{weather_count} LIVE</b></div>'
            f'<div><span>PRICED PROPS</span><b>{priced_count}</b></div>'
            f'<div class="status"><span>MODEL</span><b><i></i>{source}</b></div>'
          '</div>'
        '</header>'
    )
    st.markdown(html, unsafe_allow_html=True)
