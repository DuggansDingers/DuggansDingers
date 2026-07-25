from __future__ import annotations

from pathlib import Path

import streamlit as st

from components.theme_base import apply_theme as apply_base_theme

CSS_FILES = [
    Path(__file__).resolve().parents[1] / "assets" / "v18.css",
    Path(__file__).resolve().parents[1] / "assets" / "v19.css",
    Path(__file__).resolve().parents[1] / "assets" / "v20.css",
    Path(__file__).resolve().parents[1] / "assets" / "v21.css",
    Path(__file__).resolve().parents[1] / "assets" / "v22.css",
]


def apply_theme() -> None:
    apply_base_theme()
    for path in CSS_FILES:
        try:
            css = path.read_text(encoding="utf-8")
        except OSError:
            css = ""
        if css:
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
