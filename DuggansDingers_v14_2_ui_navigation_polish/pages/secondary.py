from __future__ import annotations

import secrets

import pandas as pd
import streamlit as st

from components.navigation import go
from components.charts import neon_bar_chart
from components.ui import (
    board_row_html,
    hero,
    odds,
    parlay_ticket_html,
    percent,
    probability_fraction,
    safe_float,
    safe_int,
    section,
    weather_badge,
    weather_color,
)
from services.parlay_engine import (
    PROFILES,
    combined_decimal_odds,
    combined_model_probability,
    decimal_to_american,
    generate_parlay,
    potential_return,
)


def trends(board: dict) -> None:
    rankings = board.get("rankings", []) or []
    hero(
        "TREND <span>CENTER</span>",
        "Find hitters gaining or losing power across seven-game, 30-game, and full-season windows.",
        stats={"Hitters": len(rankings), "Date": board.get("date", "")},
    )
    rows = []
    for player in rankings:
        rows.append({
            "Player": player.get("player_name"),
            "Team": player.get("team_name"),
            "Season HR Rate": safe_float(player.get("season_hr_rate")),
            "Last 30 HR Rate": safe_float(player.get("last_30_hr_rate")),
            "Last 7 HR Rate": safe_float(player.get("last_7_hr_rate")),
            "Last 7 HR": safe_int(player.get("last_7_home_runs")),
            "Last 30 HR": safe_int(player.get("last_30_home_runs")),
            "Change vs Season": safe_float(player.get("last_7_hr_rate")) - safe_float(player.get("season_hr_rate")),
        })
    frame = pd.DataFrame(rows).sort_values("Change vs Season", ascending=False)
    if frame.empty:
        st.info("No trend data is available.")
        return
    top, bottom = st.columns(2)
    with top:
        section("Biggest Risers", "RECENT MOMENTUM")
        st.dataframe(frame.head(12), use_container_width=True, hide_index=True)
    with bottom:
        section("Biggest Fallers", "COOLING OFF")
        st.dataframe(frame.tail(12).sort_values("Change vs Season"), use_container_width=True, hide_index=True)
    section("Seven-Game vs 30-Game vs Season Power", "TOP 20 RISERS")
    neon_bar_chart(frame.head(20).set_index("Player")[["Season HR Rate", "Last 30 HR Rate", "Last 7 HR Rate"]], height=430, value_title="HR Rate")


def matchups(board: dict) -> None:
    rankings = board.get("rankings", []) or []
    hero(
        "MATCHUP <span>CENTER</span>",
        "Today's model board grouped by game. Starting-pitcher, lineup, weather, and Statcast modules can plug into the same cards next.",
        stats={"Games": board.get("games", 0), "Hitters": len(rankings)},
    )
    games: dict[str, list[dict]] = {}
    for player in rankings:
        games.setdefault(str(player.get("game_id", "Unknown")), []).append(player)
    for game_id, players in games.items():
        players.sort(key=lambda item: safe_float(item.get("dinger_score")), reverse=True)
        top_player = players[0]
        teams = sorted({str(player.get("team_name")) for player in players})
        label = " vs ".join(teams[:2]) if len(teams) >= 2 else f"Game {game_id}"
        weather_suffix = weather_badge(top_player) if top_player.get("weather_available") else "Weather unavailable"
        with st.expander(f"{label} • {len(players)} projected hitters • {weather_suffix} • Top: {top_player.get('player_name')}", expanded=len(games) <= 4):
            if top_player.get("weather_available"):
                w1, w2, w3, w4, w5 = st.columns(5)
                w1.metric("Weather Grade", str(top_player.get("weather_grade") or "—"), f"{safe_float(top_player.get('weather_impact')):+.1f} impact")
                w2.metric("Temperature", f"{safe_float(top_player.get('temperature_f')):.0f}°F")
                w3.metric("Wind", f"{safe_float(top_player.get('wind_speed_mph')):.0f} mph", str(top_player.get("wind_field_effect") or "unknown").upper())
                w4.metric("Rain Chance", f"{safe_float(top_player.get('precip_probability')):.0f}%")
                w5.metric("Roof", str(top_player.get("roof_status") or top_player.get("roof_type") or "—").title())
                reasons = " • ".join(top_player.get("weather_reasons") or [])
                st.markdown(f"<div class='dd-weather-line' style='--weather:{weather_color(top_player)}'><b>{weather_badge(top_player)}</b><span>{reasons}</span></div>", unsafe_allow_html=True)
            else:
                st.caption(f"Weather unavailable: {top_player.get('weather_error','No forecast returned')}")
            st.markdown('<div class="dd-board-header"></div>', unsafe_allow_html=True)
            for rank, player in enumerate(players[:12], 1):
                st.markdown(board_row_html(rank, player), unsafe_allow_html=True)
            player_ids = [int(player.get("player_id")) for player in players[:12] if player.get("player_id")]
            selected = st.selectbox("Open matchup hitter", player_ids, key=f"matchup_{game_id}", format_func=lambda player_id: next(player.get("player_name") for player in players if int(player.get("player_id")) == player_id))
            if st.button("Open player profile", key=f"open_matchup_{game_id}"):
                go("Player Profile", selected)
                st.rerun()


def parks(board: dict) -> None:
    rankings = board.get("rankings", []) or []
    hero(
        "PARK <span>SIGNALS</span>",
        "Compare the connected Ballpark Pal projection signal with live Open-Meteo game-time weather. Handedness-specific park factors remain the next data layer.",
        stats={"Teams": len(board.get("teams", [])), "Weather": f"{safe_int((board.get('weather_summary') or {}).get('games_available'))} games"},
    )
    frame = pd.DataFrame([
        {
            "Player": player.get("player_name"),
            "Team": player.get("team_name"),
            "Venue": player.get("venue_name") or "—",
            "Projection Percentile": safe_float(player.get("ballpark_score")),
            "HR Probability": probability_fraction(player.get("probability")) * 100,
            "Dinger Score": safe_float(player.get("dinger_score")),
            "Weather Grade": player.get("weather_grade") or "—",
            "Weather Impact": safe_float(player.get("weather_impact")),
            "Temperature F": safe_float(player.get("temperature_f")),
            "Wind MPH": safe_float(player.get("wind_speed_mph")),
            "Wind Effect": player.get("wind_field_effect") or "—",
        }
        for player in rankings
    ])
    if frame.empty:
        st.info("No park projection inputs are available.")
        return
    team_summary = frame.groupby("Team", as_index=False).agg({"Projection Percentile": "mean", "Dinger Score": "mean", "HR Probability": "mean"}).sort_values("Projection Percentile", ascending=False)
    section("Team Environment Rankings", "CURRENT CONNECTED SIGNAL")
    neon_bar_chart(team_summary.set_index("Team")[["Projection Percentile", "Dinger Score"]], height=390, value_title="Model Score")
    section("All Hitters", "DETAIL")
    st.dataframe(frame.sort_values("Projection Percentile", ascending=False), use_container_width=True, hide_index=True)


def parlay(board: dict) -> None:
    rankings = board.get("rankings", []) or []
    hero(
        "RANDOM PARLAY <span>LAB</span>",
        "Generate diversified home-run combinations by risk profile. Balanced favors stronger grades, Longshot chases bigger prices, and Pipedream targets the highest-payout, least-likely chaos builds.",
        stats={"Players": len(rankings), "Profiles": 3, "Max Legs": 8},
    )
    if not rankings:
        st.info("No player board is available.")
        return

    mode_columns = st.columns(3)
    colors = {"Balanced": "#35e27e", "Longshot": "#ffbd2f", "Pipedream": "#ff573d"}
    for column, (name, profile) in zip(mode_columns, PROFILES.items()):
        with column:
            st.markdown(f'<div class="dd-parlay-mode" style="--accent:{colors[name]}"><b>{name}</b><span>{profile.description}</span></div>', unsafe_allow_html=True)

    mode = st.radio("Risk profile", list(PROFILES), horizontal=True, index=0)
    teams = sorted({str(player.get("team_name")) for player in rankings})
    controls1 = st.columns([1, 1, 1, 1])
    legs = controls1[0].slider("Legs", 2, 8, 3)
    stake = controls1[1].number_input("Stake ($)", min_value=1.0, max_value=10000.0, value=10.0, step=5.0)
    default_min = int(PROFILES[mode].min_score)
    min_score = controls1[2].slider("Minimum Dinger Score", 0, 95, default_min)
    selected_teams = controls1[3].multiselect("Team pool", teams, placeholder="All teams")

    controls2 = st.columns([1, 1, 2])
    unique_teams = controls2[0].toggle("Max one player per team", value=True)
    unique_games = controls2[1].toggle("Max one player per game", value=True)
    lock_options = [int(player.get("player_id")) for player in rankings[:60] if player.get("player_id")]
    locked = controls2[2].multiselect(
        "Lock players before generating (optional)",
        lock_options,
        max_selections=legs,
        format_func=lambda player_id: next(f"{player.get('player_name')} ({player.get('team_name')})" for player in rankings if int(player.get("player_id")) == player_id),
    )

    generate_column, reroll_column, clear_column = st.columns([1.4, 1, 1])
    generate_clicked = generate_column.button("⚡ Generate Random Parlay", type="primary", use_container_width=True)
    reroll_clicked = reroll_column.button("↻ Reroll", use_container_width=True)
    clear_clicked = clear_column.button("Clear ticket", use_container_width=True)
    if clear_clicked:
        st.session_state.generated_parlay = []
        st.rerun()

    if generate_clicked or reroll_clicked:
        picks = generate_parlay(
            rankings,
            mode,
            legs,
            min_score_override=min_score,
            selected_teams=set(selected_teams),
            unique_teams=unique_teams,
            unique_games=unique_games,
            locked_player_ids=set(locked),
            seed=secrets.randbits(32),
        )
        st.session_state.generated_parlay = [int(player.get("player_id")) for player in picks if player.get("player_id")]
        st.session_state.generated_parlay_mode = mode
        st.session_state.generated_parlay_stake = stake

    selected_ids = st.session_state.get("generated_parlay", [])
    picks = [player for player_id in selected_ids for player in rankings if int(player.get("player_id") or -1) == int(player_id)]
    if picks:
        active_mode = st.session_state.get("generated_parlay_mode", mode)
        active_stake = float(st.session_state.get("generated_parlay_stake", stake))
        decimal_odds = combined_decimal_odds(picks)
        combined_probability = combined_model_probability(picks)
        combined_american = decimal_to_american(decimal_odds)
        profit, total_return = potential_return(decimal_odds, active_stake)
        st.markdown(
            parlay_ticket_html(picks, active_mode, combined_probability, combined_american, decimal_odds, active_stake, profit, total_return),
            unsafe_allow_html=True,
        )

        if len(picks) < legs:
            st.warning(f"Only {len(picks)} eligible legs were available with the current restrictions. Relax team/game uniqueness or lower the minimum score.")
        if active_mode == "Pipedream":
            st.markdown('<div class="dd-disclaimer"><strong>PIPEDREAM MODE:</strong> This intentionally favors extreme prices and low hit probability. The payout can be enormous because the chance of the entire ticket hitting is very small.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="dd-disclaimer">Combined estimates assume independent outcomes. Connected sportsbook prices are used when available; model fair odds fill any missing legs. Treat this as research, not a guarantee.</div>', unsafe_allow_html=True)

        export = pd.DataFrame([
            {
                "Profile": active_mode,
                "Player": player.get("player_name"),
                "Team": player.get("team_name"),
                "Opponent": player.get("opponent"),
                "Dinger Score": player.get("dinger_score"),
                "HR Probability": percent(player.get("probability")),
                "Best Book": player.get("best_book") or "Model",
                "Best/Model Odds": odds(player.get("best_odds")) if player.get("best_odds") is not None else odds(player.get("fair_odds")),
                "Edge %": player.get("edge_pct"),
                "Season HR": player.get("season_home_runs"),
                "Last 7 HR": player.get("last_7_home_runs"),
                "Last 30 HR": player.get("last_30_home_runs"),
            }
            for player in picks
        ])
        st.download_button("Download this ticket", export.to_csv(index=False).encode("utf-8"), f"{active_mode.lower()}_hr_parlay_{board.get('date','today')}.csv", "text/csv", use_container_width=True)
    else:
        st.markdown('<div class="dd-empty">Choose a profile and click Generate Random Parlay. Use locks and filters to control the chaos.</div>', unsafe_allow_html=True)

    with st.expander("Manual parlay builder"):
        names = [str(player.get("player_name")) for player in rankings[:80]]
        manual = st.multiselect("Choose 2 to 8 hitters", names, max_selections=8)
        if len(manual) >= 2:
            manual_players = [next(player for player in rankings if player.get("player_name") == name) for name in manual]
            decimal_odds = combined_decimal_odds(manual_players)
            model_probability = combined_model_probability(manual_players)
            american = decimal_to_american(decimal_odds)
            profit, total_return = potential_return(decimal_odds, stake)
            st.markdown(parlay_ticket_html(manual_players, "Custom", model_probability, american, decimal_odds, stake, profit, total_return), unsafe_allow_html=True)


def sportsbook_odds(board: dict) -> None:
    from services.odds import ODDS_FILE, template_csv, write_uploaded_odds

    rankings = board.get("rankings", []) or []
    summary = board.get("odds_summary", {}) or {}
    hero(
        "SPORTSBOOK <span>ODDS</span>",
        "Live MLB home-run prices load automatically and match to the Dinger Board. Odds load automatically when the site opens. The manual refresh and CSV import remain available only as backups.",
        stats={
            "Live Offers": safe_int(summary.get("live_records")),
            "Matched": safe_int(summary.get("matched_players")),
            "Positive Edges": safe_int(summary.get("positive_edges")),
        },
    )

    status = str(summary.get("api_status") or "Odds API key not configured")
    live_count = safe_int(summary.get("live_records"))
    if live_count:
        st.success(f"Odds-API.io connected: {status}")
    elif summary.get("connected"):
        st.warning(status)
    else:
        st.info("Live odds load automatically when the site opens. The app retries empty results automatically; no button press is required.")

    # Show a persistent result after refresh. Toasts were too easy to miss and
    # made the button appear to do nothing.
    refresh_result = st.session_state.pop("odds_refresh_result", None)
    if refresh_result:
        message = str(refresh_result.get("message") or "Live odds refresh completed.")
        if refresh_result.get("connected"):
            st.success(message)
        else:
            st.error(message)

    a, b, c = st.columns([1.2, 1, 1])
    with a:
        if st.button("⚡ Refresh Live Odds", type="primary", use_container_width=True):
            # Clear only the board cache, rerun, and then display the API result
            # as a persistent banner on the refreshed page.
            from data_service import load_board
            from services.odds import clear_live_odds_cache

            clear_live_odds_cache()
            load_board.clear()
            st.session_state["odds_refresh_pending"] = True
            st.rerun()

    if st.session_state.pop("odds_refresh_pending", False):
        st.session_state["odds_refresh_result"] = {
            "connected": bool(summary.get("connected")),
            "message": (
                f"Refresh finished for {board.get('date', 'the selected slate')}: "
                f"{summary.get('api_status') or 'No API status returned'} "
                f"({safe_int(summary.get('api_events'))} MLB events checked, "
                f"{safe_int(summary.get('live_records'))} HR offers found)."
            ),
        }
        st.rerun()
    with b:
        st.metric("MLB Events Checked", safe_int(summary.get("api_events")))
    with c:
        st.metric("Live HR Offers", live_count)

    with st.expander("Manual CSV backup", expanded=False):
        st.caption("Use this only when a sportsbook is missing from the live feed or props have not been posted yet.")
        left, right = st.columns([1.3, 1])
        with left:
            uploaded = st.file_uploader("Upload sportsbook HR odds CSV", type=["csv"], help="Required columns: date, player_name, team, book, american_odds. player_id and game_id are optional.")
            if uploaded is not None and st.button("Save CSV odds and refresh", use_container_width=True):
                write_uploaded_odds(uploaded.getvalue())
                st.cache_data.clear()
                st.rerun()
        with right:
            st.download_button(
                "Download CSV template",
                template_csv(),
                "duggansdingers_odds_template.csv",
                "text/csv",
                use_container_width=True,
            )
            if st.button("Clear manual CSV odds", use_container_width=True):
                ODDS_FILE.write_text("date,player_id,player_name,team,book,american_odds,game_id\n", encoding="utf-8")
                st.cache_data.clear()
                st.rerun()

    books = summary.get("books") or []
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Offers", safe_int(summary.get("records")))
    c2.metric("Players Matched", safe_int(summary.get("matched_players")), f"{safe_int(summary.get('unmatched_records'))} unmatched")
    c3.metric("Books", len(books), ", ".join(books[:3]) if books else "Waiting for props")
    c4.metric("Positive Model Edges", safe_int(summary.get("positive_edges")))

    priced = [player for player in rankings if player.get("best_odds") is not None]
    if not priced:
        st.info("The connection is automatic. When the books return MLB home-run props, they will appear here when the page loads. Empty results retry automatically; no PowerShell commands or button press are needed.")
        return

    section("Best Value Edges", "MODEL VS MARKET", "Positive edge means the model probability is higher than the sportsbook implied probability")
    rows = []
    for player in sorted(priced, key=lambda p: safe_float(p.get("edge_pct")), reverse=True):
        rows.append({
            "Player": player.get("player_name"),
            "Team": player.get("team_name"),
            "Opponent": player.get("opponent"),
            "Book": player.get("best_book"),
            "Best Odds": player.get("best_odds"),
            "Model Probability": probability_fraction(player.get("probability")),
            "Book Implied Probability": safe_float(player.get("book_implied_probability")),
            "Edge %": safe_float(player.get("edge_pct")),
            "EV per $10": safe_float(player.get("ev_10")),
            "Dinger Score": safe_float(player.get("dinger_score")),
        })
    frame = pd.DataFrame(rows)
    st.dataframe(
        frame,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Best Odds": st.column_config.NumberColumn(format="%+.0f"),
            "Model Probability": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=1),
            "Book Implied Probability": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=1),
            "Edge %": st.column_config.NumberColumn(format="%+.1f%%"),
            "EV per $10": st.column_config.NumberColumn(format="$%+.2f"),
            "Dinger Score": st.column_config.NumberColumn(format="%.1f"),
        },
    )
    st.download_button(
        "Export matched odds and value edges",
        frame.to_csv(index=False).encode("utf-8"),
        f"duggansdingers_odds_edges_{board.get('date','today')}.csv",
        "text/csv",
        use_container_width=True,
    )


def _field_zone_values(player: dict) -> tuple[int, int, int]:
    impact = safe_float(player.get("weather_impact"))
    speed = safe_float(player.get("wind_speed_mph"))
    direction = str(player.get("wind_field_effect") or "cross").lower()
    base = max(-18, min(18, round(impact * 1.8)))
    cross = min(8, round(speed * 0.35))
    if direction == "out":
        return base + cross // 2, base + cross, base + cross // 2
    if direction == "in":
        return base - cross // 2, base - cross, base - cross // 2
    wind_deg = safe_float(player.get("wind_direction_deg"))
    if 0 <= wind_deg < 180:
        return base + cross, base, base - cross
    return base - cross, base, base + cross


def _stadium_weather_card(player: dict) -> str:
    team = str(player.get("team_name") or "MLB")
    stadium = str(player.get("stadium_name") or player.get("venue_name") or "Ballpark")
    lf, cf, rf = _field_zone_values(player)
    wind = safe_float(player.get("wind_speed_mph"))
    temp = safe_float(player.get("temperature_f"))
    rain = safe_float(player.get("precip_probability"))
    impact = safe_float(player.get("weather_impact"))
    grade_value = str(player.get("weather_grade") or "—")
    direction = str(player.get("wind_field_effect") or "unknown").upper()
    angle = (safe_float(player.get("wind_direction_deg")) + 180) % 360
    accent = weather_color(player)
    def signed(value: int) -> str:
        return f"+{value}%" if value > 0 else f"{value}%"
    return f"""
<div class="dd-weather-card" style="--weather:{accent}">
  <div class="dd-weather-card-head">
    <div><span>{team}</span><h3>{stadium}</h3></div>
    <div class="dd-weather-grade">{grade_value}<small>HR WEATHER</small></div>
  </div>
  <div class="dd-ballpark">
    <div class="dd-outfield-arc"></div>
    <div class="dd-infield"></div>
    <div class="dd-diamond"></div>
    <div class="dd-homeplate"></div>
    <div class="dd-zone dd-zone-lf"><b>{signed(lf)}</b><small>LF</small></div>
    <div class="dd-zone dd-zone-cf"><b>{signed(cf)}</b><small>CF</small></div>
    <div class="dd-zone dd-zone-rf"><b>{signed(rf)}</b><small>RF</small></div>
    <div class="dd-wind-arrow" style="transform:translateX(-50%) rotate({angle:.0f}deg)">➤</div>
  </div>
  <div class="dd-weather-metrics">
    <div><b>{temp:.0f}°</b><span>Temperature</span></div>
    <div><b>{wind:.0f} mph</b><span>Wind {direction}</span></div>
    <div><b>{rain:.0f}%</b><span>Rain Chance</span></div>
    <div><b>{impact:+.1f}</b><span>HR Impact</span></div>
  </div>
</div>
"""


def weather_center(board: dict) -> None:
    rankings = board.get("rankings", []) or []
    game_weather: dict[str, dict] = {}
    for meta in board.get("games_meta", []) or []:
        if not meta.get("weather_available"):
            continue
        key = str(meta.get("game_id") or meta.get("stadium_name") or meta.get("home_team_name"))
        game_weather.setdefault(key, meta)
    for player in rankings:
        if not player.get("weather_available"):
            continue
        key = str(player.get("game_id") or player.get("stadium_name") or player.get("team_name"))
        game_weather.setdefault(key, player)

    hero(
        "BALLPARK <span>WEATHER COMMAND</span>",
        "Original stadium-specific wind intelligence showing where the air is helping or suppressing home-run carry in left, center, and right field.",
        stats={"Games Connected": len(game_weather), "Slate": board.get("date", ""), "Source": "Open-Meteo"},
    )
    if not game_weather:
        summary = board.get("weather_summary", {}) or {}
        errors = summary.get("errors", []) or []
        st.info("No connected outdoor weather games are available for this slate.")
        if errors:
            with st.expander("Weather connection details"):
                for error in errors:
                    st.code(str(error))
        return

    cards = [_stadium_weather_card(player) for player in game_weather.values()]
    st.markdown('<div class="dd-weather-grid">' + "".join(cards) + "</div>", unsafe_allow_html=True)

    section("Weather-Adjusted Hitter Board", "WIND + TEMPERATURE + RAIN", "Sorted by weather impact")
    weather_players = sorted(
        [player for player in rankings if player.get("weather_available")],
        key=lambda player: (safe_float(player.get("weather_impact")), safe_float(player.get("dinger_score"))),
        reverse=True,
    )
    rows = []
    for player in weather_players:
        lf, cf, rf = _field_zone_values(player)
        rows.append({
            "Player": player.get("player_name"),
            "Team": player.get("team_name"),
            "Ballpark": player.get("stadium_name") or player.get("venue_name"),
            "Weather Grade": player.get("weather_grade"),
            "HR Impact": safe_float(player.get("weather_impact")),
            "Temperature": safe_float(player.get("temperature_f")),
            "Wind MPH": safe_float(player.get("wind_speed_mph")),
            "Wind Effect": str(player.get("wind_field_effect") or "unknown").upper(),
            "LF": lf,
            "CF": cf,
            "RF": rf,
            "Dinger Score": safe_float(player.get("dinger_score")),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
