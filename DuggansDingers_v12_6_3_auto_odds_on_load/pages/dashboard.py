from __future__ import annotations

import math

import streamlit as st

from components.navigation import go
from components.ui import (
    bottom_strip,
    feature_grid_html,
    odds,
    percent,
    probability_fraction,
    ranking_table_html,
    safe_float,
    safe_int,
    source_ribbon,
    topbar,
    weather_badge,
)
from services.parlay_engine import combined_decimal_odds, decimal_to_american, generate_parlay


def _best_value(rankings: list[dict]) -> dict:
    priced = [player for player in rankings if player.get("edge_pct") is not None]
    if priced:
        return max(priced, key=lambda player: (safe_float(player.get("edge_pct")), safe_float(player.get("dinger_score"))))

    def signal(player: dict) -> float:
        price = max(0.0, safe_float(player.get("fair_odds")))
        return safe_float(player.get("dinger_score")) * 0.70 + min(price, 700) / 7 * 0.30

    return max(rankings, key=signal)


def render(board: dict) -> None:
    rankings = board.get("rankings", []) or []
    topbar(str(board.get("date", "")))
    source_ribbon(board)
    if not rankings:
        st.error("No rankings are available. Confirm the API key, selected slate date, and internet connection, then refresh.")
        return

    top = rankings[0]
    highest = max(rankings, key=lambda player: probability_fraction(player.get("probability")))
    hottest = max(rankings, key=lambda player: (safe_float(player.get("last_7_hr_rate")), safe_int(player.get("last_7_home_runs"))))
    value = _best_value(rankings)
    park_signal = max(rankings, key=lambda player: safe_float(player.get("ballpark_score")))
    weather_candidates = [player for player in rankings if player.get("weather_available")]
    best_weather = max(weather_candidates, key=lambda player: safe_float(player.get("weather_impact"))) if weather_candidates else park_signal
    parlay_picks = generate_parlay(rankings, "Balanced", 3, unique_teams=True, unique_games=True, seed=17)
    parlay_decimal = combined_decimal_odds(parlay_picks)
    parlay_american = decimal_to_american(parlay_decimal)
    parlay_anchor = parlay_picks[0] if parlay_picks else top

    cards = [
        {"label": "Top Pick", "player": top, "value": f"{safe_float(top.get('dinger_score')):.1f}", "caption": "Dinger Score", "accent": "#ff3038"},
        {"label": "Best Value", "player": value, "value": odds(value.get("best_odds")) if value.get("best_odds") is not None else odds(value.get("fair_odds")), "caption": f"{safe_float(value.get('edge_pct')):+.1f}% Edge" if value.get("edge_pct") is not None else "Model Fair Odds", "accent": "#ffb226", "meta": f"{value.get('best_book')} • Model vs market" if value.get("best_book") else None},
        {"label": "Hottest Bat", "player": hottest, "value": f"{safe_int(hottest.get('last_7_home_runs'))} HR", "caption": "Last 7 Games", "accent": "#9a4dff"},
        {"label": "Highest HR Prob", "player": highest, "value": percent(highest.get("probability")), "caption": "HR Probability", "accent": "#2e91ff"},
        {"label": "Best Weather", "player": best_weather, "value": str(best_weather.get("weather_grade") or "—"), "caption": f"{safe_float(best_weather.get('weather_impact')):+.1f} Weather Impact", "accent": "#35e27e", "name": best_weather.get("venue_name") or best_weather.get("stadium_name") or best_weather.get("player_name"), "meta": weather_badge(best_weather)},
        {"label": "Best Parlay", "player": parlay_anchor, "value": f"+{parlay_american:.0f}" if parlay_american >= 0 else f"{parlay_american:.0f}", "caption": "3-Leg Book/Fair Odds", "accent": "#ff6d20", "name": " • ".join(str(player.get("player_name", "")).split()[-1] for player in parlay_picks), "meta": "Balanced random build"},
    ]
    st.markdown(feature_grid_html(cards), unsafe_allow_html=True)

    action_columns = st.columns(6)
    for column, card in zip(action_columns, cards):
        with column:
            target = "Parlay Lab" if card["label"] == "Best Parlay" else "Player Profile"
            if st.button("Open Lab" if target == "Parlay Lab" else "View Player", key=f"feature_{card['label']}", use_container_width=True):
                player_id = card["player"].get("player_id")
                go(target, int(player_id) if player_id else None)
                st.rerun()

    st.markdown(ranking_table_html(rankings, limit=8), unsafe_allow_html=True)
    st.markdown(bottom_strip(board), unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    if c1.button("Full Rankings", use_container_width=True):
        go("Rankings"); st.rerun()
    if c2.button("Daily Team Cheat Sheets", use_container_width=True):
        go("Team Cheat Sheets"); st.rerun()
    if c3.button("Player Power Profiles", use_container_width=True):
        go("Player Profile"); st.rerun()
    if c4.button("Generate Random Parlay", use_container_width=True, type="primary"):
        go("Parlay Lab"); st.rerun()

    # Quick slate intelligence adds useful context without inventing unconnected data.
    st.markdown('<div class="dd-sectionbar"><div class="dd-sectionbar-title"><span>⚡</span> Slate Intelligence</div><div class="dd-sectionbar-sub">What stands out right now</div></div>', unsafe_allow_html=True)
    teams: dict[str, list[dict]] = {}
    for player in rankings:
        teams.setdefault(str(player.get("team_name") or "N/A"), []).append(player)
    team_heat = []
    for team, players in teams.items():
        top_five = sorted(players, key=lambda player: safe_float(player.get("dinger_score")), reverse=True)[:5]
        at_least_one = 1 - math.prod(1 - probability_fraction(player.get("probability")) for player in top_five)
        team_heat.append((team, sum(safe_float(player.get("dinger_score")) for player in top_five) / len(top_five), at_least_one))
    team_heat.sort(key=lambda row: row[1], reverse=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Hottest Team Stack", team_heat[0][0] if team_heat else "—", f"{team_heat[0][1]:.1f} avg score" if team_heat else None)
    m2.metric("At-Least-One HR Signal", f"{team_heat[0][2]*100:.1f}%" if team_heat else "—", "Top 5 independence estimate")
    m3.metric("Top Individual Price", odds(max(rankings, key=lambda p: safe_float(p.get("best_odds") if p.get("best_odds") is not None else p.get("fair_odds"))).get("best_odds") or max(rankings, key=lambda p: safe_float(p.get("best_odds") if p.get("best_odds") is not None else p.get("fair_odds"))).get("fair_odds")))
    weather_summary = board.get("weather_summary", {}) or {}
    m4.metric("Favorable Weather Games", safe_int(weather_summary.get("favorable_games")), f"{safe_int(weather_summary.get('games_available'))} games connected")
