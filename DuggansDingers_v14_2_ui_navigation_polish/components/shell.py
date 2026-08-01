from __future__ import annotations

from pathlib import Path
import streamlit as st

from components.ui import image_data


def render_app_header(board: dict, page: str) -> None:
    desktop = image_data(Path(__file__).resolve().parents[1] / "assets" / "v34_hero_desktop.jpg")
    mobile = image_data(Path(__file__).resolve().parents[1] / "assets" / "v34_hero_mobile.jpg")
    st.markdown(
        '<header class="dd34-hero">'
        '<picture>'
        f'<source media="(max-width:780px)" srcset="{mobile}">'
        f'<img src="{desktop}" alt="DuggansDingerz home run intelligence">'
        '</picture>'
        '</header>',
        unsafe_allow_html=True,
    )
