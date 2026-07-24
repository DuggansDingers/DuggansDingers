from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st

from components.navigation import go
from components.neon_table import Column, render_neon_table
from components.ui import (
    esc,
    headshot,
    odds,
    percent,
    probability_fraction,
    safe_float,
    safe_int,
    score_color,
    team_logo,
)


PICK_LABELS = [
    ("TOP PICK", "#ff3c45"),
    ("POWER MATCHUP", "#ff9f1c"),
    ("HOTTEST BAT", "#a85cff"),
    ("HIGHEST HR PROB", "#27c7ff"),
    ("BEST BALLPARK", "#35f29a"),
    ("BEST VALUE", "#ff7b22"),
]


def _reason_lines(player: dict[str, Any]) -> list[str]:
    reasons = [str(value) for value in (player.get("projection_reasons") or []) if value]
    pitcher = str(player.get("opposing_pitcher") or "Not announced")
    if player.get("pitching_data_available") and pitcher != "Not announced":
        pitcher_reason = f"vs {pitcher} • {safe_float(player.get('pitcher_hr9')):.2f} HR/9"
        if not any(pitcher in reason for reason in reasons):
            reasons.append(pitcher_reason)
    if len(reasons) < 2:
        reasons.append(f"{safe_int(player.get('last_30_home_runs'))} HR in last 30 games")
    return reasons[:2]


def _top_pick_cards(rankings: list[dict[str, Any]]) -> str:
    cards: list[str] = []
    for rank, player in enumerate(rankings[:6], 1):
        label, accent = PICK_LABELS[rank - 1]
        player_id = int(player.get("player_id") or 0)
        href = f"?view=player-intelligence&player={player_id}" if player_id else "?view=daily-board"
        reasons = _reason_lines(player)
        pitcher = str(player.get("opposing_pitcher") or "Not announced")
        hand = str(player.get("opposing_pitcher_hand") or "—")
        pitcher_detail = (
            f"{hand}HP • {safe_float(player.get('pitcher_hr9')):.2f} HR/9 • {safe_float(player.get('pitcher_era')):.2f} ERA"
            if player.get("pitching_data_available")
            else "Probable starter pending"
        )
        cards.append(
            f'''
<a class="dd-home-pick-link" href="{href}" target="_self">
  <article class="dd-home-pick" style="--pick:{accent}">
    <div class="dd-home-pick-label">{label}</div>
    <div class="dd-home-pick-rank">#{rank}</div>
    <img class="dd-home-pick-photo" src="{headshot(player.get('player_id'), 500)}" alt="{esc(player.get('player_name'))}">
    <div class="dd-home-pick-glow"></div>
    <div class="dd-home-pick-body">
      <h3>{esc(player.get('player_name'))}</h3>
      <div class="dd-home-pick-team">{esc(player.get('team_name'))} • {esc(player.get('position') or '—')}</div>
      <div class="dd-home-pick-metrics"><b>{safe_float(player.get('dinger_score')):.1f}</b><span>{percent(player.get('probability'))}</span></div>
      <div class="dd-home-pick-metric-label"><span>DINGER SCORE</span><span>HR PROB</span></div>
      <div class="dd-home-pick-reason"><i></i>{esc(reasons[0])}</div>
      <div class="dd-home-pick-reason alt"><i></i>{esc(reasons[1])}</div>
      <div class="dd-home-pick-pitcher"><strong>VS {esc(pitcher)}</strong><span>{esc(pitcher_detail)}</span></div>
    </div>
  </article>
</a>'''
        )
    return '<div class="dd-home-picks">' + "".join(cards) + "</div>"


def _player_cell(_: Any, row: dict[str, Any]) -> str:
    return (
        f'<div class="dd-home-table-player"><img src="{headshot(row.get("Player ID"), 110)}">'
        f'<div><b>{esc(row.get("Player"))}</b><span>{esc(row.get("Position"))}</span></div></div>'
    )


def _team_cell(_: Any, row: dict[str, Any]) -> str:
    logo = team_logo(row.get("Team ID"))
    return f'<div class="dd-home-table-team"><img src="{logo}"><b>{esc(row.get("Team"))}</b></div>'


def _pitcher_cell(value: Any, row: dict[str, Any]) -> str:
    pitcher = str(value or "Not announced")
    if pitcher == "Not announced":
        return '<div class="dd-pitcher-cell pending"><b>TBD</b><span>Starter pending</span></div>'
    detail = f'{row.get("Pitcher Hand") or "—"}HP • {safe_float(row.get("Pitcher HR9")):.2f} HR/9'
    return f'<div class="dd-pitcher-cell"><b>{esc(pitcher)}</b><span>{esc(detail)}</span></div>'


def _trend_cell(_: Any, row: dict[str, Any]) -> str:
    recent = safe_int(row.get("Last 7"))
    month = safe_int(row.get("Last 30"))
    color = "#35f29a" if recent >= 2 else "#ffd83d" if month >= 5 else "#27c7ff"
    bars = "".join(f'<i style="height:{10 + ((index * 7 + month * 3 + recent * 9) % 26)}px"></i>' for index in range(8))
    return f'<div class="dd-mini-trend" style="--trend:{color}">{bars}</div>'


def _top_rankings_rows(rankings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rank, player in enumerate(rankings[:25], 1):
        rows.append({
            "Rank": rank,
            "Player": player.get("player_name"),
            "Player ID": player.get("player_id"),
            "Position": player.get("position"),
            "Team": player.get("team_name"),
            "Team ID": player.get("team_id"),
            "Dinger Score": safe_float(player.get("dinger_score")),
            "HR Probability": probability_fraction(player.get("probability")) * 100,
            "Fair Odds": player.get("best_odds") if player.get("best_odds") is not None else player.get("fair_odds"),
            "Season HR": safe_int(player.get("season_home_runs")),
            "Last 7": safe_int(player.get("last_7_home_runs")),
            "Last 15": safe_int(player.get("last_15_home_runs")),
            "Last 30": safe_int(player.get("last_30_home_runs")),
            "OPS": safe_float(player.get("season_ops")),
            "Opposing Pitcher": player.get("opposing_pitcher") or "Not announced",
            "Pitcher Hand": player.get("opposing_pitcher_hand") or "—",
            "Pitcher HR9": player.get("pitcher_hr9"),
            "Trend": "",
        })
    return rows


def _slate_strip(board: dict[str, Any], rankings: list[dict[str, Any]]) -> str:
    announced = sum(1 for player in rankings if player.get("pitching_data_available"))
    positive_edges = sum(1 for player in rankings if safe_float(player.get("edge_pct")) > 0)
    hottest = max((safe_int(player.get("last_7_home_runs")) for player in rankings), default=0)
    return f'''
<div class="dd-home-slate-strip">
  <div><i>◉</i><span>FULL MLB SLATE</span><b>{safe_int(board.get('games'))} GAMES</b></div>
  <div><i>⚾</i><span>RANKED HITTERS</span><b>{len(rankings)}</b></div>
  <div><i>✦</i><span>PROBABLE PITCHERS</span><b>{announced} MATCHED</b></div>
  <div><i>↗</i><span>POSITIVE VALUE EDGES</span><b>{positive_edges}</b></div>
  <div><i>🔥</i><span>HOTTEST LAST 7</span><b>{hottest} HR</b></div>
</div>'''


def render(board: dict[str, Any]) -> None:
    rankings = board.get("rankings", []) or []
    if not rankings:
        st.error("No rankings are available. Confirm the API keys and selected slate date, then refresh.")
        return

    date_text = str(board.get("date") or "")
    try:
        date_text = datetime.fromisoformat(date_text).strftime("%B %d, %Y").upper()
    except ValueError:
        pass

    st.markdown(
        f'''
<header class="dd-home-masthead">
  <div class="dd-home-wordmark">DUGGANS<span>DINGERS</span></div>
  <div class="dd-home-tagline"><i></i><b>HOME RUN INTELLIGENCE</b><i></i></div>
  <div class="dd-home-date">▣ &nbsp; {esc(date_text)}</div>
</header>
<div class="dd-home-picks-head"><div><i>⚡</i><span><b>TODAY'S TOP HOME RUN PICKS</b><small>Six highest projections with the matchup reasons behind every ranking</small></span></div><a href="?view=daily-board" target="_self">VIEW ALL TOP PLAYS →</a></div>
''',
        unsafe_allow_html=True,
    )
    st.markdown(_top_pick_cards(rankings), unsafe_allow_html=True)

    st.markdown(
        '<div class="dd-home-table-title"><div><i>♛</i><b>TOP 25 HOME RUN RANKINGS</b><span>Probable pitchers, real power windows, model probability, and live price</span></div><a href="?view=daily-board" target="_self">OPEN FULL BOARD</a></div>',
        unsafe_allow_html=True,
    )
    rows = _top_rankings_rows(rankings)
    columns = [
        Column("Rank", "RANK", formatter=lambda value, row: f'<span class="dd-home-rank rank-{int(value) if int(value) <= 3 else 4}">{int(value)}</span>', width=".42fr", align="center"),
        Column("Player", "PLAYER", formatter=_player_cell, width="1.55fr"),
        Column("Team", "TEAM", formatter=_team_cell, width=".68fr"),
        Column("Opposing Pitcher", "PROBABLE PITCHER", formatter=_pitcher_cell, width="1.45fr"),
        Column("Dinger Score", "DINGER SCORE", progress_max=100, accent="#ff3c45", width="1.05fr"),
        Column("HR Probability", "HR PROB", progress_max=35, accent="#27c7ff", width=".95fr"),
        Column("Fair Odds", "BEST PRICE", formatter=lambda value, row: f'<b style="color:#35f29a">{odds(value)}</b>', width=".72fr", align="center"),
        Column("Season HR", "SEASON HR", width=".62fr", align="center"),
        Column("Last 7", "LAST 7", progress_max=5, accent="#ff4df2", width=".85fr"),
        Column("Last 15", "LAST 15", progress_max=9, accent="#a85cff", width=".85fr"),
        Column("OPS", "OPS", formatter=lambda value, row: f'<b>{safe_float(value):.3f}</b>', width=".58fr", align="center"),
        Column("Trend", "TREND", formatter=_trend_cell, width=".8fr", align="center"),
    ]
    render_neon_table(rows, columns, key="home_top_25", max_height=760)
    st.markdown(_slate_strip(board, rankings), unsafe_allow_html=True)
