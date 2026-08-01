from __future__ import annotations

from html import escape
from pathlib import Path

import streamlit as st

from components.ui import image_data


def render_app_header(board: dict, page: str) -> None:
    desktop_banner = image_data(Path(__file__).resolve().parents[1] / "assets" / "brand_banner_v32.jpg")
    mobile_banner = image_data(Path(__file__).resolve().parents[1] / "assets" / "brand_banner_v32_mobile.jpg")

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
        '<header class="dd32-app-header">'
          '<picture class="dd32-brand-hero">'
            f'<source media="(max-width: 780px)" srcset="{mobile_banner}">'
            f'<img src="{desktop_banner}" alt="DuggansDingers AI baseball analytics">'
          '</picture>'
          '<div class="dd32-action-row">'
            '<nav class="dd32-action-left">'
              '<a class="weather" href="?view=weather" target="_self"><span>☀</span><b>WEATHER</b><em>LIVE</em></a>'
              '<a class="kitchen" href="?view=the-kitchen" target="_self"><span>♨</span><b>THE KITCHEN</b><em>COOK</em></a>'
            '</nav>'
            '<div class="dd32-mini-brand"><b>DUGGANS<span>DINGERS</span></b><small>HOME RUN INTELLIGENCE</small></div>'
            '<nav class="dd32-action-right">'
              '<a class="props" href="?view=props" target="_self"><span>◆</span><b>PROP COMMAND</b><em>HOT</em></a>'
              f'<a class="alerts" href="?view=news-alerts" target="_self"><span>♧</span><b>{alerts}</b></a>'
            '</nav>'
          '</div>'
          '<div class="dd32-status-strip">'
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
