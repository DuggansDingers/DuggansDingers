from __future__ import annotations

from html import escape
from pathlib import Path

import streamlit as st

from components.ui import image_data


def render_app_header(board: dict, page: str) -> None:
    wordmark = image_data(Path(__file__).resolve().parents[1] / "assets" / "wordmark_v25.png")
    alerts = int(st.session_state.get("last_alert_count",0))
    st.markdown(
        f'''<header class="dd25-app-header">
          <div class="dd25-header-page">{escape(page)}</div>
          <a href="?view=home" target="_self"><img src="{wordmark}" alt="DuggansDingers"></a>
          <div class="dd25-header-actions">
            <span title="Search">&#8981;</span>
            <span class="notice" title="Alerts">&#9831;<b>{alerts}</b></span>
            <span title="Account">&#9711;</span>
          </div>
        </header>''',
        unsafe_allow_html=True,
    )
