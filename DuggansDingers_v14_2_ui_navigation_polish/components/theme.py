from __future__ import annotations

from pathlib import Path

import streamlit as st

from components.theme_base import apply_theme as apply_base_theme


CSS_FILE = Path(__file__).resolve().parents[1] / "assets" / "v18.css"


def apply_theme() -> None:
    apply_base_theme()
    try:
        css = CSS_FILE.read_text(encoding="utf-8")
    except OSError:
        css = ""
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
