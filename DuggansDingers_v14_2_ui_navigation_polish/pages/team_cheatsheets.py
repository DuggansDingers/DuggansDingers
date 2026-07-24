from __future__ import annotations

import math
from html import escape
from urllib.parse import quote

import pandas as pd
import streamlit as st

from components.navigation import go
from components.neon_table import progress_html
from components.ui import (
    esc,
    headshot,
    hero,
    odds,
    percent,
    probability_fraction,
    safe_float,
    safe_int,
    section,
    team_logo,
)
from config import TEAM_COLORS


def _games(board: dict) -> list[dict]:
    rankings = board.get("rankings", []) or []
    meta_map = {str(meta.get("game_id")): meta for meta in board.get("games_meta", []) or []}
    by_game: dict[str, list[dict]] = {}
    for player in rankings:
        by_game.setdefault(str(player.get("game_id") or ""), []).append(player)

    games: list[dict] = []
    for key, players in by_game.items():
        if not key:
            continue
        meta = meta_map.get(key, {})
        away = str(meta.get("away_team_name") or "")
        home = str(meta.get("home_team_name") or "")
        if not away or not home:
            teams = list(dict.fromkeys(str(p.get("team_name") or "") for p in players if p.get("team_name")))
            if len(teams) < 2:
                continue
            away, home = teams[:2]
        players.sort(key=lambda p: safe_float(p.get("dinger_score")), reverse=True)
        top = players[:10]
        at_least_one = 1 - math.prod(1 - probability_fraction(p.get("probability")) for p in top)
        avg_score = sum(safe_float(p.get("dinger_score")) for p in top[:6]) / max(1, len(top[:6]))
        away_id = next((p.get("team_id") for p in players if str(p.get("team_name")) == away and p.get("team_id")), None)
        home_id = next((p.get("team_id") for p in players if str(p.get("team_name")) == home and p.get("team_id")), None)
        games.append({
            "key": key,
            "away": away,
            "home": home,
            "away_id": away_id,
            "home_id": home_id,
            "players": players,
            "meta": meta,
            "game_hr_probability": at_least_one,
            "avg_score": avg_score,
            "top_score": safe_float(players[0].get("dinger_score")) if players else 0,
        })
    games.sort(key=lambda g: (g["game_hr_probability"], g["avg_score"]), reverse=True)
    return games


def _game_tabs(games: list[dict], active_key: str) -> str:
    cards = []
    for rank, game in enumerate(games, 1):
        active = " active" if game["key"] == active_key else ""
        away_logo = f'<img src="{team_logo(game["away_id"])}">' if game.get("away_id") else f'<b>{esc(game["away"])}</b>'
        home_logo = f'<img src="{team_logo(game["home_id"])}">' if game.get("home_id") else f'<b>{esc(game["home"])}</b>'
        cards.append(
            f'<a class="dd-game-tab{active}" href="?view=team-sheets&game={quote(game["key"])}" target="_self">'
            f'<span class="dd-game-tab-rank">#{rank}</span><div>{away_logo}<i>vs</i>{home_logo}</div>'
            f'<b>{esc(game["away"])} @ {esc(game["home"])}</b>'
            f'<small>{game["game_hr_probability"]*100:.1f}% game HR chance</small></a>'
        )
    return '<div class="dd-game-tabs">' + "".join(cards) + "</div>"


def _pitcher_for(team: str, game: dict) -> tuple[str, str]:
    meta = game.get("meta") or {}
    if team == game.get("away"):
        name = meta.get("home_probable_pitcher")
        hand = meta.get("home_probable_pitcher_hand")
    else:
        name = meta.get("away_probable_pitcher")
        hand = meta.get("away_probable_pitcher_hand")
    if not name or name == "Not announced":
        player = next((p for p in game["players"] if str(p.get("team_name")) == team), {})
        name = player.get("opposing_pitcher") or "Not announced"
        hand = player.get("opposing_pitcher_hand") or "—"
    return str(name), str(hand or "—")


def _player_row(player: dict, rank: int, accent: str) -> str:
    score = safe_float(player.get("dinger_score"))
    probability = probability_fraction(player.get("probability")) * 100
    l7 = safe_int(player.get("last_7_home_runs"))
    l15 = safe_int(player.get("last_15_home_runs"))
    pitcher = str(player.get("opposing_pitcher") or "Not announced")
    pitcher_stats = (
        f"{player.get('opposing_pitcher_hand','—')}HP • {safe_float(player.get('pitcher_hr9')):.2f} HR/9"
        if player.get("pitching_data_available") else "Starter data pending"
    )
    reasons = player.get("projection_reasons") or []
    reason = str(reasons[0]) if reasons else f"{probability:.1f}% model HR probability"
    return f'''
<div class="dd-matchup-player-row" style="--team-accent:{accent}">
  <div class="dd-matchup-rank">{rank}</div>
  <div class="dd-matchup-player">
    <img src="{headshot(player.get('player_id'), 150)}"><div><b>{esc(player.get('player_name'))}</b><span>{esc(player.get('position','—'))} • {esc(player.get('model_tier','Model'))}</span><small>{esc(reason)}</small></div>
  </div>
  <div class="dd-matchup-pitcher"><b>vs {esc(pitcher)}</b><span>{esc(pitcher_stats)}</span></div>
  <div>{progress_html(score, 100, accent, f'{score:.1f}')}</div>
  <div>{progress_html(probability, 35, '#27c7ff', f'{probability:.1f}%')}</div>
  <div>{progress_html(l7, 5, '#36f29b', f'{l7} HR')}</div>
  <div>{progress_html(l15, 8, '#ff4df2', f'{l15} HR')}</div>
  <div class="dd-matchup-price"><b>{odds(player.get('best_odds')) if player.get('best_odds') is not None else odds(player.get('fair_odds'))}</b><span>{esc(player.get('best_book') or 'Fair')}</span></div>
</div>'''


def _team_panel(team: str, team_id: int | None, players: list[dict], game: dict) -> str:
    primary, secondary = TEAM_COLORS.get(team, ("#25b6ff", "#ff4df2"))
    pitcher, hand = _pitcher_for(team, game)
    top = sorted(players, key=lambda p: safe_float(p.get("dinger_score")), reverse=True)[:8]
    at_least_one = 1 - math.prod(1 - probability_fraction(p.get("probability")) for p in top[:6])
    avg_score = sum(safe_float(p.get("dinger_score")) for p in top[:6]) / max(1, len(top[:6]))
    rows = "".join(_player_row(player, rank, primary) for rank, player in enumerate(top, 1))
    logo = f'<img src="{team_logo(team_id)}">' if team_id else ""
    return f'''
<section class="dd-matchup-team" style="--team-a:{primary};--team-b:{secondary}">
  <div class="dd-matchup-team-head">
    <div class="dd-matchup-team-brand">{logo}<div><b>{esc(team)} POWER BOARD</b><span>Opposing starter: {esc(pitcher)} • {esc(hand)}HP</span></div></div>
    <div class="dd-team-summary"><div><b>{at_least_one*100:.1f}%</b><span>Top-6 HR chance</span></div><div><b>{avg_score:.1f}</b><span>Avg model score</span></div></div>
  </div>
  <div class="dd-matchup-columns"><span>#</span><span>Hitter / Reason</span><span>Pitcher Matchup</span><span>Dinger Score</span><span>HR Probability</span><span>Last 7</span><span>Last 15</span><span>Best Price</span></div>
  {rows}
</section>'''


def render(board: dict) -> None:
    games = _games(board)
    hero(
        "MATCHUP <span>TEAM SHEETS</span>",
        "Both clubs live on one sheet. The highest projected home-run game opens first; use the glowing matchup icons to switch games.",
        stats={"Games": len(games), "Date": board.get("date", ""), "Default": "Highest HR Game"},
    )
    if not games:
        st.info("No team sheets are available for this slate.")
        return

    requested = str(st.query_params.get("game") or "")
    active = next((game for game in games if game["key"] == requested), games[0])
    st.markdown(_game_tabs(games, active["key"]), unsafe_allow_html=True)

    meta = active.get("meta") or {}
    weather = str(meta.get("weather_grade") or "—")
    source = str(meta.get("weather_source") or "Weather pending")
    section(
        f"{active['away']} at {active['home']}",
        "HIGHEST-PROJECTED MATCHUP" if active is games[0] else "SELECTED MATCHUP",
        f"{active['game_hr_probability']*100:.1f}% at least one HR • Weather {weather} • {source}",
    )

    away_players = [p for p in active["players"] if str(p.get("team_name")) == active["away"]]
    home_players = [p for p in active["players"] if str(p.get("team_name")) == active["home"]]
    st.markdown(
        '<div class="dd-matchup-sheet-grid">'
        + _team_panel(active["away"], active.get("away_id"), away_players, active)
        + _team_panel(active["home"], active.get("home_id"), home_players, active)
        + "</div>",
        unsafe_allow_html=True,
    )

    section("Open a Player", "PLAYER INTELLIGENCE")
    options = [p for p in active["players"] if p.get("player_id")]
    selected = st.selectbox(
        "Player",
        [int(p["player_id"]) for p in options],
        format_func=lambda pid: next(f"{p.get('player_name')} — {p.get('team_name')}" for p in options if int(p["player_id"]) == pid),
    )
    if st.button("Open Player Intelligence", type="primary", use_container_width=True):
        go("Player Intelligence", selected)
        st.rerun()

    export_rows = []
    for player in active["players"]:
        export_rows.append({
            "Date": board.get("date"), "Game": f"{active['away']} @ {active['home']}",
            "Player": player.get("player_name"), "Team": player.get("team_name"),
            "Opponent": player.get("opponent"), "Projected Pitcher": player.get("opposing_pitcher"),
            "Pitcher Hand": player.get("opposing_pitcher_hand"), "Pitcher HR9": player.get("pitcher_hr9"),
            "Dinger Score": player.get("dinger_score"), "HR Probability": percent(player.get("probability")),
            "Last 7 HR": safe_int(player.get("last_7_home_runs")), "Last 15 HR": safe_int(player.get("last_15_home_runs")),
            "Best Book": player.get("best_book"), "Best Odds": player.get("best_odds"),
        })
    export = pd.DataFrame(export_rows)
    st.download_button(
        "Download Selected Matchup CSV",
        export.to_csv(index=False).encode("utf-8"),
        f"duggansdingers_matchup_{active['away']}_{active['home']}_{board.get('date','today')}.csv",
        "text/csv",
        use_container_width=True,
    )
