from __future__ import annotations

import pandas as pd
import streamlit as st

from components.navigation import go
from components.ui import hero, player_card_html, probability_fraction, risk_label, safe_float, safe_int, section


def render(board: dict) -> None:
    rankings = board.get("rankings", []) or []
    hero(
        "PLAYER <span>RANKINGS</span>",
        "Every player card carries real season, last-7, last-15, and last-30 power history. Filter the board and open any profile for the full multi-season view.",
        stats={"Hitters": len(rankings), "Teams": len(board.get("teams", [])), "Games": board.get("games", 0)},
    )
    if not rankings:
        st.info("No rankings are available.")
        return

    teams = sorted({str(player.get("team_name", "N/A")) for player in rankings})
    f1, f2, f3, f4, f5 = st.columns([1.7, 1.25, 1.0, 1.0, 1.15])
    query = f1.text_input("Search player", placeholder="Type a player name...")
    selected_teams = f2.multiselect("Teams", teams)
    min_score = f3.slider("Min score", 0, 100, 0)
    risk_filters = f4.multiselect("Profile", ["Prime", "Strong", "Longshot", "Pipedream"])
    sort_by = f5.selectbox("Sort by", ["Dinger Score", "HR Probability", "Best Sportsbook Odds", "Model Edge", "EV per $10", "Fair Odds", "Season HR", "Last 7 HR", "Last 30 HR", "OPS"])

    filtered = []
    for player in rankings:
        risk, _ = risk_label(player)
        if query.lower() not in str(player.get("player_name", "")).lower():
            continue
        if selected_teams and player.get("team_name") not in selected_teams:
            continue
        if safe_float(player.get("dinger_score")) < min_score:
            continue
        if risk_filters and risk not in risk_filters:
            continue
        filtered.append(player)

    sort_key = {
        "Dinger Score": lambda p: safe_float(p.get("dinger_score")),
        "HR Probability": lambda p: probability_fraction(p.get("probability")),
        "Best Sportsbook Odds": lambda p: safe_float(p.get("best_odds")),
        "Model Edge": lambda p: safe_float(p.get("edge_pct"), -999),
        "EV per $10": lambda p: safe_float(p.get("ev_10"), -999),
        "Fair Odds": lambda p: safe_float(p.get("fair_odds")),
        "Season HR": lambda p: safe_int(p.get("season_home_runs")),
        "Last 7 HR": lambda p: safe_int(p.get("last_7_home_runs")),
        "Last 30 HR": lambda p: safe_int(p.get("last_30_home_runs")),
        "OPS": lambda p: safe_float(p.get("season_ops")),
    }[sort_by]
    filtered.sort(key=sort_key, reverse=True)

    page_size = st.select_slider("Cards shown", options=[8, 12, 16, 24, 40], value=24)
    section(f"{len(filtered)} Hitters", "FILTERED POWER BOARD", f"Sorted by {sort_by} • showing {min(page_size, len(filtered))}")
    visible = filtered[:page_size]
    for start in range(0, len(visible), 4):
        columns = st.columns(4)
        for offset, player in enumerate(visible[start:start + 4]):
            rank = filtered.index(player) + 1
            with columns[offset]:
                st.markdown(player_card_html(player, rank), unsafe_allow_html=True)
                if st.button("Open full profile", key=f"profile_{player.get('player_id')}", use_container_width=True):
                    go("Player Profile", int(player.get("player_id")))
                    st.rerun()

    rows = []
    for player in filtered:
        risk, _ = risk_label(player)
        rows.append({
            "Rank": player.get("overall_rank"),
            "Player": player.get("player_name"),
            "Team": player.get("team_name"),
            "Opponent": player.get("opponent"),
            "Opposing Pitcher": player.get("opposing_pitcher") or "TBD",
            "Pitcher Hand": player.get("opposing_pitcher_hand") or "—",
            "Pitcher HR/9": player.get("pitcher_hr9"),
            "Pitcher ERA": player.get("pitcher_era"),
            "Barrel %": player.get("barrel_pct"),
            "Hard-Hit %": player.get("hard_hit_pct"),
            "Avg Exit Velo": player.get("avg_exit_velocity"),
            "Profile": risk,
            "Dinger Score": safe_float(player.get("dinger_score")),
            "HR Probability": probability_fraction(player.get("probability")),
            "Best Book": player.get("best_book") or "—",
            "Best Odds": player.get("best_odds"),
            "Book Implied Probability": player.get("book_implied_probability"),
            "Model Edge %": player.get("edge_pct"),
            "EV per $10": player.get("ev_10"),
            "Fair Odds": player.get("fair_odds"),
            "Season HR": safe_int(player.get("season_home_runs")),
            "Last 7 HR": safe_int(player.get("last_7_home_runs")),
            "Last 15 HR": safe_int(player.get("last_15_home_runs")),
            "Last 30 HR": safe_int(player.get("last_30_home_runs")),
            "AVG": safe_float(player.get("season_avg")),
            "SLG": safe_float(player.get("season_slg")),
            "OPS": safe_float(player.get("season_ops")),
        })
    export = pd.DataFrame(rows)
    st.download_button("Export filtered rankings CSV", export.to_csv(index=False).encode("utf-8"), f"duggansdingers_rankings_{board.get('date','today')}.csv", "text/csv", use_container_width=True)
