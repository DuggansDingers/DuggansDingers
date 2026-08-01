from __future__ import annotations

from html import escape
from pathlib import Path

import streamlit as st

from components.ui import image_data


def render_app_header(board: dict, page: str) -> None:
    brand = image_data(Path(__file__).resolve().parents[1] / "assets" / "header_brand_v28.png")
    alerts = int(st.session_state.get("last_alert_count", 0))
    live = "SNAPSHOT" if board.get("fast_start") else "LIVE"
    html = (
        '<header class="dd28-app-header">'
        f'<div class="dd28-header-context"><span>{escape(page)}</span><b><i></i>{live} DATA</b></div>'
        f'<a class="dd28-brand-lockup" href="?view=home" target="_self"><img src="{brand}" alt="DuggansDingers Home Run Intelligence"></a>'
        '<div class="dd28-header-actions">'
        '<a href="?view=props" target="_self"><span>&#9670;</span><b>PROP COMMAND</b></a>'
        f'<a href="?view=news-alerts" target="_self" class="notice"><span>&#9831;</span><b>{alerts}</b></a>'
        '</div></header>'
    )
    st.markdown(html, unsafe_allow_html=True)
