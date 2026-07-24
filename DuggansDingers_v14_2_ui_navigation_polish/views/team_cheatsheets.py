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




def _form_strip(player: dict, games: int = 15) -> str:
    series = list(player.get("recent_game_hr_series") or [])[-games:]
    dates = list(player.get("recent_game_dates") or [])[-len(series):]
    if len(series) < games:
        pad = games - len(series)
        series = [None] * pad + series
        dates = [""] * pad + dates
    cells: list[str] = []
    for index, value in enumerate(series):
        date_label = str(dates[index] or "")[-5:]
        if value is None:
            cells.append(f'<i class="dnp"><span>—</span><small>{esc(date_label)}</small></i>')
            continue
        home_runs = safe_int(value)
        if home_runs <= 0:
            cells.append(f'<i class="zero"><span>•</span><small>{esc(date_label)}</small></i>')
        elif home_runs == 1:
            cells.append(f'<i class="one"><span>🔥</span><small>{esc(date_label)}</small></i>')
        else:
            cells.append(f'<i class="multi"><span>{home_runs}🔥</span><small>{esc(date_label)}</small></i>')
    return '<div class="dd-form-strip">' + ''.join(cells) + '</div>'

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
      <div class="dd-form-wrap"><span>LAST 15 GAME FORM • L7 {l7} HR • L15 {l15} HR</span>{_form_strip(player, 15)}</div>
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

    st.markdown('''<div class="dd-form-guide"><b>FORM GUIDE</b><span><i class="one">🔥</i> Home run</span><span><i class="multi">2🔥</i> Multi-HR game</span><span><i class="zero">•</i> No home run</span><span><i class="dnp">—</i> No data / did not play</span></div>''', unsafe_allow_html=True)

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

# ===== V18 PIXEL-TEMPLATE TEAM SHEETS =====

def _v18_team_form(players: list[dict], games: int) -> str:
    top = players[:6]
    width = games
    aggregate: list[int | None] = []
    for offset in range(width):
        values: list[int] = []
        for player in top:
            series = list(player.get("recent_game_hr_series") or [])[-width:]
            if len(series) < width:
                series = [None] * (width - len(series)) + series
            value = series[offset] if offset < len(series) else None
            if value is not None:
                values.append(safe_int(value))
        aggregate.append(sum(values) if values else None)
    cells: list[str] = []
    for value in aggregate:
        if value is None:
            cells.append('<i class="dnp"><span>—</span></i>')
        elif value <= 0:
            cells.append('<i class="zero"><span></span></i>')
        elif value == 1:
            cells.append('<i class="one"><span>🔥</span></i>')
        else:
            cells.append(f'<i class="multi"><span>{value}</span></i>')
    return '<div class="dd-v18-team-form">' + ''.join(cells) + '</div>'


def _v18_hitter_list(players: list[dict], accent: str) -> str:
    rows: list[str] = []
    for rank, player in enumerate(players[:6], 1):
        score = safe_float(player.get("dinger_score"))
        flames = max(1, min(4, int(round(score / 25))))
        rows.append(
            f'''<a href="?view=player-intelligence&player={int(player.get('player_id') or 0)}" target="_self" class="dd-v18-team-hitter">
            <em>{rank}</em><img src="{headshot(player.get('player_id'), 120)}"><b>{esc(player.get('player_name'))}<small>{esc(player.get('position') or '—')}</small></b><strong style="color:{accent}">{score:.1f}</strong><span>{'🔥' * flames}</span></a>'''
        )
    return ''.join(rows)


def _v18_matchup_notes(players: list[dict], pitcher: str, hand: str, hr9: float) -> str:
    notes: list[str] = []
    if pitcher and pitcher != "Not announced":
        notes.append(f"Projected matchup vs {pitcher} ({hand}HP, {hr9:.2f} HR/9)")
    top = players[0] if players else {}
    for reason in top.get("projection_reasons") or []:
        if reason and str(reason) not in notes:
            notes.append(str(reason))
    while len(notes) < 3:
        notes.append("Model combines live probability, recent power, and opposing-pitcher contact risk")
    icons = ["⚡", "⚾", "🏆"]
    return ''.join(f'<li><i>{icons[index]}</i>{esc(note)}</li>' for index, note in enumerate(notes[:3]))


def _v18_team_panel(team: str, team_id: int | None, players: list[dict], game: dict, side: str) -> str:
    primary, secondary = TEAM_COLORS.get(team, ("#27c7ff", "#ff4df2"))
    pitcher, hand, hr9, era = _pitcher_for(team, game)
    top = sorted(players, key=lambda p: safe_float(p.get("dinger_score")), reverse=True)[:8]
    leader = top[0] if top else {}
    score = safe_float(leader.get("dinger_score"))
    probability = probability_fraction(leader.get("probability")) * 100
    price = leader.get("best_odds") if leader.get("best_odds") is not None else leader.get("fair_odds")
    book = str(leader.get("best_book") or "FAIR PRICE")
    logo = f'<img src="{team_logo(team_id)}">' if team_id else ""
    pitcher_detail = "Starter pending" if pitcher == "Not announced" else f"{hand}HP • {hr9:.2f} HR/9 • {era:.2f} ERA"
    return f'''
<section class="dd-v18-team-sheet" style="--team-primary:{primary};--team-secondary:{secondary}">
  <header class="dd-v18-team-brand">
    <div class="club">{logo}<span><small>{esc(side)}</small><b>{esc(team)}</b><em>POWER BOARD</em></span></div>
    <div class="score"><span>DINGER SCORE</span><b>{score:.1f}</b><i></i><span>HR PROBABILITY</span><strong>{probability:.1f}%</strong></div>
  </header>
  <div class="dd-v18-team-pitcher"><div class="avatar">⚾</div><span><small>PROBABLE PITCHER</small><b>{esc(pitcher)}</b><em>{esc(pitcher_detail)}</em></span></div>
  <div class="dd-v18-team-body">
    <div class="dd-v18-team-top"><header>TOP 6 PROJECTED HR HITTERS</header>{_v18_hitter_list(top, primary)}</div>
    <div class="dd-v18-team-form-panel"><header>LAST 7 GAMES</header>{_v18_team_form(top, 7)}<header>LAST 15 GAMES</header>{_v18_team_form(top, 15)}</div>
  </div>
  <footer class="dd-v18-team-footer">
    <div class="price"><span>LIVE PRICE</span><b>{odds(price)}</b><small>{esc(book)}</small></div>
    <div class="notes"><span>MATCHUP NOTES</span><ul>{_v18_matchup_notes(top, pitcher, hand, hr9)}</ul></div>
  </footer>
</section>'''


def render(board: dict) -> None:
    games = _games(board)
    if not games:
        st.info("No team sheets are available for this slate.")
        return

    requested = str(st.query_params.get("game") or "")
    active = next((game for game in games if game["key"] == requested), games[0])
    st.markdown(
        f'''<header class="dd-v18-page-title"><div><h1>TEAM SHEETS</h1><p>Matchup boards with projected HR upside, batter profiles, and game context.</p></div><aside><span>SLATE DINGER LEADER</span><b>{esc(active['away'])} @ {esc(active['home'])}</b><strong>{active['game_hr_probability']*100:.1f}</strong></aside></header>''',
        unsafe_allow_html=True,
    )
    st.markdown(_game_tabs(games, active["key"]), unsafe_allow_html=True)

    away_players = sorted([p for p in active["players"] if str(p.get("team_name")) == active["away"]], key=lambda p: safe_float(p.get("dinger_score")), reverse=True)
    home_players = sorted([p for p in active["players"] if str(p.get("team_name")) == active["home"]], key=lambda p: safe_float(p.get("dinger_score")), reverse=True)
    st.markdown(
        '<div class="dd-v18-team-grid">'
        + _v18_team_panel(active["away"], active.get("away_id"), away_players, active, "AWAY")
        + _v18_team_panel(active["home"], active.get("home_id"), home_players, active, "HOME")
        + '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="dd-v18-form-legend"><b>READING THE FORM GUIDE</b><span><i class="one">🔥</i> HOME RUN</span><span><i class="multi">2</i> MULTI-HR GAME</span><span><i class="zero"></i> NO HR</span><span><i class="dnp">—</i> DID NOT PLAY / NO DATA</span></div>',
        unsafe_allow_html=True,
    )


# ===== V20 READABLE TEAM SHEETS =====

def _v20_team_form(players: list[dict], games: int) -> str:
    top = players[:6]
    aggregate: list[int | None] = []
    date_labels: list[str] = []
    source_dates = next((list(player.get("recent_game_dates") or []) for player in top if player.get("recent_game_dates")), [])
    source_dates = source_dates[-games:]
    if len(source_dates) < games:
        source_dates = [""] * (games - len(source_dates)) + source_dates

    for offset in range(games):
        values: list[int] = []
        for player in top:
            series = list(player.get("recent_game_hr_series") or [])[-games:]
            if len(series) < games:
                series = [None] * (games - len(series)) + series
            value = series[offset] if offset < len(series) else None
            if value is not None:
                values.append(safe_int(value))
        aggregate.append(sum(values) if values else None)
        date_labels.append(str(source_dates[offset] or "")[-5:])

    cells: list[str] = []
    for value, date_label in zip(aggregate, date_labels):
        if value is None:
            cls, shown, title = "dnp", "—", "No data / did not play"
        elif value <= 0:
            cls, shown, title = "zero", "0", "No home runs by the six listed hitters"
        elif value == 1:
            cls, shown, title = "one", "1", "One combined home run"
        else:
            cls, shown, title = "multi", str(value), f"{value} combined home runs"
        cells.append(
            f'<i class="{cls}" title="{esc(title)}"><span>{shown}</span><small>{esc(date_label)}</small></i>'
        )
    return '<div class="dd20-team-form">' + ''.join(cells) + '</div>'


def _v20_team_panel(team: str, team_id: int | None, players: list[dict], game: dict, side: str) -> str:
    primary, secondary = TEAM_COLORS.get(team, ("#27c7ff", "#ff4df2"))
    pitcher, hand, hr9, era = _pitcher_for(team, game)
    top = sorted(players, key=lambda p: safe_float(p.get("dinger_score")), reverse=True)[:8]
    leader = top[0] if top else {}
    score = safe_float(leader.get("dinger_score"))
    probability = probability_fraction(leader.get("probability")) * 100
    price = leader.get("best_odds") if leader.get("best_odds") is not None else leader.get("fair_odds")
    book = str(leader.get("best_book") or "FAIR PRICE")
    logo = f'<img src="{team_logo(team_id)}">' if team_id else ""
    pitcher_detail = (
        "Starter projection pending"
        if pitcher in {"Not announced", "Awaiting announcement", "TBD"}
        else f"{hand}HP • {hr9:.2f} HR/9 • {era:.2f} ERA"
    )
    weather = leader.get("weather_card_text") or (
        f'{leader.get("weather_grade") or "—"} • {safe_float(leader.get("weather_impact")):+.1f} HR impact'
        if leader.get("weather_available") else "Weather pending"
    )
    return f'''
<section class="dd-v18-team-sheet dd20-team-sheet" style="--team-primary:{primary};--team-secondary:{secondary}">
  <header class="dd-v18-team-brand">
    <div class="club">{logo}<span><small>{esc(side)}</small><b>{esc(team)}</b><em>POWER BOARD</em></span></div>
    <div class="score"><span>DINGER SCORE</span><b>{score:.1f}</b><i></i><span>HR PROBABILITY</span><strong>{probability:.1f}%</strong></div>
  </header>
  <div class="dd-v18-team-pitcher dd20-team-pitcher">
    <div class="avatar">⚾</div>
    <span><small>PROJECTED OPPOSING STARTER</small><b>{esc(pitcher)}</b><em>{esc(pitcher_detail)}</em></span>
    <strong>{esc(weather)}</strong>
  </div>
  <div class="dd-v18-team-body dd20-team-body">
    <div class="dd-v18-team-top"><header>TOP 6 PROJECTED HR HITTERS</header>{_v18_hitter_list(top, primary)}</div>
    <div class="dd-v18-team-form-panel dd20-form-panel">
      <header>TOP-6 HOME RUN FORM</header>
      <p>Each column is one team game. The number is the combined home runs hit by the six listed players.</p>
      <h4>LAST 7 GAMES</h4>{_v20_team_form(top, 7)}
      <h4>LAST 15 GAMES</h4>{_v20_team_form(top, 15)}
      <div class="dd20-inline-legend"><span><i class="zero">0</i> No HR</span><span><i class="one">1</i> One HR</span><span><i class="multi">2+</i> Multi-HR</span><span><i class="dnp">—</i> No data</span></div>
    </div>
  </div>
  <footer class="dd-v18-team-footer">
    <div class="price"><span>LIVE PRICE</span><b>{odds(price)}</b><small>{esc(book)}</small></div>
    <div class="notes"><span>MATCHUP NOTES</span><ul>{_v18_matchup_notes(top, pitcher, hand, hr9)}</ul></div>
  </footer>
</section>'''


def render(board: dict) -> None:
    games = _games(board)
    if not games:
        st.info("No team sheets are available for this slate.")
        return

    requested = str(st.query_params.get("game") or "")
    active = next((game for game in games if game["key"] == requested), games[0])
    st.markdown(
        f'''<header class="dd-v18-page-title dd20-team-title"><div><h1>TEAM SHEETS</h1><p>Side-by-side matchup boards with projected starters, weather, HR upside, and a clearly labeled recent-form guide.</p></div><aside><span>SLATE DINGER LEADER</span><b>{esc(active['away'])} @ {esc(active['home'])}</b><strong>{active['game_hr_probability']*100:.1f}</strong></aside></header>''',
        unsafe_allow_html=True,
    )
    st.markdown(_game_tabs(games, active["key"]), unsafe_allow_html=True)

    away_players = sorted([p for p in active["players"] if str(p.get("team_name")) == active["away"]], key=lambda p: safe_float(p.get("dinger_score")), reverse=True)
    home_players = sorted([p for p in active["players"] if str(p.get("team_name")) == active["home"]], key=lambda p: safe_float(p.get("dinger_score")), reverse=True)
    st.markdown(
        '<div class="dd-v18-team-grid">'
        + _v20_team_panel(active["away"], active.get("away_id"), away_players, active, "AWAY")
        + _v20_team_panel(active["home"], active.get("home_id"), home_players, active, "HOME")
        + '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="dd-v18-form-legend dd20-form-legend"><b>HOW TO READ THE FORM GUIDE</b>'
        '<span><i class="zero">0</i> NO HR</span><span><i class="one">1</i> ONE COMBINED HR</span>'
        '<span><i class="multi">2+</i> MULTIPLE COMBINED HR</span><span><i class="dnp">—</i> NO DATA / DNP</span>'
        '<em>The form panel totals only the six hitters listed on that team sheet.</em></div>',
        unsafe_allow_html=True,
    )
