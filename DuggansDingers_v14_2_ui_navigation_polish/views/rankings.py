from __future__ import annotations

import pandas as pd
import streamlit as st

from components.neon_table import Column, render_neon_table
from components.ui import esc, headshot, odds, percent, probability_fraction, safe_float, safe_int, score_color, team_logo


RANK_CARD_LABELS = ["TOP PICK", "POWER MATCHUP", "HOTTEST BAT", "HIGHEST HR PROB", "BEST BALLPARK"]


def _compact_card(player: dict, rank: int) -> str:
    score = safe_float(player.get("dinger_score"))
    accent = score_color(score)
    pitcher = str(player.get("opposing_pitcher") or "Not announced")
    pitcher_line = (
        f'{player.get("opposing_pitcher_hand") or "—"}HP • {safe_float(player.get("pitcher_hr9")):.2f} HR/9'
        if player.get("pitching_data_available") else "Starter pending"
    )
    player_id = int(player.get("player_id") or 0)
    href = f"?view=player-intelligence&player={player_id}" if player_id else "?view=daily-board"
    reasons = [str(value) for value in (player.get("projection_reasons") or []) if value][:2]
    while len(reasons) < 2:
        reasons.append(f"{safe_int(player.get('last_7_home_runs'))} HR in the last 7 games")
    label = RANK_CARD_LABELS[min(rank - 1, len(RANK_CARD_LABELS) - 1)]
    return f'''
<a class="dd-rank-card-link" href="{href}" target="_self">
<article class="dd-rank-card" style="--card-accent:{accent}">
  <span class="dd-rank-card-number">{rank}</span>
  <div class="dd-rank-card-label">{label}</div>
  <img class="dd-rank-card-photo" src="{headshot(player.get('player_id'), 300)}" alt="{esc(player.get('player_name'))}">
  <div class="dd-rank-card-copy">
    <h3>{esc(player.get('player_name'))}</h3>
    <div class="dd-rank-card-team"><img src="{team_logo(player.get('team_id'))}">{esc(player.get('team_name'))} • {esc(player.get('position') or '—')}</div>
    <div class="dd-rank-card-numbers"><b>{score:.1f}<small>DINGER SCORE</small></b><b>{percent(player.get('probability'))}<small>HR PROBABILITY</small></b></div>
    <div class="dd-rank-card-pitcher"><span>PROBABLE PITCHER</span><strong>{esc(pitcher)}</strong><small>{esc(pitcher_line)}</small></div>
    <ul><li>{esc(reasons[0])}</li><li>{esc(reasons[1])}</li></ul>
  </div>
</article>
</a>'''


def _player_cell(_: object, row: dict) -> str:
    return (
        f'<div class="dd-rank-table-player"><img src="{headshot(row.get("Player ID"), 100)}">'
        f'<div><b>{esc(row.get("Player"))}</b><span>{esc(row.get("Position"))}</span></div></div>'
    )


def _team_cell(_: object, row: dict) -> str:
    return f'<div class="dd-rank-table-team"><img src="{team_logo(row.get("Team ID"))}"><b>{esc(row.get("Team"))}</b></div>'


def _pitcher_cell(value: object, row: dict) -> str:
    pitcher = str(value or "Not announced")
    detail = "Starter pending"
    if pitcher != "Not announced":
        detail = f'{row.get("Pitcher Hand") or "—"}HP • {safe_float(row.get("Pitcher HR9")):.2f} HR/9 • {safe_float(row.get("Pitcher ERA")):.2f} ERA'
    return f'<div class="dd-rank-pitcher"><b>{esc(pitcher)}</b><span>{esc(detail)}</span></div>'


def render(board: dict) -> None:
    rankings = board.get("rankings", []) or []
    if not rankings:
        st.info("No rankings are available.")
        return

    st.markdown(
        f'''
<section class="dd-template-hero compact">
  <div><span>MLB HOME RUN INTELLIGENCE</span><h1>PLAYER <em>RANKINGS</em></h1><p>Live home-run probability, probable-pitcher matchup, real power history, and sportsbook value.</p></div>
  <aside><div><span>PLAYERS RANKED</span><b>{len(rankings)}</b></div><div><span>TEAMS</span><b>{len(board.get('teams', []))}</b></div><div><span>GAMES</span><b>{safe_int(board.get('games'))}</b></div></aside>
</section>''',
        unsafe_allow_html=True,
    )

    teams = sorted({str(player.get("team_name", "N/A")) for player in rankings})
    f1, f2, f3, f4, f5 = st.columns([1.7, 1.15, .9, 1.05, 1.1])
    query = f1.text_input("Search player", placeholder="Search by player name...")
    selected_teams = f2.multiselect("Team", teams, placeholder="All teams")
    min_score = f3.slider("Min score", 0, 100, 0)
    hand = f4.selectbox("Pitcher hand", ["All", "R", "L"])
    sort_by = f5.selectbox("Sort by", ["Dinger Score", "HR Probability", "Season HR", "Last 7 HR", "OPS"])

    filtered: list[dict] = []
    for player in rankings:
        if query and query.lower() not in str(player.get("player_name", "")).lower():
            continue
        if selected_teams and player.get("team_name") not in selected_teams:
            continue
        if safe_float(player.get("dinger_score")) < min_score:
            continue
        if hand != "All" and str(player.get("opposing_pitcher_hand") or "").upper() != hand:
            continue
        filtered.append(player)

    sort_key = {
        "Dinger Score": lambda p: safe_float(p.get("dinger_score")),
        "HR Probability": lambda p: probability_fraction(p.get("probability")),
        "Season HR": lambda p: safe_int(p.get("season_home_runs")),
        "Last 7 HR": lambda p: safe_int(p.get("last_7_home_runs")),
        "OPS": lambda p: safe_float(p.get("season_ops")),
    }[sort_by]
    filtered.sort(key=sort_key, reverse=True)

    card_count = min(25, len(filtered))
    st.markdown(f'<div class="dd-board-kicker"><b>TOP {card_count} POWER CARDS</b><span>Five compact player cards per row • click any player for the full profile</span></div>', unsafe_allow_html=True)
    visible = filtered[:card_count]
    cards = ''.join(_compact_card(player, index + 1) for index, player in enumerate(visible))
    st.markdown(f'<div class="dd-rank-card-grid">{cards}</div>', unsafe_allow_html=True)

    rows = []
    for player in filtered:
        rows.append({
            "Rank": player.get("overall_rank"),
            "Player": player.get("player_name"),
            "Player ID": player.get("player_id"),
            "Position": player.get("position"),
            "Team": player.get("team_name"),
            "Team ID": player.get("team_id"),
            "Opposing Pitcher": player.get("opposing_pitcher") or "Not announced",
            "Pitcher Hand": player.get("opposing_pitcher_hand") or "—",
            "Pitcher HR9": player.get("pitcher_hr9"),
            "Pitcher ERA": player.get("pitcher_era"),
            "Dinger Score": safe_float(player.get("dinger_score")),
            "HR Probability": probability_fraction(player.get("probability")) * 100,
            "Best Odds": player.get("best_odds") if player.get("best_odds") is not None else player.get("fair_odds"),
            "Season HR": safe_int(player.get("season_home_runs")),
            "Last 7": safe_int(player.get("last_7_home_runs")),
            "Last 15": safe_int(player.get("last_15_home_runs")),
            "OPS": safe_float(player.get("season_ops")),
        })

    st.markdown('<div class="dd-board-kicker"><b>FULL PLAYER BOARD</b><span>Probable pitchers are displayed beside every hitter</span></div>', unsafe_allow_html=True)
    columns = [
        Column("Rank", "RANK", width=".42fr", align="center"),
        Column("Player", "PLAYER", formatter=_player_cell, width="1.5fr"),
        Column("Team", "TEAM", formatter=_team_cell, width=".72fr"),
        Column("Opposing Pitcher", "PROBABLE PITCHER", formatter=_pitcher_cell, width="1.6fr"),
        Column("Dinger Score", "DINGER SCORE", progress_max=100, accent="#ff4d6d", width="1fr"),
        Column("HR Probability", "HR PROB", progress_max=35, accent="#27c7ff", width="1fr"),
        Column("Best Odds", "BEST PRICE", formatter=lambda value, row: f'<b style="color:#43f59d">{odds(value)}</b>', width=".75fr", align="center"),
        Column("Season HR", "SEASON HR", width=".7fr", align="center"),
        Column("Last 7", "LAST 7", progress_max=5, accent="#ff6a32", width=".85fr"),
        Column("Last 15", "LAST 15", progress_max=9, accent="#a855f7", width=".85fr"),
        Column("OPS", "OPS", formatter=lambda value, row: f'<b>{safe_float(value):.3f}</b>', width=".62fr", align="center"),
    ]
    render_neon_table(rows, columns, key="v17_rankings", max_height=720)

    export = pd.DataFrame(rows)
    st.download_button(
        "Export filtered rankings CSV",
        export.to_csv(index=False).encode("utf-8"),
        f"duggansdingers_rankings_{board.get('date','today')}.csv",
        "text/csv",
        use_container_width=True,
    )
