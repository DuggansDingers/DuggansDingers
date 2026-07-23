from __future__ import annotations

import base64
import html
from pathlib import Path
from typing import Any

import streamlit as st

from config import LOGO_PATH, STADIUMS_DIR, TEAM_COLORS


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def image_data(path: Path) -> str:
    if not path.exists():
        return ""
    ext = path.suffix.lower().lstrip(".") or "png"
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/{ext};base64,{payload}"


def headshot(player_id: Any, width: int = 300) -> str:
    return f"https://img.mlbstatic.com/mlb-photos/image/upload/w_{width},q_100/v1/people/{player_id}/headshot/67/current"


def team_logo(team_id: Any) -> str:
    return f"https://www.mlbstatic.com/team-logos/{team_id}.svg"


def odds(value: Any) -> str:
    try:
        number = float(value)
        return f"+{number:.0f}" if number > 0 else f"{number:.0f}"
    except (TypeError, ValueError):
        return "—"


def probability_fraction(value: Any) -> float:
    number = safe_float(value)
    return max(0.0, min(1.0, number if 0 <= number <= 1 else number / 100))


def percent(value: Any) -> str:
    return f"{probability_fraction(value) * 100:.1f}%"




def sportsbook_price(player: dict[str, Any]) -> str:
    if player.get("best_odds") is None:
        return odds(player.get("fair_odds"))
    book = esc(player.get("best_book") or "Book")
    edge = player.get("edge_pct")
    edge_text = f"{safe_float(edge):+.1f}% edge" if edge is not None else ""
    color = "#35e27e" if edge is not None and safe_float(edge) > 0 else "#ffbd2f" if edge is not None else "#91a6bc"
    return f'<span class="dd-book-price">{odds(player.get("best_odds"))}<small>{book}</small><em style="color:{color}">{edge_text}</em></span>'

def sportsbook_badge(player: dict[str, Any]) -> str:
    if player.get("best_odds") is None:
        return "No live price"
    return f"{esc(player.get('best_book') or 'Book')} {odds(player.get('best_odds'))} • {safe_float(player.get('edge_pct')):+.1f}% edge"

def decimal_stat(value: Any) -> str:
    number = safe_float(value)
    return f"{number:.3f}" if number > 0 else "—"


def logo_data() -> str:
    return image_data(LOGO_PATH)



def weather_badge(player: dict[str, Any]) -> str:
    if not player.get("weather_available"):
        return "Weather unavailable"
    roof = str(player.get("roof_type") or "outdoor")
    if roof == "retractable":
        return f"{safe_float(player.get('temperature_f')):.0f}°F • roof unconfirmed"
    wind = str(player.get("wind_field_effect") or "unknown").upper()
    speed = safe_float(player.get("wind_speed_mph"))
    return f"{safe_float(player.get('temperature_f')):.0f}°F • {speed:.0f} mph {wind}"


def weather_color(player: dict[str, Any]) -> str:
    impact = safe_float(player.get("weather_impact"))
    if impact >= 5:
        return "#35ff93"
    if impact >= 2:
        return "#35d8ff"
    if impact > -2:
        return "#a64dff"
    if impact > -5:
        return "#ffbd2f"
    return "#ff573d"

def score_color(score: float) -> str:
    if score >= 92:
        return "#ff3038"
    if score >= 85:
        return "#ff9225"
    if score >= 78:
        return "#a64dff"
    if score >= 68:
        return "#258eff"
    return "#7f95ad"


def risk_label(player: dict[str, Any]) -> tuple[str, str]:
    probability = probability_fraction(player.get("probability"))
    score = safe_float(player.get("dinger_score"))
    if probability >= 0.30 and score >= 82:
        return "Prime", "#35e27e"
    if probability >= 0.22 and score >= 70:
        return "Strong", "#2f9fff"
    if probability >= 0.15:
        return "Longshot", "#ffbd2f"
    return "Pipedream", "#ff6534"


def trend_label(player: dict[str, Any]) -> tuple[str, str]:
    season = safe_float(player.get("season_hr_rate"))
    seven = safe_float(player.get("last_7_hr_rate"))
    thirty = safe_float(player.get("last_30_hr_rate"))
    if seven >= max(season * 1.35, thirty * 1.25) and safe_int(player.get("last_7_home_runs")) > 0:
        return "HOT", "#ff3038"
    if seven > season and safe_int(player.get("last_7_home_runs")) > 0:
        return "UP", "#35e27e"
    if season > 0 and seven <= season * 0.55:
        return "COOL", "#7890aa"
    return "STEADY", "#2f9fff"


def topbar(board_date: str) -> None:
    st.markdown(
        f'''
<div class="dd-topbar">
  <div></div>
  <div class="dd-wordmark">
    <div class="dd-wordmark-main">DuggansDingers</div>
    <div class="dd-wordmark-sub">Home Run Intelligence</div>
  </div>
  <div class="dd-top-actions">
    <div class="dd-top-control">▣ &nbsp; {esc(board_date or 'Today')} &nbsp;⌄</div>
    <div class="dd-top-control">▽ &nbsp; Live Filters</div>
  </div>
</div>''',
        unsafe_allow_html=True,
    )


def source_ribbon(board: dict[str, Any]) -> None:
    statuses = board.get("data_sources", {}) or {}
    pills = "".join(
        f'<span class="dd-source-pill {"live" if str(status).lower() == "live" else "pending"}">{esc(name)}: {esc(status)}</span>'
        for name, status in statuses.items()
    )
    st.markdown(
        f'''
<div class="dd-alert-ribbon">
  <div><strong>MODEL BOARD</strong> • Ballpark Pal projection + MLB rolling power history. Connected data only—live Open-Meteo weather and imported sportsbook prices when available; no fake values.</div>
  <div class="dd-source-pills">{pills}</div>
</div>''',
        unsafe_allow_html=True,
    )


def _feature_card_html(
    label: str,
    player: dict[str, Any],
    main_value: str,
    caption: str,
    accent: str,
    override_name: str | None = None,
    override_meta: str | None = None,
) -> str:
    brand = ""
    name = override_name or str(player.get("player_name") or "—")
    meta = override_meta or f"{player.get('team_name','—')} • {player.get('position','—')} • vs {player.get('opponent','—')} • {player.get('opposing_pitcher_hand','—')}HP {player.get('opposing_pitcher','TBD')}"
    player_image = ""
    if player.get("player_id"):
        player_image = f'<img class="dd-feature-player" src="{headshot(player.get("player_id"), 260)}">'
    return f'''
<div class="dd-feature-card" style="--accent:{accent}">
  <div class="dd-feature-title">{esc(label)}</div>
  {brand}{player_image}<div class="dd-feature-shade"></div>
  <div class="dd-feature-content">
    <div class="dd-feature-name">{esc(name)}</div>
    <div class="dd-feature-meta">{esc(meta)}</div>
    <div class="dd-feature-value">{esc(main_value)}</div>
    <div class="dd-feature-caption">{esc(caption)}</div>
    <div class="dd-feature-stats">
      <div class="dd-feature-stat"><b>{safe_int(player.get('season_home_runs'))}</b><span>Season HR</span></div>
      <div class="dd-feature-stat"><b>{safe_int(player.get('last_7_home_runs'))}</b><span>Last 7</span></div>
      <div class="dd-feature-stat"><b>{safe_int(player.get('last_15_home_runs'))}</b><span>Last 15</span></div>
      <div class="dd-feature-stat"><b>{safe_int(player.get('last_30_home_runs'))}</b><span>Last 30</span></div>
    </div>
  </div>
</div>'''


def feature_grid_html(cards: list[dict[str, Any]]) -> str:
    return '<div class="dd-feature-grid">' + "".join(
        _feature_card_html(
            card["label"],
            card["player"],
            card["value"],
            card["caption"],
            card["accent"],
            card.get("name"),
            card.get("meta"),
        )
        for card in cards
    ) + "</div>"


def _sparkline(player: dict[str, Any], color: str) -> str:
    series = player.get("recent_game_hr_series") or []
    if not series:
        return '<span style="color:#6f849a">—</span>'
    bars = []
    for value in series[-12:]:
        height = 5 if safe_int(value) == 0 else min(30, 16 + safe_int(value) * 8)
        opacity = ".35" if safe_int(value) == 0 else "1"
        bars.append(f'<i style="height:{height}px;opacity:{opacity}"></i>')
    return f'<div class="dd-spark" style="--spark:{color}">{"".join(bars)}</div>'


def ranking_table_html(rankings: list[dict[str, Any]], limit: int = 8) -> str:
    rows: list[str] = []
    for index, player in enumerate(rankings[:limit], 1):
        rank_class = "gold" if index == 1 else "silver" if index == 2 else "bronze" if index == 3 else ""
        score = safe_float(player.get("dinger_score"))
        color = score_color(score)
        trend, trend_color = trend_label(player)
        rows.append(f'''
<tr>
  <td><span class="dd-rank-badge {rank_class}">{index}</span></td>
  <td><div class="dd-player-wrap"><img src="{headshot(player.get('player_id'),120)}"><div class="dd-player-text"><strong>{esc(player.get('player_name'))}</strong><span>{esc(player.get('position','—'))} • vs {esc(player.get('opponent','—'))} • {esc(player.get('opposing_pitcher','TBD'))}</span></div></div></td>
  <td><div class="dd-team-wrap"><img src="{team_logo(player.get('team_id'))}"><span>{esc(player.get('team_name'))}</span></div></td>
  <td><span class="dd-score-ring" style="--score-color:{color}">{score:.1f}</span></td>
  <td class="dd-num">{percent(player.get('probability'))}</td>
  <td class="dd-odds">{sportsbook_price(player)}</td>
  <td><span class="dd-mini-stat">{safe_int(player.get('season_home_runs'))}<small>HR</small></span></td>
  <td><span class="dd-mini-stat">{safe_int(player.get('last_7_home_runs'))}<small>HR</small></span></td>
  <td><span class="dd-mini-stat">{safe_int(player.get('last_15_home_runs'))}<small>HR</small></span></td>
  <td><span class="dd-mini-stat">{safe_int(player.get('last_30_home_runs'))}<small>HR</small></span></td>
  <td class="dd-num">{decimal_stat(player.get('season_slg'))}</td>
  <td class="dd-num">{decimal_stat(player.get('season_ops'))}</td>
  <td><div style="color:{trend_color}">{_sparkline(player, trend_color)}<div class="dd-trend-label">{trend}</div></div></td>
</tr>''')
    return f'''
<div class="dd-sectionbar"><div class="dd-sectionbar-title"><span>♛</span> Top Home Run Rankings</div><div class="dd-sectionbar-sub">Real rolling MLB history • Top {min(limit, len(rankings))} shown</div></div>
<div class="dd-table-shell"><table class="dd-rank-table">
<colgroup><col style="width:4%"><col style="width:17%"><col style="width:8%"><col style="width:8%"><col style="width:7%"><col style="width:7%"><col style="width:6%"><col style="width:5.5%"><col style="width:5.5%"><col style="width:5.5%"><col style="width:5.5%"><col style="width:5.5%"><col style="width:10.5%"></colgroup>
<thead><tr><th>Rank</th><th>Player</th><th>Team</th><th>Dinger Score</th><th>HR Prob</th><th>Best Odds</th><th>Season</th><th>Last 7</th><th>Last 15</th><th>Last 30</th><th>SLG</th><th>OPS</th><th>Trend</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>'''


def bottom_strip(board: dict[str, Any]) -> str:
    rankings = board.get("rankings", []) or []
    teams = {str(player.get("team_name")) for player in rankings}
    hot = sum(1 for player in rankings if trend_label(player)[0] in {"HOT", "UP"})
    average_probability = sum(probability_fraction(player.get("probability")) for player in rankings) / len(rankings) if rankings else 0
    top_score = max((safe_float(player.get("dinger_score")) for player in rankings), default=0)
    weather = board.get("weather_summary", {}) or {}
    weather_value = f"{safe_int(weather.get('favorable_games'))} Games" if weather.get("games_available") else "Unavailable"
    items = [
        ("◉", "Full MLB Slate", f"{board.get('games',0)} Games", "#2e9fff"),
        ("☁", "Weather Boost", weather_value, "#35d8ff"),
        ("↗", "Heating Up", f"{hot} Players", "#35e27e"),
        ("⚡", "Board Avg HR", f"{average_probability*100:.1f}%", "#a64dff"),
        ("⚾", "Top Dinger Score", f"{top_score:.1f}", "#ff6d20"),
    ]
    return '<div class="dd-bottom-strip">' + ''.join(
        f'<div class="dd-bottom-stat" style="--accent:{color}"><div class="dd-bottom-icon" style="color:{color}">{icon}</div><div><div class="dd-bottom-label">{label}</div><div class="dd-bottom-value">{value}</div></div></div>'
        for icon, label, value, color in items
    ) + '</div>'


def player_card_html(player: dict[str, Any], rank: int | None = None) -> str:
    score = safe_float(player.get("dinger_score"))
    accent = score_color(score)
    risk, risk_color = risk_label(player)
    trend, trend_color = trend_label(player)
    rank_html = f'<span class="dd-rank-badge {"gold" if rank == 1 else "silver" if rank == 2 else "bronze" if rank == 3 else ""}">{rank}</span>' if rank else ""
    return f'''
<div class="dd-player-card" style="--accent:{accent}">
  <div class="dd-player-card-score">{score:.1f}<small>Dinger Score</small></div>
  <div class="dd-player-card-head"><img src="{headshot(player.get('player_id'),180)}"><div><div class="dd-player-card-name">{esc(player.get('player_name'))}</div><div class="dd-player-card-team"><img src="{team_logo(player.get('team_id'))}">{esc(player.get('team_name'))} • {esc(player.get('position','—'))} • vs {esc(player.get('opponent','—'))} • {esc(player.get('opposing_pitcher','TBD'))}</div></div></div>
  <div class="dd-card-stats">
    <div class="dd-card-stat"><b>{percent(player.get('probability'))}</b><span>HR Prob</span></div>
    <div class="dd-card-stat"><b>{odds(player.get('best_odds')) if player.get('best_odds') is not None else odds(player.get('fair_odds'))}</b><span>{esc(player.get('best_book') or 'Fair Odds')}</span></div>
    <div class="dd-card-stat"><b>{safe_int(player.get('season_home_runs'))}</b><span>Season HR</span></div>
    <div class="dd-card-stat"><b>{decimal_stat(player.get('season_ops'))}</b><span>OPS</span></div>
    <div class="dd-card-stat"><b>{safe_int(player.get('last_7_home_runs'))}</b><span>Last 7</span></div>
    <div class="dd-card-stat"><b>{safe_int(player.get('last_15_home_runs'))}</b><span>Last 15</span></div>
    <div class="dd-card-stat"><b>{safe_int(player.get('last_30_home_runs'))}</b><span>Last 30</span></div>
    <div class="dd-card-stat"><b>{decimal_stat(player.get('season_slg'))}</b><span>SLG</span></div>
  </div>
  <div class="dd-card-footer"><span>{rank_html} Overall #{safe_int(player.get('overall_rank'))}</span><span style="color:{trend_color};font-weight:900">{trend}</span><span style="color:{'#35e27e' if safe_float(player.get('edge_pct')) > 0 else '#91a6bc'};font-weight:900">{safe_float(player.get('edge_pct')):+.1f}% EDGE</span><span class="dd-risk-chip" style="--accent:{risk_color}">{risk}</span></div>
</div>'''


def player_grid_html(players: list[dict[str, Any]], start_rank: int = 1) -> str:
    return '<div class="dd-player-grid">' + ''.join(player_card_html(player, start_rank + index) for index, player in enumerate(players)) + '</div>'


def team_gradient(team: str) -> str:
    first, second = TEAM_COLORS.get(team, ("#0b2a50", "#116fc4"))
    return f"linear-gradient(130deg,{first},{second})"


def stadium_background(team: str) -> str:
    for extension in ("jpg", "jpeg", "png", "webp"):
        path = STADIUMS_DIR / f"{team}.{extension}"
        if path.exists():
            return f"url('{image_data(path)}')"
    return team_gradient(team)


def grade(score: float) -> tuple[str, str]:
    if score >= 90:
        return "ELITE", "#37e29a"
    if score >= 80:
        return "STRONG", "#44d8ff"
    if score >= 70:
        return "WATCH", "#ffd05c"
    return "LONGSHOT", "#ff8a28"


def profile_banner(player: dict[str, Any]) -> None:
    team = str(player.get("team_name") or "N/A")
    score = safe_float(player.get("dinger_score"))
    label, color = grade(score)
    st.markdown(
        f'''
<div class="dd-profile" style="--profile-bg:{stadium_background(team)}">
  <div class="dd-profile-inner"><div class="dd-profile-copy">
    <div class="dd-eyebrow">{esc(team)} • {esc(player.get('position','—'))} • BATS {esc(player.get('bat_side','—'))} • vs {esc(player.get('opponent','—'))}</div>
    <div class="dd-player-name">{esc(player.get('player_name','Unknown'))}</div>
    <div class="dd-profile-score">{score:.1f}<small>Dinger Score</small></div>
    <div style="width:min(540px,66%);margin-top:12px" class="dd-meter"><span style="width:{max(0,min(100,score)):.1f}%"></span></div>
    <div class="dd-ribbon"><span style="border-color:{color};color:{color}">{label} PICK</span><span>{percent(player.get('probability'))} MODEL HR</span><span>{odds(player.get('fair_odds'))} FAIR ODDS</span><span>{safe_int(player.get('season_home_runs'))} SEASON HR</span><span style="border-color:{weather_color(player)};color:{weather_color(player)}">{esc(weather_badge(player))}</span></div>
  </div></div>
  <img class="dd-headshot" src="{headshot(player.get('player_id'),700)}">
</div>''',
        unsafe_allow_html=True,
    )


def section(title: str, kicker: str = "", trailing: str = "") -> None:
    trailing_html = f'<div class="dd-sectionbar-sub">{esc(trailing)}</div>' if trailing else ""
    st.markdown(
        f'<div class="dd-sectionbar"><div><div class="dd-eyebrow">{esc(kicker)}</div><div class="dd-sectionbar-title">{esc(title)}</div></div>{trailing_html}</div>',
        unsafe_allow_html=True,
    )


def player_reasons(player: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    score = safe_float(player.get("dinger_score"))
    seven = safe_float(player.get("last_7_hr_rate"))
    thirty = safe_float(player.get("last_30_hr_rate"))
    season = safe_float(player.get("season_hr_rate"))
    if score >= 88:
        reasons.append("Elite combination of projection and historical power")
    elif score >= 76:
        reasons.append("Strong overall model profile relative to today's board")
    if seven > max(season, thirty) and safe_int(player.get("last_7_home_runs")) > 0:
        reasons.append("Seven-game home-run pace is running above longer windows")
    if safe_int(player.get("last_30_home_runs")) >= 5:
        reasons.append("Sustained power across the last 30 games")
    if safe_float(player.get("season_slg")) >= 0.500:
        reasons.append("Season slugging profile supports real extra-base power")
    if probability_fraction(player.get("probability")) >= 0.25:
        reasons.append("Top-tier home-run probability on the current slate")
    if safe_float(player.get("fair_odds")) >= 350 and score >= 65:
        reasons.append("High-payout price while retaining a usable model grade")
    if player.get("weather_available") and safe_float(player.get("weather_impact")) >= 3:
        reasons.append(f"Favorable game-time weather ({player.get('weather_grade','—')}) with {weather_badge(player)}")
    elif player.get("weather_available") and safe_float(player.get("weather_impact")) <= -3:
        reasons.append(f"Weather is a meaningful power penalty: {weather_badge(player)}")
    if not reasons:
        reasons.append("Balanced projection, season power, and recent form")
    return reasons[:5]


def hero(title: str, subtitle: str, eyebrow: str = "MLB HOME RUN INTELLIGENCE", stats: dict[str, Any] | None = None) -> None:
    stats = stats or {}
    stats_html = "".join(
        f'<div style="min-width:92px;padding:9px 11px;border:1px solid #174e80;border-radius:7px;background:#06182b"><div style="font-size:.61rem;text-transform:uppercase;color:#8fa5bf;font-weight:800">{esc(key)}</div><div style="font-family:Barlow Condensed,sans-serif;font-size:1.22rem;font-weight:900;color:#fff">{esc(value)}</div></div>'
        for key, value in stats.items()
    )
    st.markdown(
        f'''
<div class="dd-hero"><div style="display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap">
  <div><div class="dd-eyebrow">{esc(eyebrow)}</div><div class="dd-hero-title">{title}</div><div class="dd-hero-sub">{esc(subtitle)}</div></div>
  <div style="display:flex;gap:8px;flex-wrap:wrap">{stats_html}</div>
</div></div>''',
        unsafe_allow_html=True,
    )


def team_cheat_card_html(team: str, players: list[dict[str, Any]], board_date: str) -> str:
    first, second = TEAM_COLORS.get(team, ("#0b5da7", "#ffbd2f"))
    team_id = players[0].get("team_id") if players else ""
    opponent = players[0].get("opponent", "—") if players else "—"
    weather_text = weather_badge(players[0]) if players else "Weather unavailable"
    weather_grade = players[0].get("weather_grade", "—") if players else "—"
    rows: list[str] = []
    for rank, player in enumerate(players[:5], 1):
        rows.append(f'''
<div class="dd-cheat-row">
  <div class="dd-cheat-rank">{rank}</div>
  <div class="dd-cheat-player"><img src="{headshot(player.get('player_id'),90)}"><div><b>{esc(player.get('player_name'))}</b><span>{esc(player.get('position','—'))} • {odds(player.get('fair_odds'))}</span></div></div>
  <div class="dd-cheat-metric">{safe_float(player.get('dinger_score')):.1f}<small>Score</small></div>
  <div class="dd-cheat-metric">{percent(player.get('probability'))}<small>HR Prob</small></div>
  <div class="dd-cheat-metric">{safe_int(player.get('season_home_runs'))}<small>Season</small></div>
  <div class="dd-cheat-metric">{safe_int(player.get('last_7_home_runs'))}<small>L7</small></div>
  <div class="dd-cheat-metric">{safe_int(player.get('last_30_home_runs'))}<small>L30</small></div>
</div>''')
    return f'''
<div class="dd-cheat-card" style="--team-a:{first};--team-b:{second}">
  <div class="dd-cheat-head"><div class="dd-cheat-team"><img src="{team_logo(team_id)}"><div><b>{esc(team)} Daily Dinger Sheet</b><span>vs {esc(opponent)} • {esc(weather_text)} • Weather {esc(weather_grade)}</span></div></div><div class="dd-cheat-date">{esc(board_date)}</div></div>
  <div class="dd-cheat-list">{''.join(rows)}</div>
</div>'''


def parlay_ticket_html(
    picks: list[dict[str, Any]],
    profile: str,
    combined_probability: float,
    combined_american: float,
    decimal_odds: float,
    stake: float,
    profit: float,
    total_return: float,
) -> str:
    accent = {"Balanced": "#35e27e", "Longshot": "#ffbd2f", "Pipedream": "#ff573d"}.get(profile, "#2f9fff")
    legs: list[str] = []
    for index, player in enumerate(picks, 1):
        legs.append(f'''
<div class="dd-ticket-leg">
  <div><img src="{headshot(player.get('player_id'),90)}"></div>
  <div class="dd-ticket-player"><b>{index}. {esc(player.get('player_name'))}</b><span>{esc(player.get('team_name'))} vs {esc(player.get('opponent','—'))}</span></div>
  <div class="dd-ticket-metric">{safe_float(player.get('dinger_score')):.1f}<small>Score</small></div>
  <div class="dd-ticket-metric">{percent(player.get('probability'))}<small>HR Prob</small></div>
  <div class="dd-ticket-metric">{odds(player.get('best_odds')) if player.get('best_odds') is not None else odds(player.get('fair_odds'))}<small>{esc(player.get('best_book') or 'Fair Odds')}</small></div>
  <div class="dd-ticket-metric">{safe_int(player.get('last_30_home_runs'))}<small>L30 HR</small></div>
</div>''')
    american_text = f"+{combined_american:.0f}" if combined_american >= 0 else f"{combined_american:.0f}"
    return f'''
<div class="dd-parlay-ticket" style="--accent:{accent}">
  <div class="dd-ticket-head"><div><b>{esc(profile)} Random Dinger Parlay</b><div style="color:#91a6bc;font-size:.68rem">Model-generated combination • {len(picks)} legs</div></div><div style="font-family:Barlow Condensed,sans-serif;font-size:1.65rem;font-weight:900;color:{accent}">{american_text}</div></div>
  {''.join(legs)}
  <div class="dd-ticket-summary">
    <div><b>{combined_probability*100:.3f}%</b><span>Est. Hit Rate</span></div>
    <div><b>{decimal_odds:.2f}x</b><span>Decimal Odds</span></div>
    <div><b>${stake:,.2f}</b><span>Stake</span></div>
    <div><b>${profit:,.2f}</b><span>Est. Profit</span></div>
    <div><b>${total_return:,.2f}</b><span>Total Return</span></div>
  </div>
</div>'''


def board_row_html(rank: int, player: dict[str, Any]) -> str:
    trend, trend_color = trend_label(player)
    rank_class = "gold" if rank == 1 else "silver" if rank == 2 else "bronze" if rank == 3 else ""
    return f'''
<div style="display:grid;grid-template-columns:55px minmax(250px,2.2fr) .75fr .75fr .75fr .75fr .75fr .75fr 1fr;align-items:center;gap:7px;min-height:66px;padding:5px 11px;border:1px solid #11365f;border-top:0;background:linear-gradient(180deg,#061423,#040f1c)">
  <div><span class="dd-rank-badge {rank_class}">{rank}</span></div>
  <div class="dd-player-wrap"><img src="{headshot(player.get('player_id'),120)}"><div class="dd-player-text"><strong>{esc(player.get('player_name'))}</strong><span>{esc(player.get('team_name'))} • vs {esc(player.get('opponent','—'))}</span></div></div>
  <div><span class="dd-score-ring" style="--score-color:{score_color(safe_float(player.get('dinger_score')))}">{safe_float(player.get('dinger_score')):.1f}</span></div>
  <div class="dd-num">{percent(player.get('probability'))}</div><div class="dd-odds">{sportsbook_price(player)}</div>
  <div class="dd-num">{safe_int(player.get('season_home_runs'))}</div><div class="dd-num">{safe_int(player.get('last_7_home_runs'))}</div><div class="dd-num">{safe_int(player.get('last_30_home_runs'))}</div>
  <div style="font-size:.68rem;font-weight:900;color:{trend_color};text-transform:uppercase">{trend}</div>
</div>'''
