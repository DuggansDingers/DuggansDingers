from __future__ import annotations

import pandas as pd
import requests
import streamlit as st

from components.ui import (
    odds,
    percent,
    player_reasons,
    profile_banner,
    safe_float,
    safe_int,
    section,
    trend_label,
    weather_badge,
    weather_color,
)
from services.player_history import get_year_by_year_history


def render(board: dict) -> None:
    rankings = board.get("rankings", []) or []
    if not rankings:
        st.info("No players are available.")
        return

    players_by_id = {int(player.get("player_id")): player for player in rankings if player.get("player_id")}
    default_id = st.session_state.get("selected_player_id")
    if default_id not in players_by_id:
        default_id = next(iter(players_by_id))

    selector, favorite_column = st.columns([4, 1])
    with selector:
        choices = list(players_by_id)
        selected = st.selectbox(
            "Choose a player",
            choices,
            index=choices.index(default_id),
            format_func=lambda player_id: f"{players_by_id[player_id].get('player_name')} — {players_by_id[player_id].get('team_name')} vs {players_by_id[player_id].get('opponent','—')}",
        )
    with favorite_column:
        st.write("")
        favorites = set(st.session_state.get("favorites", []))
        label = "★ Favorited" if selected in favorites else "☆ Add favorite"
        if st.button(label, use_container_width=True):
            if selected in favorites:
                favorites.remove(selected)
            else:
                favorites.add(selected)
            st.session_state.favorites = sorted(favorites)
            st.rerun()

    st.session_state.selected_player_id = selected
    player = players_by_id[selected]
    profile_banner(player)
    st.write("")

    metrics = [
        ("HR Probability", percent(player.get("probability"))),
        ("Best Sportsbook Odds", odds(player.get("best_odds")) if player.get("best_odds") is not None else "—"),
        ("Best Book", player.get("best_book") or "—"),
        ("Model Edge", f"{safe_float(player.get('edge_pct')):+.1f}%" if player.get("edge_pct") is not None else "—"),
        ("EV per $10", f"${safe_float(player.get('ev_10')):+.2f}" if player.get("ev_10") is not None else "—"),
        ("Fair Odds", odds(player.get("fair_odds"))),
        ("Season HR", safe_int(player.get("season_home_runs"))),
        ("Last 7 HR", safe_int(player.get("last_7_home_runs"))),
        ("Last 15 HR", safe_int(player.get("last_15_home_runs"))),
        ("Last 30 HR", safe_int(player.get("last_30_home_runs"))),
        ("AVG", f"{safe_float(player.get('season_avg')):.3f}" if safe_float(player.get("season_avg")) else "—"),
        ("SLG", f"{safe_float(player.get('season_slg')):.3f}" if safe_float(player.get("season_slg")) else "—"),
        ("OPS", f"{safe_float(player.get('season_ops')):.3f}" if safe_float(player.get("season_ops")) else "—"),
        ("Barrel %", f"{safe_float(player.get('barrel_pct')):.1f}%" if player.get("statcast_available") else "—"),
        ("Hard-Hit %", f"{safe_float(player.get('hard_hit_pct')):.1f}%" if player.get("statcast_available") else "—"),
        ("Avg Exit Velo", f"{safe_float(player.get('avg_exit_velocity')):.1f} mph" if player.get("statcast_available") else "—"),
    ]
    for start in range(0, len(metrics), 5):
        columns = st.columns(min(5, len(metrics) - start))
        for column, (label, value) in zip(columns, metrics[start:start + 5]):
            column.metric(label, value)

    section("Statcast & Pitching Matchup", "CONTACT QUALITY + OPPOSING STARTER", "Live probable pitcher with season and Statcast contact profile")
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("Opposing Pitcher", player.get("opposing_pitcher") or "TBD", f"{player.get('opposing_pitcher_hand','—')}HP")
    s2.metric("Pitcher HR/9", f"{safe_float(player.get('pitcher_hr9')):.2f}" if player.get("pitching_data_available") else "—")
    s3.metric("Pitcher ERA", f"{safe_float(player.get('pitcher_era')):.2f}" if player.get("pitching_data_available") else "—")
    s4.metric("Pitcher Barrel %", f"{safe_float(player.get('pitcher_barrel_pct')):.1f}%" if player.get("pitcher_barrel_pct") else "—")
    s5.metric("Pitcher Hard-Hit %", f"{safe_float(player.get('pitcher_hard_hit_pct')):.1f}%" if player.get("pitcher_hard_hit_pct") else "—")
    if not player.get("statcast_available"):
        st.caption("Statcast leaderboard data is unavailable for this player or the optional pybaseball package has not been installed yet.")

    section("Game-Time Weather", "OPEN-METEO LIVE FORECAST", "Forecast matched to scheduled first pitch")
    if player.get("weather_available"):
        w1, w2, w3, w4, w5 = st.columns(5)
        w1.metric("Weather Grade", str(player.get("weather_grade") or "—"), f"{safe_float(player.get('weather_impact')):+.1f} impact")
        w2.metric("Temperature", f"{safe_float(player.get('temperature_f')):.0f}°F")
        w3.metric("Wind", f"{safe_float(player.get('wind_speed_mph')):.0f} mph", str(player.get("wind_field_effect") or "unknown").upper())
        w4.metric("Rain Chance", f"{safe_float(player.get('precip_probability')):.0f}%")
        w5.metric("Roof", str(player.get("roof_status") or player.get("roof_type") or "—").title())
        reasons = "".join(f"<li>{reason}</li>" for reason in (player.get("weather_reasons") or []))
        st.markdown(f"<div class='dd-insight' style='border-color:{weather_color(player)}'><strong>{weather_badge(player)}</strong><ul>{reasons}</ul><div style='color:#8fa7c0;font-size:.68rem'>Source: Open-Meteo • Forecast time: {player.get('weather_time_local','—')}</div></div>", unsafe_allow_html=True)
        if str(player.get("roof_type")) == "retractable":
            st.warning("Retractable roof status is unconfirmed. Weather is shown as an outdoor scenario until roof status is entered or confirmed.")
    else:
        st.info(f"Weather is unavailable for this matchup: {player.get('weather_error','No forecast returned')}")

    left, right = st.columns([1.45, 1])
    with left:
        section("Model Component Breakdown", "WHY THE SCORE MOVED")
        breakdown = pd.DataFrame({
            "Component": ["Projection", "Season Power", "Last-7 Power", "Last-30 Power", "Slugging Power", "Statcast Power", "Pitcher Matchup"],
            "Percentile": [
                safe_float(player.get("ballpark_score")),
                safe_float(player.get("season_power_score")),
                safe_float(player.get("recent_power_score")),
                safe_float(player.get("month_power_score")),
                safe_float(player.get("slug_power_score")),
                safe_float(player.get("statcast_power_score")),
                safe_float(player.get("pitcher_matchup_score")),
            ],
        }).set_index("Component")
        st.bar_chart(breakdown, height=330)
    with right:
        section("Why He Ranks Here", "MODEL READ")
        trend, _ = trend_label(player)
        bullets = "".join(f"<li>{reason}</li>" for reason in player_reasons(player))
        st.markdown(
            f"<div class='dd-insight'><strong>{player.get('player_name')}</strong><div style='margin-top:5px;color:#38c7ff;font-weight:900'>{trend} POWER PROFILE</div><ul>{bullets}</ul></div>",
            unsafe_allow_html=True,
        )

    section("Rolling Power Windows", "RECENT HISTORY", "Home runs and HR rate by game window")
    rolling = pd.DataFrame({
        "Window": ["Last 7", "Last 15", "Last 30", "Season"],
        "Home Runs": [
            safe_int(player.get("last_7_home_runs")),
            safe_int(player.get("last_15_home_runs")),
            safe_int(player.get("last_30_home_runs")),
            safe_int(player.get("season_home_runs")),
        ],
        "HR Rate %": [
            safe_float(player.get("last_7_hr_rate")),
            safe_float(player.get("last_15_hr_rate")),
            safe_float(player.get("last_30_hr_rate")),
            safe_float(player.get("season_hr_rate")),
        ],
    }).set_index("Window")
    c1, c2 = st.columns(2)
    c1.bar_chart(rolling[["Home Runs"]], height=290)
    c2.line_chart(rolling[["HR Rate %"]], height=290)

    recent_series = player.get("recent_game_hr_series") or []
    recent_dates = player.get("recent_game_dates") or []
    if recent_series:
        section("Recent Game-by-Game HR Pulse", "LAST 15 GAMES")
        pulse = pd.DataFrame({"Date": recent_dates[-len(recent_series):], "Home Runs": recent_series}).set_index("Date")
        st.bar_chart(pulse, height=240)

    section("Career / Multi-Season History", "HISTORICAL POWER", "Pulled on demand from MLB Stats")
    try:
        history = get_year_by_year_history(selected)
    except requests.RequestException as error:
        history = []
        st.warning(f"Historical MLB data could not be loaded right now: {error}")

    if history:
        history_df = pd.DataFrame(history)
        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "AVG": st.column_config.NumberColumn(format="%.3f"),
                "OBP": st.column_config.NumberColumn(format="%.3f"),
                "SLG": st.column_config.NumberColumn(format="%.3f"),
                "OPS": st.column_config.NumberColumn(format="%.3f"),
            },
        )
        season_totals = history_df.groupby("Season", as_index=True)[["HR", "RBI", "G"]].sum().sort_index()
        st.bar_chart(season_totals[["HR"]], height=310)
    else:
        st.markdown('<div class="dd-empty">No year-by-year history was returned for this player.</div>', unsafe_allow_html=True)

    section("Board Context", "HOW HE COMPARES")
    board_average = sum(safe_float(item.get("dinger_score")) for item in rankings) / len(rankings)
    same_team = [item for item in rankings if item.get("team_name") == player.get("team_name")]
    team_rank = next((index for index, item in enumerate(sorted(same_team, key=lambda row: safe_float(row.get("dinger_score")), reverse=True), 1) if item.get("player_id") == player.get("player_id")), None)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overall Rank", f"#{safe_int(player.get('overall_rank'))}")
    c2.metric("Team Rank", f"#{team_rank}" if team_rank else "—")
    c3.metric("Score vs Board Avg", f"{safe_float(player.get('dinger_score')) - board_average:+.1f}")
    c4.metric("L7 vs Season HR Rate", f"{safe_float(player.get('last_7_hr_rate')) - safe_float(player.get('season_hr_rate')):+.2f}%")

    with st.expander("Stadium background setup"):
        st.caption(f"Place a stadium image at assets/stadiums/{player.get('team_name')}.jpg and this player page automatically uses it as the hero background.")
