from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st

from components.neon_table import Column, render_neon_table
from components.ui import esc, headshot, odds, probability_fraction, safe_float, safe_int, score_color, team_logo

PICKS = [
    ("🔥", "TOP PICK", "#ff394f"),
    ("⚡", "POWER MATCHUP", "#ffae22"),
    ("🔥", "HOTTEST BAT", "#b95cff"),
    ("◎", "HIGHEST HR PROB", "#2dbbff"),
    ("▥", "BEST BALLPARK", "#3be98f"),
    ("★", "BEST VALUE", "#ff8329"),
]


def _reason_lines(player: dict[str, Any]) -> list[str]:
    reasons = [str(value) for value in (player.get("projection_reasons") or []) if value]
    if len(reasons) < 1:
        reasons.append(f"{safe_int(player.get('last_7_home_runs'))} HR in the last 7 games")
    if len(reasons) < 2:
        reasons.append(f"{safe_float(player.get('season_ops')):.3f} season OPS")
    return reasons[:2]


def _pick_cards(rankings: list[dict[str, Any]]) -> str:
    cards: list[str] = []
    for index, player in enumerate(rankings[:6]):
        icon, label, accent = PICKS[index]
        player_id = int(player.get("player_id") or 0)
        href = f"?view=player-intelligence&player={player_id}" if player_id else "?view=daily-board"
        pitcher = str(player.get("opposing_pitcher") or "TBD")
        hand = str(player.get("opposing_pitcher_hand") or "—")
        reasons = _reason_lines(player)
        if player.get("weather_available"):
            weather_reason = f'{player.get("weather_grade") or "—"} weather • {safe_float(player.get("weather_impact")):+.1f} HR impact'
            reasons = [weather_reason, *[reason for reason in reasons if reason != weather_reason]][:2]
        score = safe_float(player.get("dinger_score"))
        probability = probability_fraction(player.get("probability")) * 100
        cards.append(
            f'''
<a class="dd19-pick-link" href="{href}" target="_self">
<article class="dd19-pick" style="--accent:{accent}">
  <header><span>{icon}</span><b>{label}</b></header>
  <div class="dd19-photo-wrap"><img src="{headshot(player.get('player_id'), 500)}" alt="{esc(player.get('player_name'))}"></div>
  <h3>{esc(player.get('player_name'))}</h3>
  <div class="dd19-team">{esc(player.get('team_name'))} • {esc(player.get('position') or '—')}</div>
  <div class="dd19-metric-row"><strong>{score:.1f}<small>DINGER SCORE</small></strong><strong>{probability:.1f}%<small>HR PROBABILITY</small></strong></div>
  <ul><li>{esc(reasons[0])}</li><li>{esc(reasons[1])}</li></ul>
  <div class="dd20-home-weather"><span>WEATHER</span><b>{esc(player.get("weather_card_text") or ("PENDING" if not player.get("weather_available") else f"{player.get('weather_grade') or '—'} • {safe_float(player.get('weather_impact')):+.1f}"))}</b></div>
  <footer><span>Projected Starter:</span><b>{esc(pitcher if pitcher not in {"TBD","Not announced"} else "Awaiting announcement")}</b><em>{esc(hand)}HP</em></footer>
</article></a>'''
        )
    return '<div class="dd19-picks">' + "".join(cards) + "</div>"


def _player_cell(_: Any, row: dict[str, Any]) -> str:
    return (
        f'<div class="dd19-player-cell"><img src="{headshot(row.get("Player ID"), 120)}">'
        f'<div><b>{esc(row.get("Player"))}</b><span>{esc(row.get("Position"))}</span></div></div>'
    )


def _team_cell(_: Any, row: dict[str, Any]) -> str:
    return f'<div class="dd19-team-cell"><img src="{team_logo(row.get("Team ID"))}"><b>{esc(row.get("Team"))}</b></div>'


def _pitcher_cell(value: Any, row: dict[str, Any]) -> str:
    pitcher = str(value or "TBD")
    if pitcher in {"Not announced", "TBD", "None"}:
        return '<div class="dd19-pitcher pending"><b>TBD</b><span>Starter pending</span></div>'
    return (
        f'<div class="dd19-pitcher"><b>{esc(pitcher)}</b>'
        f'<span>{esc(row.get("Pitcher Hand") or "—")}HP • {safe_float(row.get("Pitcher HR9")):.2f} HR/9</span></div>'
    )


def _score_cell(value: Any, row: dict[str, Any]) -> str:
    score = safe_float(value)
    return (
        f'<div class="dd19-score" style="--score:{score_color(score)};--pct:{max(0, min(100, score)):.1f}%">'
        f'<b>{score:.1f}</b></div>'
    )


def _probability_cell(value: Any, row: dict[str, Any]) -> str:
    return f'<div class="dd19-prob"><b>{safe_float(value):.1f}%</b></div>'


def _form_cell(value: Any, total: int, color: str) -> str:
    count = max(0, min(total, safe_int(value)))
    bars = "".join(f'<i class="{"hit" if index < count else "miss"}"></i>' for index in range(total))
    return f'<div class="dd19-form" style="--form:{color}">{bars}</div>'


def _trend_cell(_: Any, row: dict[str, Any]) -> str:
    recent = safe_int(row.get("Last 7"))
    month = safe_int(row.get("Last 30"))
    color = "#ff384e" if recent >= 3 else "#ff8a23" if recent >= 2 else "#35a8ff"
    points = [12 + ((index * 11 + recent * 13 + month * 3) % 30) for index in range(9)]
    polyline = " ".join(f"{index * 10},{42 - point}" for index, point in enumerate(points))
    label = "HOT" if recent >= 2 else "WARM"
    return (
        f'<div class="dd19-trend" style="--trend:{color}"><svg viewBox="0 0 80 44">'
        f'<polyline points="{polyline}"/></svg><span>{label}</span></div>'
    )


def _rows(rankings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rank, player in enumerate(rankings[:25], 1):
        rows.append(
            {
                "Rank": rank,
                "Player": player.get("player_name"),
                "Player ID": player.get("player_id"),
                "Position": player.get("position"),
                "Team": player.get("team_name"),
                "Team ID": player.get("team_id"),
                "Opposing Pitcher": player.get("opposing_pitcher") or "TBD",
                "Pitcher Hand": player.get("opposing_pitcher_hand") or "—",
                "Pitcher HR9": player.get("pitcher_hr9"),
                "Dinger Score": safe_float(player.get("dinger_score")),
                "HR Probability": probability_fraction(player.get("probability")) * 100,
                "Best Price": player.get("best_odds") if player.get("best_odds") is not None else player.get("fair_odds"),
                "Season HR": safe_int(player.get("season_home_runs")),
                "Last 7": safe_int(player.get("last_7_home_runs")),
                "Last 15": safe_int(player.get("last_15_home_runs")),
                "Last 30": safe_int(player.get("last_30_home_runs")),
                "OPS": safe_float(player.get("season_ops")),
                "Trend": "",
            }
        )
    return rows


def render(board: dict[str, Any]) -> None:
    rankings = board.get("rankings", []) or []
    if not rankings:
        st.error("No rankings are available. Confirm the API keys and selected slate date, then refresh.")
        return

    date_text = str(board.get("date") or "")
    try:
        date_text = datetime.fromisoformat(date_text).strftime("%b %d, %Y")
    except ValueError:
        pass

    st.markdown(
        f'''<header class="dd19-masthead"><div class="dd19-wordmark">DUGGANS<span>DINGERS</span></div>
        <div class="dd19-tagline"><i></i><b>HOME RUN INTELLIGENCE</b><i></i></div>
        <div class="dd19-date">▣ &nbsp; {esc(date_text)}</div></header>''',
        unsafe_allow_html=True,
    )
    st.markdown(_pick_cards(rankings), unsafe_allow_html=True)
    st.markdown(
        '<div class="dd19-table-title"><div><i>♛</i><b>TOP 25 HOME RUN RANKINGS</b></div>'
        '<div class="dd19-title-actions"><a href="?view=daily-board" target="_self">⚙ Customize Columns</a>'
        '<a href="?view=daily-board" target="_self">⇩ Export CSV</a></div></div>',
        unsafe_allow_html=True,
    )

    columns = [
        Column("Rank", "RANK", formatter=lambda value, row: f'<span class="dd19-rank r{int(value) if int(value) <= 3 else 4}">{int(value)}</span>', width=".44fr", align="center"),
        Column("Player", "PLAYER", formatter=_player_cell, width="1.55fr"),
        Column("Team", "TEAM", formatter=_team_cell, width=".72fr"),
        Column("Opposing Pitcher", "PROBABLE PITCHER", formatter=_pitcher_cell, width="1.28fr"),
        Column("Dinger Score", "DINGER SCORE", formatter=_score_cell, width=".92fr", align="center"),
        Column("HR Probability", "HR PROB (%)", formatter=_probability_cell, width=".82fr", align="center"),
        Column("Best Price", "BEST PRICE", formatter=lambda value, row: f'<b class="dd19-price">{odds(value)}</b>', width=".7fr", align="center"),
        Column("Season HR", "SEASON HR", width=".62fr", align="center"),
        Column("Last 7", "LAST 7", formatter=lambda value, row: _form_cell(value, 7, "#ff394f"), width=".9fr"),
        Column("Last 15", "LAST 15", formatter=lambda value, row: _form_cell(value, 10, "#ff4df2"), width="1.0fr"),
        Column("OPS", "OPS", formatter=lambda value, row: f'<b class="dd19-ops">{safe_float(value):.3f}</b>', width=".58fr", align="center"),
        Column("Trend", "TREND", formatter=_trend_cell, width=".82fr", align="center"),
    ]
    render_neon_table(_rows(rankings), columns, key="dd19-home-table", max_height=360)

    announced = sum(1 for player in rankings if player.get("pitching_data_available"))
    weather = sum(1 for player in rankings if player.get("weather_available"))
    wind = sum(1 for player in rankings if safe_float(player.get("weather_impact")) > 2)
    st.markdown(
        f'''<div class="dd19-summary"><div><i>◎</i><span>FULL MLB SLATE</span><b>{safe_int(board.get('games'))} GAMES</b></div>
        <div><i>☁</i><span>WEATHER IMPACT</span><b>{weather} GAMES</b></div>
        <div><i>≋</i><span>WIND BOOST</span><b>{wind} PLAYERS</b></div>
        <div><i>⌂</i><span>PROBABLE PITCHERS</span><b>{announced} MATCHED</b></div>
        <div><i>⚾</i><span>RANKED HITTERS</span><b>{len(rankings)}</b></div></div>''',
        unsafe_allow_html=True,
    )
