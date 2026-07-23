from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from components.navigation import go
from components.ui import hero, percent, probability_fraction, safe_float, safe_int, section, team_cheat_card_html


def render(board: dict) -> None:
    rankings = board.get("rankings", []) or []
    teams: dict[str, list[dict]] = {}
    for player in rankings:
        teams.setdefault(str(player.get("team_name") or "N/A"), []).append(player)
    for players in teams.values():
        players.sort(key=lambda player: safe_float(player.get("dinger_score")), reverse=True)

    hero(
        "DAILY TEAM <span>CHEAT SHEETS</span>",
        "A five-player home-run shortlist for every team on the selected slate. Each sheet combines model probability with real season and rolling power history.",
        stats={"Date": board.get("date", ""), "Teams": len(teams), "Targets": min(len(rankings), len(teams) * 5)},
    )
    if not teams:
        st.info("No team cheat sheets are available for this slate.")
        return

    team_names = sorted(teams)
    selected = st.multiselect("Teams to display", team_names, default=team_names)
    compact = st.toggle("Compact print-style view", value=False)

    heat_rows = []
    for team in team_names:
        top_five = teams[team][:5]
        at_least_one = 1 - math.prod(1 - probability_fraction(player.get("probability")) for player in top_five)
        heat_rows.append({
            "Team": team,
            "Top-5 Avg Score": round(sum(safe_float(player.get("dinger_score")) for player in top_five) / len(top_five), 1),
            "Top-5 At Least One HR": round(at_least_one * 100, 1),
            "Top Target": top_five[0].get("player_name"),
        })
    heat_df = pd.DataFrame(heat_rows).sort_values("Top-5 Avg Score", ascending=False)
    section("Team Stack Heat", "SLATE-WIDE COMPARISON", "Independence estimate—not a guarantee")
    st.dataframe(
        heat_df,
        use_container_width=True,
        hide_index=True,
        column_config={"Top-5 At Least One HR": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100)},
    )

    section("Top Five Targets by Team", "DAILY CHEAT SHEETS", f"{len(selected)} teams selected")
    selected_cards = [team_cheat_card_html(team, teams[team][:5], str(board.get("date", ""))) for team in selected]
    if compact:
        st.markdown("".join(selected_cards), unsafe_allow_html=True)
    else:
        st.markdown('<div class="dd-cheat-grid">' + "".join(selected_cards) + "</div>", unsafe_allow_html=True)

    pick_team = st.selectbox("Open a player from a team sheet", selected or team_names)
    options = teams[pick_team][:5]
    selected_player = st.selectbox("Player", [int(player.get("player_id")) for player in options], format_func=lambda pid: next(player.get("player_name") for player in options if int(player.get("player_id")) == pid))
    if st.button("Open selected player profile", type="primary"):
        go("Player Profile", selected_player)
        st.rerun()

    export_rows = []
    for team in selected:
        for rank, player in enumerate(teams[team][:5], 1):
            export_rows.append({
                "Date": board.get("date"), "Team": team, "Team Rank": rank,
                "Player": player.get("player_name"), "Opponent": player.get("opponent"),
                "Dinger Score": player.get("dinger_score"), "HR Probability": percent(player.get("probability")),
                "Fair Odds": player.get("fair_odds"), "Season HR": safe_int(player.get("season_home_runs")),
                "Last 7 HR": safe_int(player.get("last_7_home_runs")), "Last 15 HR": safe_int(player.get("last_15_home_runs")),
                "Last 30 HR": safe_int(player.get("last_30_home_runs")), "SLG": player.get("season_slg"), "OPS": player.get("season_ops"),
                "Weather Grade": player.get("weather_grade"), "Weather Impact": player.get("weather_impact"),
                "Temperature F": player.get("temperature_f"), "Wind MPH": player.get("wind_speed_mph"),
                "Wind Effect": player.get("wind_field_effect"), "Rain Chance": player.get("precip_probability"),
            })
    export = pd.DataFrame(export_rows)
    st.download_button("Download all selected cheat sheets", export.to_csv(index=False).encode("utf-8"), f"team_hr_cheat_sheets_{board.get('date','today')}.csv", "text/csv", use_container_width=True)
