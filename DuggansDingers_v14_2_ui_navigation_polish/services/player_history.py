from __future__ import annotations

from typing import Any

import requests
import streamlit as st

MLB_BASE_URL = "https://statsapi.mlb.com/api/v1"


def safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def safe_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


@st.cache_data(ttl=21600, show_spinner=False)
def get_year_by_year_history(player_id: int) -> list[dict[str, Any]]:
    response = requests.get(
        f"{MLB_BASE_URL}/people/{player_id}/stats",
        params={"stats": "yearByYear", "group": "hitting"},
        timeout=35,
    )
    response.raise_for_status()
    result = response.json()
    rows: list[dict[str, Any]] = []
    for stats_group in result.get("stats", []):
        for split in stats_group.get("splits", []) or []:
            stat = split.get("stat", {}) or {}
            season = str(split.get("season") or "")
            if not season:
                continue
            rows.append({
                "Season": season,
                "Team": (split.get("team") or {}).get("name", "Multiple/Unknown"),
                "G": safe_int(stat.get("gamesPlayed")),
                "HR": safe_int(stat.get("homeRuns")),
                "RBI": safe_int(stat.get("rbi")),
                "PA": safe_int(stat.get("plateAppearances")),
                "AVG": safe_float(stat.get("avg")),
                "OBP": safe_float(stat.get("obp")),
                "SLG": safe_float(stat.get("slg")),
                "OPS": safe_float(stat.get("ops")),
            })
    rows.sort(key=lambda row: row["Season"], reverse=True)
    return rows
