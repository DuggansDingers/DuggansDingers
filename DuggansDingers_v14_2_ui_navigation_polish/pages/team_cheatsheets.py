from __future__ import annotations

import math
from urllib.parse import quote

import pandas as pd
import streamlit as st

from components.navigation import go
from components.neon_table import progress_html
from components.ui import esc, headshot, hero, odds, percent, probability_fraction, safe_float, safe_int, section, team_logo
from config import TEAM_COLORS


def _games(board: dict) -> list[dict]:
    rankings = board.get("rankings", []) or []
    meta_map = {str(meta.get("game_id")): meta for meta in board.get("games_meta", []) or []}
    by_game: dict[str, list[dict]] = {}
    for player in rankings:
        key = str(player.get("game_id") or "")
        if key:
            by_game.setdefault(key, []).append(player)

    games: list[dict] = []
    for key, players in by_game.items():
        meta = meta_map.get(key, {})
        away = str(meta.get("away_team_name") or "")
        home = str(meta.get("home_team_name") or "")
        if not away or not home:
            teams = list(dict.fromkeys(str(p.get("team_name") or "") for p in players if p.get("team_name")))
            if len(teams) < 2:
                continue
            away, home = teams[:2]
        players.sort(key=lambda p: safe_float(p.get("dinger_score")), reverse=True)
        top = players[:12]
        at_least_one = 1 - math.prod(1 - probability_fraction(p.get("probability")) for p in top)
        avg_score = sum(safe_float(p.get("dinger_score")) for p in top[:8]) / max(1, len(top[:8]))
        away_id = next((p.get("team_id") for p in players if str(p.get("team_name")) == away and p.get("team_id")), meta.get("away_team_id"))
        home_id = next((p.get("team_id") for p in players if str(p.get("team_name")) == home and p.get("team_id")), meta.get("home_team_id"))
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
    games.sort(key=lambda game: (game["game_hr_probability"], game["avg_score"]), reverse=True)
    return games


def _game_tabs(games: list[dict], active_key: str) -> str:
    cards: list[str] = []
    for rank, game in enumerate(games, 1):
        active = " active" if game["key"] == active_key else ""
        away_logo = f'<img src="{team_logo(game["away_id"])}">' if game.get("away_id") else f'<b>{esc(game["away"])}</b>'
        home_logo = f'<img src="{team_logo(game["home_id"])}">' if game.get("home_id") else f'<b>{esc(game["home"])}</b>'
        cards.append(
            f'<a class="dd-game-chip{active}" href="?view=team-sheets&game={quote(game["key"])}" target="_self">'
            f'<em>#{rank}</em><span>{away_logo}<i>AT</i>{home_logo}</span>'
            f'<b>{esc(game["away"])} @ {esc(game["home"])}</b>'
            f'<small>{game["game_hr_probability"]*100:.1f}% GAME HR CHANCE</small></a>'
        )
    return '<div class="dd-game-chip-row">' + "".join(cards) + "</div>"


def _pitcher_for(team: str, game: dict) -> tuple[str, str, float, float]:
    meta = game.get("meta") or {}
    if team == game.get("away"):
        side = "home"
    else:
        side = "away"
    name = meta.get(f"{side}_probable_pitcher")
    hand = meta.get(f"{side}_probable_pitcher_hand")
    hr9 = safe_float(meta.get(f"{side}_pitcher_hr9"))
    era = safe_float(meta.get(f"{side}_pitcher_era"))
    if not name or name == "Not announced":
        player = next((p for p in game["players"] if str(p.get("team_name")) == team), {})
        name = player.get("opposing_pitcher") or "Not announced"
        hand = player.get("opposing_pitcher_hand") or "—"
        hr9 = safe_float(player.get("pitcher_hr9"))
        era = safe_float(player.get("pitcher_era"))
    return str(name), str(hand or "—"), hr9, era


def _compact_player(player: dict, rank: int, accent: str) -> str:
    score = safe_float(player.get("dinger_score"))
    probability = probability_fraction(player.get("probability")) * 100
    l7 = safe_int(player.get("last_7_home_runs"))
    l15 = safe_int(player.get("last_15_home_runs"))
    price = player.get("best_odds") if player.get("best_odds") is not None else player.get("fair_odds")
    pitcher = str(player.get("opposing_pitcher") or "Not announced")
    pitcher_line = (
        f'{player.get("opposing_pitcher_hand") or "—"}HP • {safe_float(player.get("pitcher_hr9")):.2f} HR/9'
        if player.get("pitching_data_available") else "Starter pending"
    )
    reasons = [str(item) for item in (player.get("projection_reasons") or []) if item]
    reason = reasons[0] if reasons else f"{probability:.1f}% model HR probability"
    return f'''
<a class="dd-team-hitter-link" href="?view=player-intelligence&player={int(player.get('player_id') or 0)}" target="_self">
  <div class="dd-team-hitter" style="--team-accent:{accent}">
    <div class="dd-team-hitter-rank">{rank}</div>
    <img src="{headshot(player.get('player_id'), 160)}" alt="{esc(player.get('player_name'))}">
    <div class="dd-team-hitter-copy">
      <b>{esc(player.get('player_name'))}</b><span>{esc(player.get('position') or '—')} • {esc(player.get('model_tier') or 'MODEL')}</span>
      <small>{esc(reason)}</small>
      <em>VS {esc(pitcher)} • {esc(pitcher_line)}</em>
    </div>
    <div class="dd-team-hitter-bars">
      <div><span>SCORE</span>{progress_html(score, 100, accent, f'{score:.1f}')}</div>
      <div><span>HR PROB</span>{progress_html(probability, 35, '#27c7ff', f'{probability:.1f}%')}</div>
      <div class="recent"><span>L7</span>{progress_html(l7, 5, '#35f29a', f'{l7} HR')}</div>
      <div class="recent"><span>L15</span>{progress_html(l15, 9, '#ff4df2', f'{l15} HR')}</div>
    </div>
    <div class="dd-team-hitter-price"><b>{odds(price)}</b><span>{esc(player.get('best_book') or 'FAIR')}</span></div>
  </div>
</a>'''


def _team_panel(team: str, team_id: int | None, players: list[dict], game: dict) -> str:
    primary, secondary = TEAM_COLORS.get(team, ("#27c7ff", "#ff4df2"))
    pitcher, hand, hr9, era = _pitcher_for(team, game)
    top = sorted(players, key=lambda p: safe_float(p.get("dinger_score")), reverse=True)[:8]
    at_least_one = 1 - math.prod(1 - probability_fraction(p.get("probability")) for p in top[:6])
    avg_score = sum(safe_float(p.get("dinger_score")) for p in top[:6]) / max(1, len(top[:6]))
    logo = f'<img src="{team_logo(team_id)}">' if team_id else ""
    rows = "".join(_compact_player(player, rank, primary) for rank, player in enumerate(top, 1))
    pitcher_detail = "Starter pending" if pitcher == "Not announced" else f"{hand}HP • {hr9:.2f} HR/9 • {era:.2f} ERA"
    return f'''
<section class="dd-side-team-panel" style="--team-a:{primary};--team-b:{secondary}">
  <header class="dd-side-team-head">
    <div>{logo}<span><b>{esc(team)} POWER BOARD</b><small>VS {esc(pitcher)} • {esc(pitcher_detail)}</small></span></div>
    <aside><b>{at_least_one*100:.1f}%</b><span>TOP-6 HR CHANCE</span><b>{avg_score:.1f}</b><span>AVG SCORE</span></aside>
  </header>
  <div class="dd-side-team-list">{rows}</div>
</section>'''


def render(board: dict) -> None:
    games = _games(board)
    hero(
        "MATCHUP <span>TEAM SHEETS</span>",
        "Both clubs share one screen. The highest projected home-run game opens first, and every hitter includes a visible opposing-starter matchup.",
        stats={"Games": len(games), "Date": board.get("date", ""), "Layout": "Side by Side"},
    )
    if not games:
        st.info("No team sheets are available for this slate.")
        return

    requested = str(st.query_params.get("game") or "")
    active = next((game for game in games if game["key"] == requested), games[0])
    st.markdown(_game_tabs(games, active["key"]), unsafe_allow_html=True)

    meta = active.get("meta") or {}
    pitcher_status = "Pitchers matched" if meta.get("home_probable_pitcher") or meta.get("away_probable_pitcher") else "Pitchers pending"
    section(
        f"{active['away']} at {active['home']}",
        "HIGHEST-PROJECTED MATCHUP" if active is games[0] else "SELECTED MATCHUP",
        f"{active['game_hr_probability']*100:.1f}% at least one HR • {pitcher_status}",
    )

    away_players = [p for p in active["players"] if str(p.get("team_name")) == active["away"]]
    home_players = [p for p in active["players"] if str(p.get("team_name")) == active["home"]]
    st.markdown(
        '<div class="dd-side-by-side-teams">'
        + _team_panel(active["away"], active.get("away_id"), away_players, active)
        + _team_panel(active["home"], active.get("home_id"), home_players, active)
        + "</div>",
        unsafe_allow_html=True,
    )

    options = [p for p in active["players"] if p.get("player_id")]
    section("Open a Player", "PLAYER INTELLIGENCE")
    selected = st.selectbox(
        "Player",
        [int(p["player_id"]) for p in options],
        format_func=lambda pid: next(f"{p.get('player_name')} — {p.get('team_name')} vs {p.get('opposing_pitcher') or 'TBD'}" for p in options if int(p["player_id"]) == pid),
    )
    if st.button("Open Player Intelligence", type="primary", use_container_width=True):
        go("Player Intelligence", selected)
        st.rerun()

    export_rows = [{
        "Date": board.get("date"),
        "Game": f"{active['away']} @ {active['home']}",
        "Player": p.get("player_name"),
        "Team": p.get("team_name"),
        "Projected Pitcher": p.get("opposing_pitcher"),
        "Pitcher Hand": p.get("opposing_pitcher_hand"),
        "Pitcher HR9": p.get("pitcher_hr9"),
        "Pitcher ERA": p.get("pitcher_era"),
        "Dinger Score": p.get("dinger_score"),
        "HR Probability": percent(p.get("probability")),
        "Last 7 HR": safe_int(p.get("last_7_home_runs")),
        "Last 15 HR": safe_int(p.get("last_15_home_runs")),
        "Best Book": p.get("best_book"),
        "Best Odds": p.get("best_odds"),
    } for p in active["players"]]
    export = pd.DataFrame(export_rows)
    st.download_button(
        "Download Selected Matchup CSV",
        export.to_csv(index=False).encode("utf-8"),
        f"duggansdingers_matchup_{active['away']}_{active['home']}_{board.get('date','today')}.csv",
        "text/csv",
        use_container_width=True,
    )
