from __future__ import annotations

from typing import Sequence

import altair as alt
import pandas as pd
import streamlit as st


NEON = ["#20c5ff", "#a65cff", "#35f083", "#ffd23f", "#ff4d6d", "#00f0ff"]


def _prepare(data: pd.DataFrame) -> tuple[pd.DataFrame, str, list[str]]:
    frame = data.copy()
    if frame.index.name is None:
        frame.index.name = "Category"
    frame = frame.reset_index()
    category = str(frame.columns[0])
    values = [str(column) for column in frame.columns[1:]]
    long = frame.melt(id_vars=[category], value_vars=values, var_name="Series", value_name="Value")
    long["Value"] = pd.to_numeric(long["Value"], errors="coerce").fillna(0)
    return long, category, values


def _style(chart: alt.Chart) -> alt.Chart:
    return (
        chart
        .configure(background="transparent")
        .configure_view(stroke="#173b58", strokeWidth=1, fill="#06111b")
        .configure_axis(
            labelColor="#8fa9bd",
            titleColor="#62c9ff",
            gridColor="#183149",
            domainColor="#29506c",
            tickColor="#29506c",
            labelFont="Inter",
            titleFont="Inter",
            labelFontSize=11,
            titleFontSize=11,
            titleFontWeight=700,
        )
        .configure_legend(
            labelColor="#b8cad8",
            titleColor="#62c9ff",
            orient="top",
            direction="horizontal",
            padding=8,
            symbolType="circle",
        )
    )


def neon_bar_chart(
    data: pd.DataFrame,
    *,
    height: int = 320,
    palette: Sequence[str] = NEON,
    horizontal: bool = False,
    value_title: str | None = None,
) -> None:
    long, category, series = _prepare(data)
    color = (
        alt.Color(
            "Series:N",
            scale=alt.Scale(domain=series, range=list(palette)[: max(1, len(series))]),
            legend=None if len(series) == 1 else alt.Legend(title=None),
        )
    )

    if horizontal:
        encoding = {
            "y": alt.Y(f"{category}:N", sort=None, title=None, axis=alt.Axis(labelLimit=190)),
            "x": alt.X("Value:Q", title=value_title, scale=alt.Scale(zero=True)),
            "color": color,
            "tooltip": [
                alt.Tooltip(f"{category}:N", title="Category"),
                alt.Tooltip("Series:N"),
                alt.Tooltip("Value:Q", format=".2f"),
            ],
        }
    else:
        encoding = {
            "x": alt.X(f"{category}:N", sort=None, title=None, axis=alt.Axis(labelAngle=-35, labelLimit=150)),
            "y": alt.Y("Value:Q", title=value_title, scale=alt.Scale(zero=True)),
            "xOffset": alt.XOffset("Series:N"),
            "color": color,
            "tooltip": [
                alt.Tooltip(f"{category}:N", title="Category"),
                alt.Tooltip("Series:N"),
                alt.Tooltip("Value:Q", format=".2f"),
            ],
        }

    glow = alt.Chart(long).mark_bar(
        opacity=0.20,
        cornerRadiusTopLeft=5,
        cornerRadiusTopRight=5,
        strokeWidth=8,
    ).encode(**encoding)

    foreground = alt.Chart(long).mark_bar(
        opacity=0.92,
        cornerRadiusTopLeft=4,
        cornerRadiusTopRight=4,
        stroke="#ffffff",
        strokeOpacity=0.08,
        strokeWidth=1,
    ).encode(**encoding)

    chart = (glow + foreground).properties(height=height, padding={"left": 8, "right": 10, "top": 8, "bottom": 4})
    st.altair_chart(_style(chart), use_container_width=True)


def neon_line_chart(
    data: pd.DataFrame,
    *,
    height: int = 300,
    palette: Sequence[str] = NEON,
    value_title: str | None = None,
) -> None:
    long, category, series = _prepare(data)
    color = alt.Color(
        "Series:N",
        scale=alt.Scale(domain=series, range=list(palette)[: max(1, len(series))]),
        legend=None if len(series) == 1 else alt.Legend(title=None),
    )
    common = {
        "x": alt.X(f"{category}:N", sort=None, title=None, axis=alt.Axis(labelAngle=-25)),
        "y": alt.Y("Value:Q", title=value_title, scale=alt.Scale(zero=False)),
        "color": color,
        "tooltip": [
            alt.Tooltip(f"{category}:N", title="Window"),
            alt.Tooltip("Series:N"),
            alt.Tooltip("Value:Q", format=".2f"),
        ],
    }

    glow = alt.Chart(long).mark_line(strokeWidth=9, opacity=0.16, interpolate="monotone").encode(**common)
    line = alt.Chart(long).mark_line(strokeWidth=3, interpolate="monotone").encode(**common)
    points = alt.Chart(long).mark_circle(size=90, opacity=0.95, stroke="#06111b", strokeWidth=2).encode(**common)

    chart = (glow + line + points).properties(height=height, padding={"left": 8, "right": 10, "top": 8, "bottom": 4})
    st.altair_chart(_style(chart), use_container_width=True)
