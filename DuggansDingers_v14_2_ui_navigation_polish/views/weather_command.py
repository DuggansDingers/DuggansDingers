from __future__ import annotations

from html import escape as esc
from urllib.parse import quote

import streamlit as st

from components.stadium_art import stadium_scene_data
from components.ui import probability_fraction, safe_float, safe_int, team_logo
from views.secondary import _v16_signed, _v16_zone_values, _v17_game_key, _v17_weather_games, _v18_game_time


def _weather_icon(description: str) -> str:
    text = str(description or "").lower()
    if "rain" in text or "shower" in text:
        return "🌧"
    if "storm" in text or "thunder" in text:
        return "⛈"
    if "clear" in text:
        return "☾"
    if "sun" in text:
        return "☀"
    return "⛅"


def _updated(board: dict) -> str:
    raw = str(board.get("updated_at") or "")
    if not raw:
        return str(board.get("date") or "")
    try:
        from datetime import datetime
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).strftime("%-I:%M %p ET")
    except Exception:
        return raw[:16]


def _card(game: dict) -> str:
    key = _v17_game_key(game)
    away = str(game.get("away_team_name") or "AWAY")
    home = str(game.get("home_team_name") or "HOME")
    stadium = str(game.get("stadium_name") or game.get("venue_name") or "MLB Ballpark")
    scene = stadium_scene_data(game)
    lf, cf, rf = _v16_zone_values(game)
    available = bool(game.get("weather_available"))
    temp = f"{safe_float(game.get('temperature_f')):.0f}°F" if available else "—"
    wind = safe_float(game.get("wind_speed_mph"))
    direction = str(game.get("wind_field_effect") or "cross").upper()
    grade = str(game.get("weather_grade") or "—")
    description = str(game.get("weather_description") or "Forecast pending")
    impact = safe_float(game.get("weather_impact"))
    color = "#35f28f" if impact >= 3 else "#2ec7ff" if impact >= 0 else "#ffba35"
    style = (
        "background-image:"
        "linear-gradient(90deg,rgba(1,6,13,.18),rgba(1,6,13,.03) 52%,rgba(1,6,13,.18)),"
        "linear-gradient(180deg,rgba(1,6,13,.04),rgba(1,6,13,.24)),"
        f"url('{scene}');--card-accent:{color};"
    )
    return f'''<a class="dd25-wx-link" href="?view=weather&game={quote(key)}" target="_self">
    <article class="dd25-wx-card" style="{style}">
      <header>
        <div class="dd25-wx-match">
          <img src="{team_logo(game.get('away_team_id'))}" alt="{esc(away)}">
          <span>VS</span>
          <img src="{team_logo(game.get('home_team_id'))}" alt="{esc(home)}">
          <b>{esc(away)} @ {esc(home)}</b>
        </div>
        <time>{esc(_v18_game_time(game))} ET</time>
      </header>
      <div class="dd25-wx-body">
        <div class="dd25-wx-copy">
          <small>{esc(stadium)}</small>
          <strong>{temp}</strong>
          <span>{_weather_icon(description)} {esc(description)}</span>
        </div>
        <aside>
          <small>{wind:.0f} mph</small>
          <em>{esc(direction)}</em>
          <b>{esc(grade)}</b>
          <span>WEATHER<br>GRADE</span>
        </aside>
      </div>
      <footer>
        <div><span>LF</span><b>{_v16_signed(lf)}</b></div>
        <div><span>CF</span><b>{_v16_signed(cf)}</b></div>
        <div><span>RF</span><b>{_v16_signed(rf)}</b></div>
        <div><span>HR IMPACT</span><b>{impact:+.1f}</b></div>
      </footer>
    </article></a>'''


def _hitter_rows(board: dict, game: dict) -> str:
    key = _v17_game_key(game)
    players = [
        player for player in board.get("rankings", []) or []
        if str(player.get("weather_game_key") or player.get("schedule_game_key") or player.get("game_id") or "") == str(key)
    ]
    players.sort(key=lambda player: safe_float(player.get("dinger_score")), reverse=True)
    rows = []
    for rank, player in enumerate(players[:8], 1):
        base = probability_fraction(player.get("probability")) * 100
        adjusted = max(0.0, base + safe_float(game.get("weather_impact")) * .35)
        rows.append(
            f'''<div class="dd25-wx-hitter-row">
              <span>{rank}</span>
              <a href="?view=player-intelligence&player={safe_int(player.get('player_id'))}" target="_self">{esc(str(player.get('player_name') or '—'))}</a>
              <b>{esc(str(player.get('team_name') or '—'))}</b>
              <em>{base:.1f}%</em>
              <strong>{adjusted:.1f}%</strong>
              <i>{safe_float(game.get('weather_impact')):+.1f}</i>
            </div>'''
        )
    return "".join(rows) or '<div class="dd25-wx-empty">No hitter projections are connected to this game yet.</div>'


def _detail(board: dict, game: dict) -> None:
    away = str(game.get("away_team_name") or "AWAY")
    home = str(game.get("home_team_name") or "HOME")
    stadium = str(game.get("stadium_name") or game.get("venue_name") or "MLB Ballpark")
    scene = stadium_scene_data(game, detail=True)
    lf, cf, rf = _v16_zone_values(game)
    description = str(game.get("weather_description") or "Game-time forecast")
    st.markdown('<a class="dd25-back" href="?view=weather" target="_self">← ALL BALLPARKS</a>', unsafe_allow_html=True)
    st.markdown(
        f'''<section class="dd25-wx-detail">
          <div class="dd25-wx-detail-scene" style="background-image:linear-gradient(90deg,rgba(1,6,13,.15),rgba(1,6,13,.02) 56%,rgba(1,6,13,.18)),url('{scene}')">
            <header><div><img src="{team_logo(game.get('away_team_id'))}"><b>{esc(away)} @ {esc(home)}</b><img src="{team_logo(game.get('home_team_id'))}"></div><time>{esc(_v18_game_time(game))} ET</time></header>
            <div class="copy"><small>{esc(stadium)}</small><h1>{safe_float(game.get('temperature_f')):.0f}°F</h1><p>{_weather_icon(description)} {esc(description)}</p></div>
            <aside><small>{safe_float(game.get('wind_speed_mph')):.0f} mph</small><em>{esc(str(game.get('wind_field_effect') or 'cross').upper())}</em><b>{esc(str(game.get('weather_grade') or '—'))}</b><span>WEATHER GRADE</span></aside>
          </div>
          <div class="dd25-wx-detail-strip">
            <div><span>LEFT FIELD</span><b>{_v16_signed(lf)}</b></div>
            <div><span>CENTER FIELD</span><b>{_v16_signed(cf)}</b></div>
            <div><span>RIGHT FIELD</span><b>{_v16_signed(rf)}</b></div>
            <div><span>HR IMPACT</span><b>{safe_float(game.get('weather_impact')):+.1f}</b></div>
          </div>
          <div class="dd25-wx-detail-metrics">
            <div><span>HUMIDITY</span><b>{safe_float(game.get('humidity_pct')):.0f}%</b></div>
            <div><span>RAIN CHANCE</span><b>{safe_float(game.get('precip_probability')):.0f}%</b></div>
            <div><span>PRESSURE</span><b>{safe_float(game.get('surface_pressure_hpa')):.0f} hPa</b></div>
            <div><span>ROOF</span><b>{esc(str(game.get('roof_status') or game.get('roof_type') or 'Outdoor').title())}</b></div>
          </div>
          <section class="dd25-wx-hitters"><header><b>WEATHER-ADJUSTED HITTER BOARD</b><span>MODEL HR • WEATHER-ADJUSTED HR • IMPACT</span></header>
            <div class="dd25-wx-hitter-head"><span>RANK</span><span>PLAYER</span><span>TEAM</span><span>MODEL</span><span>ADJ.</span><span>IMPACT</span></div>
            {_hitter_rows(board, game)}
          </section>
        </section>''',
        unsafe_allow_html=True,
    )


def render(board: dict) -> None:
    games = _v17_weather_games(board)
    requested = str(st.query_params.get("game") or "")
    selected = next((game for game in games if _v17_game_key(game) == requested), None)
    if selected:
        _detail(board, selected)
        return

    summary = board.get("weather_summary", {}) or {}
    providers = " / ".join(summary.get("providers") or ["WeatherAPI", "NWS"])
    st.markdown(
        f'''<section class="dd25-wx-hero">
          <div><span>MLB HOME RUN INTELLIGENCE</span><h1>BALLPARK <em>WEATHER COMMAND</em></h1></div>
          <aside>
            <div><span>GAMES TODAY</span><b>{len(games)}</b></div>
            <div><span>DATA SOURCE</span><b>{esc(providers)}</b></div>
            <div><span>UPDATED</span><b>{esc(_updated(board))}</b><small>● Live</small></div>
          </aside>
        </section>''',
        unsafe_allow_html=True,
    )
    if not games:
        st.info("No MLB games were returned for this slate.")
        return
    st.markdown('<div class="dd25-wx-grid">' + "".join(_card(game) for game in games) + '</div>', unsafe_allow_html=True)
    st.markdown(
        '<footer class="dd25-wx-foot"><span>ⓘ Weather forecasts update every 15 minutes</span><i>•</i><span>Wind measured at 10m above field</span><i>•</i><span>HR impact compares to neutral conditions (70°F, 0 wind)</span><b>All times Eastern Time</b></footer>',
        unsafe_allow_html=True,
    )
