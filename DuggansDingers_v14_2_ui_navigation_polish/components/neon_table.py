from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any, Callable, Iterable, Mapping

import streamlit as st


@dataclass(frozen=True)
class Column:
    key: str
    label: str
    formatter: Callable[[Any, Mapping[str, Any]], str] | None = None
    progress_max: float | None = None
    accent: str = "#27c7ff"
    width: str = "auto"
    align: str = "left"


def _num(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _text(value: Any) -> str:
    if value in (None, ""):
        return "—"
    return str(value)


def progress_html(value: Any, maximum: float, accent: str, label: str | None = None) -> str:
    number = max(0.0, _num(value))
    width = min(100.0, number / maximum * 100.0) if maximum > 0 else 0.0
    shown = label if label is not None else f"{number:.1f}"
    return (
        f'<div class="dd-neon-progress" style="--bar:{escape(accent)}">'
        f'<div class="dd-neon-progress-track"><i style="width:{width:.1f}%"></i></div>'
        f'<b>{escape(shown)}</b></div>'
    )


def render_neon_table(
    rows: Iterable[Mapping[str, Any]],
    columns: list[Column],
    *,
    key: str,
    empty_message: str = "No records are available.",
    max_height: int | None = None,
) -> None:
    records = list(rows)
    if not records:
        st.markdown(f'<div class="dd-empty">{escape(empty_message)}</div>', unsafe_allow_html=True)
        return

    header = "".join(
        f'<div class="dd-neon-th" style="text-align:{column.align};min-width:{column.width}">{escape(column.label)}</div>'
        for column in columns
    )
    body_rows: list[str] = []
    for index, row in enumerate(records):
        cells: list[str] = []
        for column in columns:
            value = row.get(column.key)
            if column.formatter is not None:
                rendered = column.formatter(value, row)
            elif column.progress_max is not None:
                rendered = progress_html(value, column.progress_max, column.accent)
            else:
                rendered = escape(_text(value))
            cells.append(
                f'<div class="dd-neon-td" style="text-align:{column.align};min-width:{column.width}">{rendered}</div>'
            )
        body_rows.append(
            f'<div class="dd-neon-tr" style="--row-index:{index}">' + "".join(cells) + "</div>"
        )

    template = " ".join(column.width for column in columns)
    height_style = f"max-height:{int(max_height)}px;overflow:auto;" if max_height else ""
    st.markdown(
        f'<div id="{escape(key)}" class="dd-neon-table-shell" style="{height_style}">'
        f'<div class="dd-neon-grid dd-neon-head" style="grid-template-columns:{template}">{header}</div>'
        + "".join(
            f'<div class="dd-neon-grid" style="grid-template-columns:{template}">{row_html}</div>'
            for row_html in body_rows
        )
        + "</div>",
        unsafe_allow_html=True,
    )
