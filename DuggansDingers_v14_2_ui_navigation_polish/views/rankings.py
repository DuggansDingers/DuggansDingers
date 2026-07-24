from __future__ import annotations

import pandas as pd
import streamlit as st

from components.neon_table import Column, render_neon_table
from components.ui import (
    esc,
    headshot,
    odds,
    probability_fraction,
    safe_float,
    safe_int,
    score_color,
    team_logo,
)


def _metric_label(player: dict) -> str:
    impact = safe_float(player.get("weather_impact"))
    if player.get("weather_available"):
        return f'{player.get("weather_grade") or "—"} • {impact:+.1f} WEATHER'
    return "WEATHER PENDING"


def _assign_labels(players: list[dict]) -> list[str]:
    count = len(players)
    if not count:
        return []
    labels = ["POWER PROFILE"] * count
    unused = set(range(count))

    def claim(index: int | None, label: str) -> None:
        if index is not None and index in unused:
            labels[index] = label
            unused.remove(index)

    claim(0, "TOP PICK")

    def best(metric, predicate=lambda p: True) -> int | None:
        candidates = [(metric(player), index) for index, player in enumerate(players) if index in unused and predicate(player)]
        return max(candidates, default=(None, None))[1]

    claim(best(lambda p: probability_fraction(p.get("probability"))), "HIGHEST HR PROB")
    claim(best(lambda p: safe_int(p.get("last_7_home_runs")) * 10 + safe_float(p.get("last_7_hr_rate"))), "HOTTEST BAT")
    claim(best(lambda p: safe_float(p.get("pitcher_vulnerability_signal")), lambda p: bool(p.get("pitching_data_available"))), "POWER MATCHUP")
    claim(best(lambda p: safe_float(p.get("weather_impact")), lambda p: bool(p.get("weather_available"))), "BEST WEATHER")
    claim(best(lambda p: safe_float(p.get("edge_pct")), lambda p: p.get("edge_pct") is not None), "BEST VALUE")

    fallback = ["MATCHUP EDGE", "HOT FORM", "PARK BOOST", "VALUE UPSIDE", "POWER PROFILE"]
    for position, index in enumerate(sorted(unused)):
        labels[index] = fallback[position % len(fallback)]
    return labels


def _pitcher_details(player: dict) -> tuple[str, str]:
    pitcher = (
        player.get("opposing_pitcher")
        or player.get("projected_pitcher")
        or player.get("probable_pitcher")
        or player.get("pitcher_name")
        or "Awaiting announcement"
    )
    if pitcher in {"Not announced", "TBD", "None", ""}:
        pitcher = "Awaiting announcement"
    if player.get("pitching_data_available"):
        detail = (
            f'{player.get("opposing_pitcher_hand") or "—"}HP • '
            f'{safe_float(player.get("pitcher_hr9")):.2f} HR/9 • '
            f'{safe_float(player.get("pitcher_era")):.2f} ERA'
        )
    else:
        status = str(player.get("probable_pitcher_status") or "Starter data pending").replace("_", " ")
        detail = status.title()
    return str(pitcher), detail


def _compact_card(player: dict, rank: int, label: str) -> str:
    score = safe_float(player.get("dinger_score"))
    accent = score_color(score)
    pitcher, pitcher_line = _pitcher_details(player)
    player_id = int(player.get("player_id") or 0)
    href = f"?view=player-intelligence&player={player_id}" if player_id else "?view=daily-board"
    reasons = [str(value) for value in (player.get("projection_reasons") or []) if value][:2]
    while len(reasons) < 2:
        reasons.append(f"{safe_int(player.get('last_30_home_runs'))} HR in the last 30 games")
    probability = probability_fraction(player.get("probability")) * 100
    weather_class = " live" if player.get("weather_available") else ""

    return f'''
<a class="dd-rank-card-link" href="{href}" target="_self">
<article class="dd-rank-card dd20-rank-card" style="--card-accent:{accent}">
  <div class="dd20-rank-top"><span class="dd-rank-card-number">{rank}</span><b class="dd-rank-card-label">{esc(label)}</b></div>
  <div class="dd20-rank-player">
    <img class="dd-rank-card-photo" src="{headshot(player.get('player_id'), 300)}" alt="{esc(player.get('player_name'))}">
    <div class="dd20-rank-identity">
      <h3>{esc(player.get('player_name'))}</h3>
      <div class="dd-rank-card-team"><img src="{team_logo(player.get('team_id'))}">{esc(player.get('team_name'))} • {esc(player.get('position') or '—')}</div>
    </div>
  </div>
  <div class="dd-rank-card-numbers">
    <b>{score:.1f}<small>DINGER SCORE</small></b>
    <b>{probability:.1f}%<small>HR PROBABILITY</small></b>
  </div>
  <div class="dd20-weather-badge{weather_class}"><span>WEATHER</span><b>{esc(_metric_label(player))}</b></div>
  <div class="dd-rank-card-pitcher">
    <span>PROJECTED OPPOSING STARTER</span><strong>{esc(pitcher)}</strong><small>{esc(pitcher_line)}</small>
  </div>
  <ul><li>{esc(reasons[0])}</li><li>{esc(reasons[1])}</li></ul>
</article>
</a>'''


def _player_cell(_: object, row: dict) -> str:
    return (
        f'<a class="dd-rank-table-player dd20-profile-link" href="?view=player-intelligence&player={int(row.get("Player ID") or 0)}" target="_self">'
        f'<img src="{headshot(row.get("Player ID"), 100)}">'
        f'<div><b>{esc(row.get("Player"))}</b><span>{esc(row.get("Position"))}</span></div></a>'
    )


def _team_cell(_: object, row: dict) -> str:
    return f'<div class="dd-rank-table-team"><img src="{team_logo(row.get("Team ID"))}"><b>{esc(row.get("Team"))}</b></div>'


def _pitcher_cell(value: object, row: dict) -> str:
    pitcher = str(value or "Awaiting announcement")
    if pitcher in {"Not announced", "TBD", "None", ""}:
        pitcher = "Awaiting announcement"
    if row.get("Pitching Available"):
        detail = f'{row.get("Pitcher Hand") or "—"}HP • {safe_float(row.get("Pitcher HR9")):.2f} HR/9 • {safe_float(row.get("Pitcher ERA")):.2f} ERA'
    else:
        detail = str(row.get("Pitcher Status") or "Starter data pending").replace("_", " ").title()
    return f'<div class="dd-rank-pitcher"><b>{esc(pitcher)}</b><span>{esc(detail)}</span></div>'


def render(board: dict) -> None:
    rankings = board.get("rankings", []) or []
    if not rankings:
        st.info("No rankings are available.")
        return

    st.markdown(
        f'''
<section class="dd-template-hero compact">
  <div><span>MLB HOME RUN INTELLIGENCE</span><h1>PLAYER <em>RANKINGS</em></h1><p>Live home-run probability, projected opposing starters, weather, real power history, and sportsbook value.</p></div>
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
    sort_by = f5.selectbox("Sort by", ["Dinger Score", "HR Probability", "Weather Impact", "Season HR", "Last 7 HR", "OPS"])

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
        "Weather Impact": lambda p: safe_float(p.get("weather_impact")),
        "Season HR": lambda p: safe_int(p.get("season_home_runs")),
        "Last 7 HR": lambda p: safe_int(p.get("last_7_home_runs")),
        "OPS": lambda p: safe_float(p.get("season_ops")),
    }[sort_by]
    filtered.sort(key=sort_key, reverse=True)

    card_count = min(25, len(filtered))
    st.markdown(f'<div class="dd-board-kicker"><b>TOP {card_count} POWER CARDS</b><span>Five compact cards per row • click any player image or card for the complete profile</span></div>', unsafe_allow_html=True)
    visible = filtered[:card_count]
    labels = _assign_labels(visible)
    cards = ''.join(_compact_card(player, index + 1, labels[index]) for index, player in enumerate(visible))
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
            "Opposing Pitcher": player.get("opposing_pitcher") or "Awaiting announcement",
            "Pitcher Hand": player.get("opposing_pitcher_hand") or "—",
            "Pitcher HR9": player.get("pitcher_hr9"),
            "Pitcher ERA": player.get("pitcher_era"),
            "Pitcher Status": player.get("probable_pitcher_status"),
            "Pitching Available": bool(player.get("pitching_data_available")),
            "Dinger Score": safe_float(player.get("dinger_score")),
            "HR Probability": probability_fraction(player.get("probability")) * 100,
            "Weather": safe_float(player.get("weather_impact")),
            "Best Odds": player.get("best_odds") if player.get("best_odds") is not None else player.get("fair_odds"),
            "Season HR": safe_int(player.get("season_home_runs")),
            "Last 7": safe_int(player.get("last_7_home_runs")),
            "Last 15": safe_int(player.get("last_15_home_runs")),
            "OPS": safe_float(player.get("season_ops")),
        })

    st.markdown('<div class="dd-board-kicker"><b>FULL PLAYER BOARD</b><span>Projected opposing starter and weather impact are displayed beside every hitter</span></div>', unsafe_allow_html=True)
    columns = [
        Column("Rank", "RANK", width=".42fr", align="center"),
        Column("Player", "PLAYER", formatter=_player_cell, width="1.45fr"),
        Column("Team", "TEAM", formatter=_team_cell, width=".65fr"),
        Column("Opposing Pitcher", "PROJECTED STARTER", formatter=_pitcher_cell, width="1.55fr"),
        Column("Dinger Score", "DINGER SCORE", progress_max=100, accent="#ff4d6d", width=".95fr"),
        Column("HR Probability", "HR PROB", progress_max=35, accent="#27c7ff", width=".95fr"),
        Column("Weather", "WEATHER", formatter=lambda value, row: f'<b class="dd20-weather-table {("good" if safe_float(value) >= 2 else "bad" if safe_float(value) < -2 else "neutral")}">{safe_float(value):+.1f}</b>', width=".8fr", align="center"),
        Column("Best Odds", "BEST PRICE", formatter=lambda value, row: f'<b style="color:#43f59d">{odds(value)}</b>', width=".7fr", align="center"),
        Column("Season HR", "SEASON HR", width=".62fr", align="center"),
        Column("Last 7", "LAST 7", progress_max=5, accent="#ff6a32", width=".78fr"),
        Column("Last 15", "LAST 15", progress_max=9, accent="#a855f7", width=".78fr"),
        Column("OPS", "OPS", formatter=lambda value, row: f'<b>{safe_float(value):.3f}</b>', width=".58fr", align="center"),
    ]
    render_neon_table(rows, columns, key="v20_rankings", max_height=760)

    export = pd.DataFrame(rows)
    st.download_button(
        "Export filtered rankings CSV",
        export.to_csv(index=False).encode("utf-8"),
        f"duggansdingers_rankings_{board.get('date','today')}.csv",
        "text/csv",
        use_container_width=True,
    )
