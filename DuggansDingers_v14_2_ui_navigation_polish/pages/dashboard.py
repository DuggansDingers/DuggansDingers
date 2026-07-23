from __future__ import annotations

import math
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo
from urllib.parse import quote

import streamlit as st

from components.navigation import go
from components.ui import (
    esc,
    headshot,
    percent,
    probability_fraction,
    safe_float,
    safe_int,
    team_logo,
)


def _probability_color(rank: int) -> str:
    return "#a55cff" if rank == 1 else "#59b9ff"


def _top_pick_cards(rankings: list[dict[str, Any]]) -> str:
    cards: list[str] = []
    for rank, player in enumerate(rankings[:6], 1):
        player_id = int(player.get("player_id") or 0)
        player_href = f"?view=player-intelligence&player={player_id}" if player_id else "?view=daily-board"
        cards.append(
            f'''
<a class="dd-pick-card-link" href="{player_href}" target="_self">
<div class="dd-pick-card">
  <div class="dd-pick-rank rank-{rank}">{rank}</div>
  <img class="dd-pick-photo" src="{headshot(player.get('player_id'), 300)}" alt="{esc(player.get('player_name'))}">
  <div class="dd-pick-copy">
    <div class="dd-pick-name">{esc(player.get('player_name'))}</div>
    <div class="dd-pick-team">{esc(player.get('team_name'))} • {esc(player.get('position') or '—')}</div>
    <div class="dd-pick-prob" style="color:{_probability_color(rank)}">{percent(player.get('probability'))}</div>
    <div class="dd-pick-label">HR Probability</div>
  </div>
  <div class="dd-pick-footer">
    <span><b>{safe_int(player.get('last_7_home_runs'))}</b> Last 7</span>
    <span><b>{safe_int(player.get('last_30_home_runs'))}</b> Last 30</span>
  </div>
</div>
</a>'''
        )
    return '<div class="dd-picks-grid">' + "".join(cards) + "</div>"


def _weather_games(board: dict[str, Any]) -> list[dict[str, Any]]:
    games: dict[str, dict[str, Any]] = {}
    for meta in board.get("games_meta", []) or []:
        key = str(meta.get("game_id") or "")
        if key:
            games[key] = dict(meta)
    for player in board.get("rankings", []) or []:
        key = str(player.get("game_id") or "")
        if not key:
            continue
        item = games.setdefault(key, {})
        for field in (
            "game_id", "game_time", "home_team_name", "away_team_name", "venue_name",
            "weather_available", "weather_source", "weather_time_local", "temperature_f",
            "apparent_temperature_f", "humidity_pct", "dew_point_f", "surface_pressure_hpa",
            "visibility_miles", "cloud_cover_pct", "precip_probability", "wind_speed_mph",
            "wind_gust_mph", "wind_direction_deg", "wind_field_effect", "weather_description",
            "weather_impact", "weather_grade", "stadium_name", "stadium_timezone", "roof_type",
        ):
            if item.get(field) in (None, "") and player.get(field) not in (None, ""):
                item[field] = player.get(field)
    return list(games.values())


def _field_zone_values(weather: dict[str, Any]) -> tuple[int, int, int]:
    impact = safe_float(weather.get("weather_impact"))
    speed = safe_float(weather.get("wind_speed_mph"))
    direction = str(weather.get("wind_field_effect") or "cross").lower()
    wind_deg = safe_float(weather.get("wind_direction_deg"))
    base = max(-18, min(18, round(impact * 1.55)))
    cross = min(10, round(speed * 0.42))
    if direction == "out":
        return base + max(1, cross // 2), base + cross, base + max(1, cross // 2)
    if direction == "in":
        return base - max(1, cross // 2), base - cross, base - max(1, cross // 2)
    if 0 <= wind_deg < 180:
        return base + cross, base, base - cross
    return base - cross, base, base + cross


def _zone_color(value: int) -> str:
    if value >= 10:
        return "#38f45e"
    if value >= 4:
        return "#ffd323"
    if value > -3:
        return "#42a9ff"
    return "#ff493c"


def _signed(value: int) -> str:
    return f"+{value}%" if value > 0 else f"{value}%"


def _weather_icon(description: str) -> str:
    text = description.lower()
    if "clear" in text:
        return "☀"
    if "rain" in text or "drizzle" in text:
        return "🌧"
    if "thunder" in text:
        return "⛈"
    if "snow" in text:
        return "❄"
    if "fog" in text:
        return "🌫"
    return "🌤"


def _format_game_time(weather: dict[str, Any]) -> str:
    value = weather.get("weather_time_local") or weather.get("game_time")
    if not value:
        return "Game time TBD"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        timezone_name = str(weather.get("stadium_timezone") or "")
        if timezone_name and parsed.tzinfo:
            parsed = parsed.astimezone(ZoneInfo(timezone_name))
        return parsed.strftime("%-I:%M %p %Z")
    except (ValueError, TypeError, OSError):
        return str(value)


def _wind_to_label(weather: dict[str, Any]) -> str:
    effect = str(weather.get("wind_field_effect") or "unknown").lower()
    if effect == "out":
        return "OUT TO CF"
    if effect == "in":
        return "IN FROM CF"
    direction = safe_float(weather.get("wind_direction_deg"))
    wind_to = (direction + 180) % 360
    if 45 <= wind_to < 135:
        return "TO RF"
    if 225 <= wind_to < 315:
        return "TO LF"
    return "CROSS FIELD"


def _field_svg(lf: int, cf: int, rf: int, wind_label: str, wind_effect: str) -> str:
    lf_color, cf_color, rf_color = _zone_color(lf), _zone_color(cf), _zone_color(rf)
    if wind_effect == "in":
        x2, y2, marker = 300, 260, "arrowBlue"
        x1, y1 = 300, 95
    elif "RF" in wind_label:
        x1, y1, x2, y2, marker = 300, 350, 495, 165, "arrowWhite"
    elif "LF" in wind_label:
        x1, y1, x2, y2, marker = 300, 350, 105, 165, "arrowWhite"
    else:
        x1, y1, x2, y2, marker = 300, 350, 300, 105, "arrowGreen"
    return f'''
<svg class="dd-field-svg" viewBox="0 0 600 390" role="img" aria-label="Directional home run weather field">
  <defs>
    <linearGradient id="grass" x1="0" y1="1" x2="0" y2="0"><stop offset="0%" stop-color="#143f27"/><stop offset="100%" stop-color="#0e2e20"/></linearGradient>
    <linearGradient id="dirt" x1="0" y1="1" x2="0" y2="0"><stop offset="0%" stop-color="#836936"/><stop offset="100%" stop-color="#3e5c2b"/></linearGradient>
    <marker id="arrowWhite" markerWidth="8" markerHeight="8" refX="5" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#fff"/></marker>
    <marker id="arrowGreen" markerWidth="8" markerHeight="8" refX="5" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#38f45e"/></marker>
    <marker id="arrowBlue" markerWidth="8" markerHeight="8" refX="5" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#42a9ff"/></marker>
    <filter id="glow"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <path d="M300 365 L70 188 Q300 18 530 188 Z" fill="url(#grass)" stroke="#1782bd" stroke-width="2"/>
  <path d="M300 365 L70 188 Q182 81 300 66 L300 365 Z" fill="{lf_color}" fill-opacity=".11" stroke="{lf_color}" stroke-opacity=".55"/>
  <path d="M300 365 L300 66 Q418 81 530 188 Z" fill="{rf_color}" fill-opacity=".11" stroke="{rf_color}" stroke-opacity=".55"/>
  <path d="M300 365 L172 188 Q300 80 428 188 Z" fill="{cf_color}" fill-opacity=".10" stroke="{cf_color}" stroke-opacity=".55"/>
  <path d="M300 365 L235 300 L300 235 L365 300 Z" fill="url(#dirt)" stroke="#c6b579"/>
  <path d="M300 350 L260 310 L300 270 L340 310 Z" fill="#275b2f" stroke="#dbc893"/>
  <circle cx="300" cy="235" r="5" fill="#d6dca5"/><circle cx="300" cy="365" r="7" fill="#f0e8cc"/>
  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#fff" stroke-width="4" marker-end="url(#{marker})" filter="url(#glow)" opacity=".95"/>
  <line x1="300" y1="365" x2="300" y2="98" stroke="#38f45e" stroke-width="2.5" marker-end="url(#arrowGreen)" opacity=".75"/>
</svg>'''


def _weather_dashboard(board: dict[str, Any]) -> str:
    games = _weather_games(board)
    connected = [game for game in games if game.get("weather_available")]
    weather = max(connected, key=lambda item: safe_float(item.get("weather_impact"))) if connected else (games[0] if games else {})

    available = bool(weather.get("weather_available"))
    stadium = str(weather.get("stadium_name") or weather.get("venue_name") or "Ballpark weather")
    description = str(weather.get("weather_description") or ("Weather unavailable" if not available else "Conditions"))
    temperature = safe_float(weather.get("temperature_f"))
    feels = safe_float(weather.get("apparent_temperature_f"), temperature)
    humidity = safe_float(weather.get("humidity_pct"))
    dew = safe_float(weather.get("dew_point_f"))
    pressure = safe_float(weather.get("surface_pressure_hpa"))
    visibility = safe_float(weather.get("visibility_miles"))
    clouds = safe_float(weather.get("cloud_cover_pct"))
    rain = safe_float(weather.get("precip_probability"))
    wind = safe_float(weather.get("wind_speed_mph"))
    impact = safe_float(weather.get("weather_impact"))
    grade = str(weather.get("weather_grade") or "—")
    wind_label = _wind_to_label(weather)
    lf, cf, rf = _field_zone_values(weather)
    field = _field_svg(lf, cf, rf, wind_label, str(weather.get("wind_field_effect") or ""))

    if not available:
        overall_label, overall_class = "UNAVAILABLE", "unavailable"
    elif impact >= 4:
        overall_label, overall_class = "GOOD", "good"
    elif impact <= -3:
        overall_label, overall_class = "POOR", "poor"
    else:
        overall_label, overall_class = "NEUTRAL", "neutral"

    time_text = _format_game_time(weather)
    temp_text = f"{temperature:.0f}°F" if available else "—"
    feels_text = f"Feels like {feels:.0f}°" if available else "Awaiting live forecast"
    pressure_text = f"{pressure:.0f} hPa" if pressure else "—"
    visibility_text = f"{visibility:.0f} mi" if visibility else "—"
    dew_text = f"{dew:.0f}°F" if dew else "—"
    cloud_text = f"{clouds:.0f}%" if available else "—"
    rain_text = f"{rain:.0f}%" if available else "—"
    wind_text = f"{wind:.0f} mph {wind_label}" if available else "—"
    impact_text = f"{impact:+.0f}%" if available else "—"

    return f'''
<section class="dd-weather-shell">
  <div class="dd-weather-heading"><div><span class="dd-weather-cloud">☁</span><b>Weather &amp; Ballpark Conditions</b><small>Live weather impact for today's games</small></div></div>
  <div class="dd-weather-layout">
    <div class="dd-weather-summary">
      <div class="dd-stadium-row"><div><b>{esc(stadium)}</b><span>{esc(weather.get('home_team_name') or '')}</span></div><em class="{overall_class}">{overall_label}<small>Overall Impact</small></em></div>
      <div class="dd-big-temp"><strong>{temp_text}</strong><div><i>{_weather_icon(description)}</i><b>{esc(description)}</b><span>{feels_text}</span></div></div>
      <div class="dd-condition-grid">
        <div><i>≋</i><span>Wind</span><b>{wind:.0f} mph</b><small>{wind_label}</small></div><div><i>♧</i><span>Humidity</span><b>{humidity:.0f}%</b></div><div><i>◴</i><span>Pressure</span><b>{pressure_text}</b></div>
        <div><i>◌</i><span>Dew Point</span><b>{dew_text}</b></div><div><i>◉</i><span>Visibility</span><b>{visibility_text}</b></div><div><i>☁</i><span>Cloud Cover</span><b>{cloud_text}</b></div>
      </div>
      <div class="dd-impact-title">HR Impact Summary</div>
      <div class="dd-impact-grid"><div class="green"><span>Left Field</span><b>{_signed(lf)}</b></div><div class="yellow"><span>Center Field</span><b>{_signed(cf)}</b></div><div class="red"><span>Right Field</span><b>{_signed(rf)}</b></div><div class="blue"><span>Overall HR Impact</span><b>{impact_text}</b></div></div>
    </div>
    <div class="dd-field-panel">
      <div class="dd-field-title">HR Effectiveness by Direction</div><div class="dd-wind-box"><span>Wind Direction</span><b>➤ {wind_label}</b><span>Wind Speed</span><strong>{wind:.0f} MPH</strong></div>
      {field}
      <div class="dd-zone-tag lf" style="--zone:{_zone_color(lf)}"><b>{_signed(lf)}</b><span>Left Field</span></div><div class="dd-zone-tag cf" style="--zone:{_zone_color(cf)}"><b>{_signed(cf)}</b><span>Center Field</span></div><div class="dd-zone-tag rf" style="--zone:{_zone_color(rf)}"><b>{_signed(rf)}</b><span>Right Field</span></div>
      <div class="dd-field-wind">WIND {wind:.0f} mph <b>{wind_label}</b></div>
    </div>
    <div class="dd-forecast-panel">
      <div class="dd-forecast-title">Game Time Forecast</div><div class="dd-game-time">{esc(time_text)}</div>
      <div class="dd-forecast-list"><div><span>☀ &nbsp; Temp</span><b>{temp_text}</b></div><div><span>≋ &nbsp; Wind</span><b>{wind_text}</b></div><div><span>♧ &nbsp; Humidity</span><b>{humidity:.0f}%</b></div><div><span>☂ &nbsp; Precip</span><b>{rain_text}</b></div><div><span>☁ &nbsp; Clouds</span><b>{cloud_text}</b></div><div class="impact"><span>🔥 &nbsp; HR Impact</span><b>{impact_text}</b></div></div>
      <div class="dd-hourly-button">◷ &nbsp; Live forecast • {esc(str(weather.get('weather_source') or 'Open-Meteo'))}</div><div class="dd-weather-grade">Weather Grade <b>{esc(grade)}</b></div>
    </div>
  </div>
</section>'''


def _team_id_map(rankings: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for player in rankings:
        team = str(player.get("team_name") or "")
        if team and player.get("team_id"):
            result[team] = player.get("team_id")
    return result


def _team_probability(players: list[dict[str, Any]]) -> float:
    top = sorted(players, key=lambda item: probability_fraction(item.get("probability")), reverse=True)[:5]
    return 1 - math.prod(1 - probability_fraction(player.get("probability")) for player in top)


def _game_cards(board: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    rankings = board.get("rankings", []) or []
    by_game: dict[str, list[dict[str, Any]]] = {}
    for player in rankings:
        by_game.setdefault(str(player.get("game_id") or player.get("team_name")), []).append(player)
    meta_map = {str(meta.get("game_id")): meta for meta in board.get("games_meta", []) or []}
    team_ids = _team_id_map(rankings)
    cards_data: list[dict[str, Any]] = []
    for key, players in by_game.items():
        meta = meta_map.get(key, {})
        away, home = str(meta.get("away_team_name") or ""), str(meta.get("home_team_name") or "")
        if not away or not home:
            teams = list(dict.fromkeys(str(p.get("team_name") or "") for p in players if p.get("team_name")))
            away, home = away or (teams[0] if teams else "Away"), home or (teams[1] if len(teams) > 1 else "Home")
        away_players = [p for p in players if str(p.get("team_name")) == away]
        home_players = [p for p in players if str(p.get("team_name")) == home]
        team_prob = max(_team_probability(away_players), _team_probability(home_players))
        top_score = max((safe_float(p.get("dinger_score")) for p in players), default=0)
        park_factor = 0.88 + max(0, min(100, safe_float(players[0].get("ballpark_score") if players else 50))) / 100 * 0.30
        cards_data.append({"key": key, "away": away, "home": home, "away_id": team_ids.get(away), "home_id": team_ids.get(home), "probability": team_prob, "park_factor": park_factor, "top_score": top_score, "weather_impact": safe_float((meta or players[0]).get("weather_impact") if players else 0), "game_time": meta.get("game_time")})
    cards_data.sort(key=lambda item: (item["probability"], item["top_score"]), reverse=True)
    cards_data = cards_data[:5]

    cards: list[str] = []
    for rank, game in enumerate(cards_data, 1):
        factor = game["park_factor"]
        factor_label = "Great" if factor >= 1.08 else "Good" if factor >= 1.01 else "Neutral"
        accent = "#9a4dff" if rank in {1, 3, 5} else "#18a8ff"
        away_logo = f'<img src="{team_logo(game["away_id"])}">' if game.get("away_id") else f'<b>{esc(game["away"])}</b>'
        home_logo = f'<img src="{team_logo(game["home_id"])}">' if game.get("home_id") else f'<b>{esc(game["home"])}</b>'
        suffix = "st" if rank == 1 else "nd" if rank == 2 else "rd" if rank == 3 else "th"
        game_href = f"?view=team-sheets&game={quote(str(game['key']))}"
        cards.append(f'''
<a class="dd-team-card-link" href="{game_href}" target="_self" aria-label="Open {esc(game['away'])} versus {esc(game['home'])} team sheets">
<div class="dd-team-card" style="--accent:{accent}"><div class="dd-team-match">{esc(game['away'])} vs {esc(game['home'])}</div><div class="dd-team-logos">{away_logo}<span>VS</span>{home_logo}</div><div class="dd-team-metrics"><div><span>Team HR Prob</span><b>{game['probability']*100:.1f}%</b><small>({rank}{suffix})</small></div><div><span>Park Factor</span><b>{factor:.2f}</b><small>{factor_label}</small></div></div><div class="dd-view-sheet">View Sheet &nbsp;›</div></div>
</a>''')
    return '<div class="dd-team-cards">' + "".join(cards) + "</div>", cards_data


def _today_games(cards_data: list[dict[str, Any]]) -> str:
    rows: list[str] = []
    for game in cards_data[:5]:
        impact = safe_float(game.get("weather_impact"))
        icon, color = ("☀", "#43ef6c") if impact >= 3 else (("☁", "#ff8c3a") if impact > -2 else ("☂", "#42a9ff"))
        time_text = "TBD"
        if game.get("game_time"):
            try:
                parsed = datetime.fromisoformat(str(game["game_time"]).replace("Z", "+00:00"))
                time_text = parsed.strftime("%-I:%M %p")
            except (ValueError, TypeError, OSError):
                time_text = str(game["game_time"])
        rows.append(f'<div class="dd-game-row"><b>{esc(game["away"])} @ {esc(game["home"])}</b><span>{esc(time_text)}</span><em style="color:{color}">{icon} {impact:+.0f}%</em></div>')
    if not rows:
        rows.append('<div class="dd-game-row"><b>No games loaded</b><span>—</span><em>—</em></div>')
    return '<div class="dd-games-list">' + "".join(rows) + "</div>"


def _footer(board: dict[str, Any]) -> str:
    statuses = board.get("data_sources", {}) or {}
    weather_status = str(statuses.get("Weather") or "unavailable").title()
    return f'''<footer class="dd-app-footer"><div><i>◉</i><b>Real Data</b><span>Live MLB + {esc(weather_status)} Weather</span></div><div><i>✥</i><b>Advanced Models</b><span>Projection + rolling power</span></div><div><i>◷</i><b>Data Updated</b><span>Cached for speed and stability</span></div><div><i>✦</i><b>Built for Daily Decisions</b><span>Connected sources only</span></div><small>© 2026 Duggan's Dingers</small></footer>'''


def render(board: dict[str, Any]) -> None:
    rankings = board.get("rankings", []) or []
    if not rankings:
        st.error("No rankings are available. Confirm the API key, selected slate date, and internet connection, then refresh.")
        return

    title_col, action_col = st.columns([8.8, 2.2], vertical_alignment="center")
    with title_col:
        st.markdown('<div class="dd-home-section-title"><i>⚡</i><div><b>Today\'s Top Home Run Picks</b><span>Our 6 highest projected HR edge plays</span></div></div>', unsafe_allow_html=True)
    with action_col:
        if st.button("⌁  View All Top Plays", use_container_width=True, key="view_all_top"):
            go("Daily Board"); st.rerun()

    st.markdown(_top_pick_cards(rankings), unsafe_allow_html=True)
    st.markdown(_weather_dashboard(board), unsafe_allow_html=True)

    team_html, game_cards = _game_cards(board)
    team_col, games_col, tools_col = st.columns([7.3, 2.35, 2.55], gap="small", vertical_alignment="top")
    with team_col:
        head1, head2 = st.columns([5, 1.25], vertical_alignment="center")
        with head1:
            st.markdown('<div class="dd-panel-title purple"><i>▤</i><div><b>Team Cheat Sheets</b><span>Deep dive into every team\'s matchups, stats, and key hitters</span></div></div>', unsafe_allow_html=True)
        with head2:
            if st.button("View All Teams", use_container_width=True, key="all_teams"):
                go("Team Sheets"); st.rerun()
        st.markdown(team_html, unsafe_allow_html=True)
    with games_col:
        st.markdown('<div class="dd-small-panel-title"><b>⚡ Today\'s Games</b><span>View All</span></div>', unsafe_allow_html=True)
        st.markdown(_today_games(game_cards), unsafe_allow_html=True)
    with tools_col:
        with st.container(key="quick_tools"):
            st.markdown('<div class="dd-small-panel-title"><b>Quick Tools</b></div>', unsafe_allow_html=True)
            if st.button("◉  Player Intelligence Center", use_container_width=True, key="tool_player"):
                go("Player Intelligence"); st.rerun()
            if st.button("◎  Today\'s Home Run Watchlist", use_container_width=True, key="tool_watch"):
                go("Daily Board"); st.rerun()
            if st.button("✂  Parlay Builder", use_container_width=True, key="tool_parlay"):
                go("Parlay Lab"); st.rerun()
            if st.button("▥  Props & Sportsbook", use_container_width=True, key="tool_props"):
                go("Sportsbook"); st.rerun()

    st.markdown(_footer(board), unsafe_allow_html=True)
