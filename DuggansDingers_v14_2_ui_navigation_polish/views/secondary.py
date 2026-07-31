from __future__ import annotations

import secrets
from urllib.parse import quote

import pandas as pd
import streamlit as st

from components.navigation import go
from components.charts import neon_bar_chart
from components.neon_table import Column, progress_html, render_neon_table
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
    esc,
    team_logo,
)
from services.parlay_engine import (
    PROFILES,
    combined_decimal_odds,
    combined_model_probability,
    decimal_to_american,
    generate_parlay,
    generate_blended_parlay,
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
    trend_columns = [
        Column("Player", "Player", width="1.4fr"),
        Column("Team", "Team", width=".55fr", align="center"),
        Column("Last 7 HR", "L7 HR", progress_max=5, accent="#35f29a", width="1fr"),
        Column("Last 30 HR", "L30 HR", progress_max=10, accent="#ff4df2", width="1fr"),
        Column("Change vs Season", "Δ vs Season", formatter=lambda v, r: f'<b style="color:{"#35f29a" if safe_float(v)>=0 else "#ff5f6d"}">{safe_float(v):+.2f}</b>', width=".8fr", align="center"),
    ]
    with top:
        section("Biggest Risers", "RECENT MOMENTUM")
        render_neon_table(frame.head(12).to_dict("records"), trend_columns, key="trend_risers")
    with bottom:
        section("Biggest Fallers", "COOLING OFF")
        render_neon_table(frame.tail(12).sort_values("Change vs Season").to_dict("records"), trend_columns, key="trend_fallers")
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
        "Compare the connected Ballpark Pal projection signal with multi-provider live game-time weather. Handedness-specific park factors remain the next data layer.",
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
    park_columns = [
        Column("Player", "Player", width="1.4fr"),
        Column("Team", "Team", width=".55fr", align="center"),
        Column("Venue", "Ballpark", width="1.25fr"),
        Column("Projection Percentile", "Projection", progress_max=100, accent="#27c7ff", width="1.15fr"),
        Column("Dinger Score", "Dinger Score", progress_max=100, accent="#ff4df2", width="1.15fr"),
        Column("HR Probability", "HR Probability", progress_max=35, accent="#35f29a", width="1.15fr"),
        Column("Weather Grade", "Weather", width=".65fr", align="center"),
        Column("Weather Impact", "HR Impact", formatter=lambda v, r: f'<b style="color:{"#35f29a" if safe_float(v)>=0 else "#ff5f6d"}">{safe_float(v):+.1f}</b>', width=".7fr", align="center"),
    ]
    render_neon_table(frame.sort_values("Projection Percentile", ascending=False).to_dict("records"), park_columns, key="park_detail", max_height=620)


def parlay(board: dict) -> None:
    rankings = board.get("rankings", []) or []
    hero(
        "PARLAY <span>LAB</span>",
        "Build a ticket, lock any legs you love, then reroll only the unlocked spots. Blend mode mixes high-probability anchors with true long-price upside.",
        stats={"Players": len(rankings), "Modes": 4, "Max Legs": 8},
    )
    if not rankings:
        st.info("No player board is available.")
        return

    st.session_state.setdefault("generated_parlay", [])
    st.session_state.setdefault("parlay_locked_ids", [])

    profile_cards = [
        ("Balanced", "Stronger model grades with payout upside.", "#32f6a6"),
        ("Longshot", "Bigger prices that still clear the minimum score.", "#ffd83d"),
        ("Pipedream", "Extreme prices and intentionally low combined hit rate.", "#ff5f6d"),
        ("Blend", "Choose exactly how many high-probability and long-price legs to mix.", "#ff4df2"),
    ]
    columns = st.columns(4)
    for column, (name, description, color) in zip(columns, profile_cards):
        with column:
            st.markdown(
                f'<div class="dd-parlay-mode v15" style="--accent:{color}"><b>{name}</b><span>{description}</span></div>',
                unsafe_allow_html=True,
            )

    mode = st.radio("Build style", [item[0] for item in profile_cards], horizontal=True, index=0)
    teams = sorted({str(player.get("team_name")) for player in rankings})
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1.5])
    legs = c1.slider("Legs", 2, 8, 3)
    stake = c2.number_input("Stake ($)", min_value=1.0, max_value=10000.0, value=10.0, step=5.0)
    default_min = 55 if mode == "Blend" else int(PROFILES[mode].min_score)
    min_score = c3.slider("Minimum Dinger Score", 0, 95, default_min)
    selected_teams = c4.multiselect("Team pool", teams, placeholder="All teams")

    d1, d2, d3 = st.columns([1, 1, 2])
    unique_teams = d1.toggle("Max one per team", value=True)
    unique_games = d2.toggle("Max one per game", value=True)
    longshot_legs = 0
    if mode == "Blend":
        longshot_legs = d3.slider("Long-price legs", 0, legs, max(1, legs // 2), help="The remaining legs come from the higher-probability anchor pool.")
    else:
        d3.markdown('<div class="dd-inline-note"><b>MODEL TIER ≠ BETTING PRICE</b><span>An Elite score never becomes a Longshot label just because its sportsbook price is large.</span></div>', unsafe_allow_html=True)

    prelock_options = [int(player.get("player_id")) for player in rankings[:60] if player.get("player_id")]
    prelocked = st.multiselect(
        "Optional locks before the first build",
        prelock_options,
        max_selections=legs,
        format_func=lambda pid: next(f"{p.get('player_name')} ({p.get('team_name')})" for p in rankings if int(p.get("player_id")) == pid),
    )

    generate_col, reroll_col, clear_col = st.columns([1.45, 1.25, 1])
    generate_clicked = generate_col.button("⚡ Generate New Ticket", type="primary", use_container_width=True)
    reroll_clicked = reroll_col.button("↻ Reroll Unlocked Legs", use_container_width=True, disabled=not bool(st.session_state.generated_parlay))
    clear_clicked = clear_col.button("Clear Ticket", use_container_width=True)

    if clear_clicked:
        st.session_state.generated_parlay = []
        st.session_state.parlay_locked_ids = []
        st.rerun()

    current_ids = [int(value) for value in st.session_state.get("generated_parlay", [])]
    current_locks = {int(value) for value in st.session_state.get("parlay_locked_ids", [])}
    locked_ids = set(prelocked) if generate_clicked else current_locks

    if generate_clicked or reroll_clicked:
        if mode == "Blend":
            picks = generate_blended_parlay(
                rankings,
                legs,
                longshot_legs,
                min_score_override=min_score,
                selected_teams=set(selected_teams),
                unique_teams=unique_teams,
                unique_games=unique_games,
                locked_player_ids=locked_ids,
                seed=secrets.randbits(32),
            )
        else:
            picks = generate_parlay(
                rankings,
                mode,
                legs,
                min_score_override=min_score,
                selected_teams=set(selected_teams),
                unique_teams=unique_teams,
                unique_games=unique_games,
                locked_player_ids=locked_ids,
                seed=secrets.randbits(32),
            )
        st.session_state.generated_parlay = [int(player.get("player_id")) for player in picks if player.get("player_id")]
        st.session_state.parlay_locked_ids = sorted(locked_ids & set(st.session_state.generated_parlay))
        st.session_state.generated_parlay_mode = mode
        st.session_state.generated_parlay_stake = stake
        st.rerun()

    selected_ids = [int(value) for value in st.session_state.get("generated_parlay", [])]
    picks = [next((p for p in rankings if int(p.get("player_id") or -1) == player_id), None) for player_id in selected_ids]
    picks = [p for p in picks if p]
    if not picks:
        st.markdown('<div class="dd-empty">Choose a build style and generate a ticket. After it appears, lock the legs you want to keep and reroll everything else.</div>', unsafe_allow_html=True)
        return

    active_mode = str(st.session_state.get("generated_parlay_mode", mode))
    active_stake = float(st.session_state.get("generated_parlay_stake", stake))
    decimal_odds = combined_decimal_odds(picks)
    combined_probability = combined_model_probability(picks)
    combined_american = decimal_to_american(decimal_odds)
    profit, total_return = potential_return(decimal_odds, active_stake)
    st.markdown(
        parlay_ticket_html(picks, active_mode, combined_probability, combined_american, decimal_odds, active_stake, profit, total_return),
        unsafe_allow_html=True,
    )

    section("Lock Individual Legs", "KEEP WHAT YOU LIKE", "Checked players survive the next reroll")
    lock_columns = st.columns(min(4, len(picks)))
    new_locks: list[int] = []
    for index, player in enumerate(picks):
        player_id = int(player.get("player_id") or -1)
        with lock_columns[index % len(lock_columns)]:
            checked = st.checkbox(
                f"🔒 {player.get('player_name')}",
                value=player_id in set(st.session_state.get("parlay_locked_ids", [])),
                key=f"post_lock_{player_id}",
                help="Keep this player when you click Reroll Unlocked Legs.",
            )
            if checked:
                new_locks.append(player_id)
    st.session_state.parlay_locked_ids = new_locks

    if len(picks) < legs:
        st.warning(f"Only {len(picks)} eligible legs were available. Relax team/game uniqueness or lower the minimum score.")
    st.markdown(
        '<div class="dd-disclaimer"><strong>MODEL NOTE:</strong> Combined estimates assume independent outcomes. Sportsbook prices are used when connected; model fair odds fill missing prices. This is research, not a guarantee.</div>',
        unsafe_allow_html=True,
    )

    export = pd.DataFrame([
        {
            "Profile": active_mode,
            "Locked": int(player.get("player_id") or -1) in new_locks,
            "Player": player.get("player_name"),
            "Team": player.get("team_name"),
            "Opponent": player.get("opponent"),
            "Projected Pitcher": player.get("opposing_pitcher"),
            "Dinger Score": player.get("dinger_score"),
            "HR Probability": percent(player.get("probability")),
            "Best Book": player.get("best_book") or "Model",
            "Best/Model Odds": odds(player.get("best_odds")) if player.get("best_odds") is not None else odds(player.get("fair_odds")),
        }
        for player in picks
    ])
    st.download_button(
        "Download This Ticket",
        export.to_csv(index=False).encode("utf-8"),
        f"{active_mode.lower()}_hr_parlay_{board.get('date','today')}.csv",
        "text/csv",
        use_container_width=True,
    )

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
            st.session_state["_force_live_refresh"] = True
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

    section("Best Value Edges", "DRAFTKINGS + FANDUEL", "Compare both books against the same model probability")
    rows = []
    for player in sorted(priced, key=lambda p: safe_float(p.get("edge_pct")), reverse=True):
        offers = {str(offer.get("book") or "").lower(): offer for offer in (player.get("sportsbook_offers") or [])}
        draftkings = next((offer for book, offer in offers.items() if "draft" in book), {})
        fanduel = next((offer for book, offer in offers.items() if "fanduel" in book or "fan duel" in book), {})
        rows.append({
            "Player": player.get("player_name"),
            "Team": player.get("team_name"),
            "Pitcher": player.get("opposing_pitcher") or "Not announced",
            "DraftKings": draftkings.get("american_odds"),
            "FanDuel": fanduel.get("american_odds"),
            "Best Book": player.get("best_book"),
            "Best Odds": player.get("best_odds"),
            "Model Probability": probability_fraction(player.get("probability")) * 100,
            "Book Implied Probability": safe_float(player.get("book_implied_probability")) * 100,
            "Edge %": safe_float(player.get("edge_pct")),
            "EV per $10": safe_float(player.get("ev_10")),
            "Dinger Score": safe_float(player.get("dinger_score")),
        })
    frame = pd.DataFrame(rows)
    odds_columns = [
        Column("Player", "Player", width="1.3fr"),
        Column("Team", "Team", width=".5fr", align="center"),
        Column("Pitcher", "Projected Pitcher", width="1.2fr"),
        Column("DraftKings", "DraftKings", formatter=lambda v, r: f'<b style="color:#35f29a">{odds(v)}</b>' if v is not None else '<b>—</b>', width=".75fr", align="center"),
        Column("FanDuel", "FanDuel", formatter=lambda v, r: f'<b style="color:#ff4df2">{odds(v)}</b>' if v is not None else '<b>—</b>', width=".75fr", align="center"),
        Column("Model Probability", "Model HR", progress_max=35, accent="#27c7ff", width="1.05fr"),
        Column("Book Implied Probability", "Book Implied", progress_max=35, accent="#ffd83d", width="1.05fr"),
        Column("Edge %", "Edge", formatter=lambda v, r: f'<b style="color:{"#35f29a" if safe_float(v)>0 else "#ff5f6d"}">{safe_float(v):+.1f}%</b>', width=".65fr", align="center"),
        Column("Dinger Score", "Score", progress_max=100, accent="#a85cff", width="1fr"),
    ]
    render_neon_table(rows, odds_columns, key="sportsbook_edges", max_height=650)
    st.download_button(
        "Export matched odds and value edges",
        frame.to_csv(index=False).encode("utf-8"),
        f"duggansdingers_odds_edges_{board.get('date','today')}.csv",
        "text/csv",
        use_container_width=True,
    )


def game_sims(board: dict) -> None:
    from services.game_simulator import build_game_sims

    hero(
        "GAME <span>SIMS</span>",
        "Run 5,000 deterministic matchup simulations using live MLB team production, the connected hitter board, and projected-pitcher adjustments.",
        stats={"Simulations / Game": "5,000", "Games": board.get("games", 0), "Outputs": "Runs • Hits • HR • K • SB"},
    )
    with st.spinner("Running the game simulation engine..."):
        sims = build_game_sims(board, iterations=5000)
    if not sims:
        st.info("Game simulations are waiting for valid matchup and team data.")
        return

    game_labels = {
        sim["game_key"]: f'{sim["away"]} at {sim["home"]} • {sim["projected_score"]}'
        for sim in sims
    }
    selected_key = st.selectbox(
        "Choose a simulated game",
        [sim["game_key"] for sim in sims],
        format_func=lambda key: game_labels.get(key, key),
    )
    selected = next(sim for sim in sims if sim["game_key"] == selected_key)

    team_panels: list[str] = []
    for team, opponent, side in (
        (selected["away"], selected["home"], "AWAY"),
        (selected["home"], selected["away"], "HOME"),
    ):
        metrics = selected["teams"][team]
        team_id = selected["away_id"] if side == "AWAY" else selected["home_id"]
        logo = f'<img src="{team_logo(team_id)}" alt="{esc(team)}">' if team_id else ""
        team_panels.append(
            f'''
<section class="dd-sim-team dd-sim-{side.lower()}">
  <div class="dd-sim-team-head">{logo}<div><small>{side}</small><b>{esc(team)}</b><span>vs {esc(opponent)}</span></div></div>
  <div class="dd-sim-score"><b>{safe_float(metrics.get('projected_runs')):.1f}</b><span>Projected Runs</span></div>
  <div class="dd-sim-win"><div class="dd-sim-win-track"><i style="width:{safe_float(metrics.get('win_probability'))*100:.1f}%"></i></div><b>{safe_float(metrics.get('win_probability'))*100:.1f}% WIN</b></div>
  <div class="dd-sim-stat-grid">
    <div><b>{safe_float(metrics.get('projected_hits')):.1f}</b><span>Hits</span></div>
    <div><b>{safe_float(metrics.get('projected_hr')):.1f}</b><span>Home Runs</span></div>
    <div><b>{safe_float(metrics.get('projected_so')):.1f}</b><span>Strikeouts</span></div>
    <div><b>{safe_float(metrics.get('projected_sb')):.1f}</b><span>Stolen Bases</span></div>
  </div>
  <div class="dd-sim-source">{esc(metrics.get('source') or 'Model baseline')}</div>
</section>'''
        )

    st.markdown(
        '<div class="dd-sim-matchup">'
        + team_panels[0]
        + '<div class="dd-sim-center"><small>PROJECTED FINAL</small><b>'
        + esc(selected["projected_score"])
        + '</b><span>5,000 model simulations</span></div>'
        + team_panels[1]
        + '</div>',
        unsafe_allow_html=True,
    )

    section("Full Slate Simulation Board", "RUNS • HITS • HR • K • SB", "Sorted by combined projected home runs")
    rows: list[dict] = []
    for sim in sims:
        away_metrics = sim["teams"][sim["away"]]
        home_metrics = sim["teams"][sim["home"]]
        rows.append({
            "Game": f'{sim["away"]} @ {sim["home"]}',
            "Projected Score": sim["projected_score"],
            "Away Win": safe_float(away_metrics.get("win_probability")) * 100,
            "Home Win": safe_float(home_metrics.get("win_probability")) * 100,
            "Hits": safe_float(away_metrics.get("projected_hits")) + safe_float(home_metrics.get("projected_hits")),
            "Home Runs": safe_float(away_metrics.get("projected_hr")) + safe_float(home_metrics.get("projected_hr")),
            "Strikeouts": safe_float(away_metrics.get("projected_so")) + safe_float(home_metrics.get("projected_so")),
            "Stolen Bases": safe_float(away_metrics.get("projected_sb")) + safe_float(home_metrics.get("projected_sb")),
        })
    sim_columns = [
        Column("Game", "Matchup", width="1.1fr"),
        Column("Projected Score", "Projected Score", width="1.4fr"),
        Column("Away Win", "Away Win", progress_max=100, accent="#27c7ff", width="1fr"),
        Column("Home Win", "Home Win", progress_max=100, accent="#ff4df2", width="1fr"),
        Column("Hits", "Total Hits", progress_max=24, accent="#35f29a", width="1fr"),
        Column("Home Runs", "Total HR", progress_max=6, accent="#ffd83d", width="1fr"),
        Column("Strikeouts", "Total K", progress_max=24, accent="#a85cff", width="1fr"),
        Column("Stolen Bases", "Total SB", progress_max=5, accent="#ff5f6d", width="1fr"),
    ]
    render_neon_table(rows, sim_columns, key="game_sims_full_slate", max_height=600)
    st.markdown(
        '<div class="dd-disclaimer"><strong>SIMULATION NOTE:</strong> These are model estimates, not sportsbook lines. Team season stats, connected hitter projections, and available probable-pitcher data are used; missing inputs fall back to league-average assumptions.</div>',
        unsafe_allow_html=True,
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
        stats={"Games Connected": len(game_weather), "Slate": board.get("date", ""), "Source": ", ".join((board.get("weather_summary") or {}).get("providers") or ["NWS / WeatherAPI"])},
    )
    if not game_weather:
        summary = board.get("weather_summary", {}) or {}
        errors = summary.get("errors", []) or []
        st.markdown(
            '<div class="dd-weather-setup"><b>WEATHER FEED NEEDS A PRIMARY PROVIDER</b><span>Add <code>WEATHERAPI_KEY</code> in Streamlit Secrets for reliable weather at every MLB park. The app will then fall back to Visual Crossing and the National Weather Service automatically.</span></div>',
            unsafe_allow_html=True,
        )
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
    weather_columns = [
        Column("Player", "Player", width="1.25fr"),
        Column("Team", "Team", width=".5fr", align="center"),
        Column("Ballpark", "Ballpark", width="1.25fr"),
        Column("Weather Grade", "Grade", width=".55fr", align="center"),
        Column("HR Impact", "HR Impact", formatter=lambda v, r: f'<b style="color:{"#35f29a" if safe_float(v)>=0 else "#ff5f6d"}">{safe_float(v):+.1f}</b>', width=".7fr", align="center"),
        Column("Temperature", "Temp", formatter=lambda v, r: f'<b>{safe_float(v):.0f}°F</b>', width=".65fr", align="center"),
        Column("Wind MPH", "Wind", formatter=lambda v, r: f'<b>{safe_float(v):.0f} mph</b>', width=".65fr", align="center"),
        Column("LF", "LF", formatter=lambda v, r: f'<b style="color:{"#35f29a" if safe_float(v)>=0 else "#ff5f6d"}">{safe_float(v):+.0f}%</b>', width=".55fr", align="center"),
        Column("CF", "CF", formatter=lambda v, r: f'<b style="color:{"#35f29a" if safe_float(v)>=0 else "#ff5f6d"}">{safe_float(v):+.0f}%</b>', width=".55fr", align="center"),
        Column("RF", "RF", formatter=lambda v, r: f'<b style="color:{"#35f29a" if safe_float(v)>=0 else "#ff5f6d"}">{safe_float(v):+.0f}%</b>', width=".55fr", align="center"),
        Column("Dinger Score", "Score", progress_max=100, accent="#ff4df2", width="1fr"),
    ]
    render_neon_table(rows, weather_columns, key="weather_adjusted_board", max_height=650)

# ===== V16 DETAIL PAGES =====

def _sim_narrative(sim: dict) -> str:
    away = str(sim["away"])
    home = str(sim["home"])
    away_metrics = sim["teams"][away]
    home_metrics = sim["teams"][home]

    ar = safe_float(away_metrics.get("projected_runs"))
    hr = safe_float(home_metrics.get("projected_runs"))
    ah = safe_float(away_metrics.get("projected_hits"))
    hh = safe_float(home_metrics.get("projected_hits"))
    ahr = safe_float(away_metrics.get("projected_hr"))
    hhr = safe_float(home_metrics.get("projected_hr"))
    ak = safe_float(away_metrics.get("projected_so"))
    hk = safe_float(home_metrics.get("projected_so"))
    asb = safe_float(away_metrics.get("projected_sb"))
    hsb = safe_float(home_metrics.get("projected_sb"))
    aw = safe_float(away_metrics.get("win_probability"))
    hw = safe_float(home_metrics.get("win_probability"))

    favorite = away if aw >= hw else home
    favorite_prob = max(aw, hw) * 100
    total_runs = ar + hr
    total_hr = ahr + hhr
    total_k = ak + hk
    total_sb = asb + hsb
    run_gap = abs(ar - hr)

    if total_hr >= 3.2:
        opening = f"The model expects the long ball to shape {away}–{home}, with roughly {total_hr:.1f} combined homers and {total_runs:.1f} projected runs."
    elif total_k >= 18.0:
        opening = f"This profiles as a strikeout-heavy matchup: the simulation lands near {total_k:.1f} combined punchouts and only {total_hr:.1f} projected homers."
    elif total_sb >= 1.5:
        opening = f"The sim sees an active baserunning game, with about {total_sb:.1f} steals and pressure created through contact rather than only home-run power."
    elif total_runs >= 9.5:
        opening = f"The scoring model leans offense, projecting {total_runs:.1f} combined runs and {ah + hh:.1f} total hits."
    else:
        opening = f"The model projects a controlled game around {total_runs:.1f} combined runs, with neither lineup separating early."

    if run_gap < 0.45:
        close_detail = f"The projected score is nearly even, so the late bullpen matchup is the most likely swing point; {favorite} holds only a {favorite_prob:.0f}% edge."
    elif max(ahr, hhr) - min(ahr, hhr) >= 0.45:
        power_team = away if ahr > hhr else home
        close_detail = f"{power_team} owns the clearer home-run path, while {favorite} carries the stronger overall win profile at {favorite_prob:.0f}%."
    elif max(ah, hh) - min(ah, hh) >= 1.0:
        contact_team = away if ah > hh else home
        close_detail = f"{contact_team} is projected to create more traffic with the better hit total, and {favorite} finishes as the {favorite_prob:.0f}% simulation favorite."
    else:
        close_detail = f"{favorite} has the steadier run-production profile and wins {favorite_prob:.0f}% of simulations, but the margin remains vulnerable to one extra-base hit."

    return f"{opening} {close_detail}"


def game_sims(board: dict) -> None:
    from services.game_simulator import build_game_sims

    hero(
        "GAME <span>SIMS</span>",
        "Five thousand matchup simulations with projected scores, hits, home runs, strikeouts, stolen bases, and a two-sentence AI-style game read.",
        stats={"Simulations / Game": "5,000", "Games": board.get("games", 0), "Outputs": "Runs • Hits • HR • K • SB"},
    )
    with st.spinner("Running the game simulation engine..."):
        sims = build_game_sims(board, iterations=5000)
    if not sims:
        st.info("Game simulations are waiting for valid matchup and team data.")
        return

    labels = {sim["game_key"]: f'{sim["away"]} at {sim["home"]} • {sim["projected_score"]}' for sim in sims}
    selected_key = st.selectbox("Choose a simulated game", [sim["game_key"] for sim in sims], format_func=lambda key: labels.get(key, key))
    selected = next(sim for sim in sims if sim["game_key"] == selected_key)

    panels: list[str] = []
    for team, opponent, side in ((selected["away"], selected["home"], "AWAY"), (selected["home"], selected["away"], "HOME")):
        metrics = selected["teams"][team]
        team_id = selected["away_id"] if side == "AWAY" else selected["home_id"]
        logo = f'<img src="{team_logo(team_id)}" alt="{esc(team)}">' if team_id else ""
        panels.append(f'''
<section class="dd-sim-team dd-sim-{side.lower()}">
  <div class="dd-sim-team-head">{logo}<div><small>{side}</small><b>{esc(team)}</b><span>vs {esc(opponent)}</span></div></div>
  <div class="dd-sim-score"><b>{safe_float(metrics.get('projected_runs')):.1f}</b><span>Projected Runs</span></div>
  <div class="dd-sim-win"><div class="dd-sim-win-track"><i style="width:{safe_float(metrics.get('win_probability'))*100:.1f}%"></i></div><b>{safe_float(metrics.get('win_probability'))*100:.1f}% WIN</b></div>
  <div class="dd-sim-stat-grid">
    <div><b>{safe_float(metrics.get('projected_hits')):.1f}</b><span>Hits</span></div>
    <div><b>{safe_float(metrics.get('projected_hr')):.1f}</b><span>Home Runs</span></div>
    <div><b>{safe_float(metrics.get('projected_so')):.1f}</b><span>Strikeouts</span></div>
    <div><b>{safe_float(metrics.get('projected_sb')):.1f}</b><span>Stolen Bases</span></div>
  </div>
</section>''')

    st.markdown(
        '<div class="dd-sim-matchup">' + panels[0]
        + '<div class="dd-sim-center"><small>PROJECTED FINAL</small><b>' + esc(selected["projected_score"])
        + '</b><span>5,000 model simulations</span></div>' + panels[1] + '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="dd-sim-narrative"><i>✦</i><div><b>AI SIMULATION READ</b><p>{esc(_sim_narrative(selected))}</p></div></div>',
        unsafe_allow_html=True,
    )

    section("Full Slate Simulation Board", "RUNS • HITS • HR • K • SB", "Sorted by combined projected home runs")
    rows: list[dict] = []
    for sim in sims:
        away_metrics = sim["teams"][sim["away"]]
        home_metrics = sim["teams"][sim["home"]]
        rows.append({
            "Game": f'{sim["away"]} @ {sim["home"]}',
            "Projected Score": sim["projected_score"],
            "Away Win": safe_float(away_metrics.get("win_probability")) * 100,
            "Home Win": safe_float(home_metrics.get("win_probability")) * 100,
            "Hits": safe_float(away_metrics.get("projected_hits")) + safe_float(home_metrics.get("projected_hits")),
            "Home Runs": safe_float(away_metrics.get("projected_hr")) + safe_float(home_metrics.get("projected_hr")),
            "Strikeouts": safe_float(away_metrics.get("projected_so")) + safe_float(home_metrics.get("projected_so")),
            "Stolen Bases": safe_float(away_metrics.get("projected_sb")) + safe_float(home_metrics.get("projected_sb")),
            "AI Read": _sim_narrative(sim),
        })
    columns = [
        Column("Game", "MATCHUP", width="1.0fr"),
        Column("Projected Score", "PROJECTED SCORE", width="1.25fr"),
        Column("Away Win", "AWAY WIN", progress_max=100, accent="#27c7ff", width=".9fr"),
        Column("Home Win", "HOME WIN", progress_max=100, accent="#ff4df2", width=".9fr"),
        Column("Hits", "TOTAL HITS", progress_max=24, accent="#35f29a", width=".9fr"),
        Column("Home Runs", "TOTAL HR", progress_max=6, accent="#ffd83d", width=".9fr"),
        Column("Strikeouts", "TOTAL K", progress_max=24, accent="#a85cff", width=".9fr"),
        Column("Stolen Bases", "TOTAL SB", progress_max=5, accent="#ff5f6d", width=".9fr"),
    ]
    render_neon_table(rows, columns, key="game_sims_full_slate_v16", max_height=620)


def _v16_weather_games(board: dict) -> list[dict]:
    meta_map = {str(meta.get("game_id") or ""): dict(meta) for meta in board.get("games_meta", []) or [] if meta.get("game_id")}
    for player in board.get("rankings", []) or []:
        key = str(player.get("game_id") or "")
        if not key:
            continue
        item = meta_map.setdefault(key, {"game_id": key})
        for field in (
            "game_time", "home_team_name", "away_team_name", "home_team_id", "away_team_id", "venue_name",
            "weather_available", "weather_source", "weather_time_local", "temperature_f", "apparent_temperature_f",
            "humidity_pct", "dew_point_f", "surface_pressure_hpa", "visibility_miles", "cloud_cover_pct",
            "precip_probability", "wind_speed_mph", "wind_gust_mph", "wind_direction_deg", "wind_field_effect",
            "weather_description", "weather_impact", "weather_grade", "stadium_name", "stadium_timezone", "roof_type",
            "weather_error", "weather_reasons",
        ):
            if item.get(field) in (None, "") and player.get(field) not in (None, ""):
                item[field] = player.get(field)
    games = list(meta_map.values())
    games.sort(key=lambda game: (bool(game.get("weather_available")), safe_float(game.get("weather_impact"))), reverse=True)
    return games


def _v16_zone_values(game: dict) -> tuple[int, int, int]:
    impact = safe_float(game.get("weather_impact"))
    speed = safe_float(game.get("wind_speed_mph"))
    direction = str(game.get("wind_field_effect") or "cross").lower()
    base = max(-18, min(18, round(impact * 1.7)))
    wind = min(10, round(speed * .42))
    if direction == "out":
        return base + wind // 2, base + wind, base + wind // 2
    if direction == "in":
        return base - wind // 2, base - wind, base - wind // 2
    degrees = safe_float(game.get("wind_direction_deg"))
    return (base + wind, base, base - wind) if 0 <= degrees < 180 else (base - wind, base, base + wind)


def _v16_signed(value: int) -> str:
    return f"+{value}%" if value > 0 else f"{value}%"


def _v16_zone_color(value: int) -> str:
    return "#35f29a" if value >= 8 else "#ffd83d" if value >= 2 else "#27c7ff" if value > -3 else "#ff5f6d"


def _v16_weather_field(game: dict, compact: bool = False) -> str:
    lf, cf, rf = _v16_zone_values(game)
    angle = (safe_float(game.get("wind_direction_deg")) + 180) % 360
    height_class = " compact" if compact else ""
    return f'''
<div class="dd-v16-field{height_class}">
  <svg viewBox="0 0 560 360" aria-label="Ballpark wind effectiveness field">
    <defs><filter id="v16glow"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
    <path d="M280 338 L55 175 Q280 15 505 175 Z" fill="#123b2a" stroke="#2e91cc" stroke-width="2"/>
    <path d="M280 338 L55 175 Q165 72 280 60 L280 338 Z" fill="{_v16_zone_color(lf)}" fill-opacity=".15"/>
    <path d="M280 338 L280 60 Q395 72 505 175 Z" fill="{_v16_zone_color(rf)}" fill-opacity=".15"/>
    <path d="M280 338 L160 175 Q280 69 400 175 Z" fill="{_v16_zone_color(cf)}" fill-opacity=".13"/>
    <path d="M280 330 L220 275 L280 215 L340 275 Z" fill="#8a6a38" stroke="#e5d396"/>
    <path d="M280 316 L242 278 L280 240 L318 278 Z" fill="#226238" stroke="#f3dfaa"/>
    <line x1="280" y1="320" x2="280" y2="105" stroke="#fff" stroke-width="4" transform="rotate({angle:.0f} 280 320)" filter="url(#v16glow)"/>
    <polygon points="280,83 269,108 291,108" fill="#fff" transform="rotate({angle:.0f} 280 320)" filter="url(#v16glow)"/>
  </svg>
  <div class="dd-v16-zone lf" style="--zone:{_v16_zone_color(lf)}"><b>{_v16_signed(lf)}</b><span>LEFT FIELD</span></div>
  <div class="dd-v16-zone cf" style="--zone:{_v16_zone_color(cf)}"><b>{_v16_signed(cf)}</b><span>CENTER FIELD</span></div>
  <div class="dd-v16-zone rf" style="--zone:{_v16_zone_color(rf)}"><b>{_v16_signed(rf)}</b><span>RIGHT FIELD</span></div>
</div>'''


def _v16_weather_card(game: dict) -> str:
    key = str(game.get("game_id") or "")
    away = str(game.get("away_team_name") or "AWAY")
    home = str(game.get("home_team_name") or "HOME")
    available = bool(game.get("weather_available"))
    stadium = str(game.get("stadium_name") or game.get("venue_name") or "Ballpark")
    temp = f'{safe_float(game.get("temperature_f")):.0f}°F' if available else "—"
    wind = f'{safe_float(game.get("wind_speed_mph")):.0f} MPH' if available else "PENDING"
    grade = str(game.get("weather_grade") or "—")
    source = str(game.get("weather_source") or "Weather pending")
    error = str(game.get("weather_error") or "")
    return f'''
<a class="dd-v16-weather-link" href="?view=weather&game={quote(key)}" target="_self">
<article class="dd-v16-weather-card {'unavailable' if not available else ''}">
  <header><div><small>{esc(away)} @ {esc(home)}</small><b>{esc(stadium)}</b></div><em>{esc(grade)}<span>HR WEATHER</span></em></header>
  {_v16_weather_field(game, compact=True)}
  <footer><div><b>{temp}</b><span>TEMP</span></div><div><b>{wind}</b><span>WIND</span></div><div><b>{safe_float(game.get('precip_probability')):.0f}%</b><span>RAIN</span></div><div><b>{safe_float(game.get('weather_impact')):+.1f}</b><span>HR IMPACT</span></div></footer>
  <p>{esc(source if available else error or 'Forecast pending')}</p>
</article>
</a>'''


def _v16_weather_detail(board: dict, game: dict) -> None:
    away = str(game.get("away_team_name") or "AWAY")
    home = str(game.get("home_team_name") or "HOME")
    stadium = str(game.get("stadium_name") or game.get("venue_name") or "Ballpark")
    st.markdown('<a class="dd-weather-back" href="?view=weather" target="_self">← ALL BALLPARKS</a>', unsafe_allow_html=True)
    hero(
        f"{esc(away)} <span>AT {esc(home)}</span>",
        f"Full game-time weather intelligence for {stadium}, including field-direction carry and the hitters most affected by the conditions.",
        stats={"Grade": game.get("weather_grade") or "—", "Source": game.get("weather_source") or "Pending", "HR Impact": f'{safe_float(game.get("weather_impact")):+.1f}'},
    )
    if not game.get("weather_available"):
        st.error(f"Weather unavailable: {game.get('weather_error') or 'No provider returned a forecast'}")
        return

    st.markdown(
        '<div class="dd-v16-weather-detail">'
        + _v16_weather_field(game)
        + f'''<aside>
          <div><span>TEMPERATURE</span><b>{safe_float(game.get('temperature_f')):.0f}°F</b></div>
          <div><span>FEELS LIKE</span><b>{safe_float(game.get('apparent_temperature_f')):.0f}°F</b></div>
          <div><span>WIND</span><b>{safe_float(game.get('wind_speed_mph')):.0f} MPH</b></div>
          <div><span>HUMIDITY</span><b>{safe_float(game.get('humidity_pct')):.0f}%</b></div>
          <div><span>RAIN CHANCE</span><b>{safe_float(game.get('precip_probability')):.0f}%</b></div>
          <div><span>CLOUD COVER</span><b>{safe_float(game.get('cloud_cover_pct')):.0f}%</b></div>
          <div class="impact"><span>OVERALL HR IMPACT</span><b>{safe_float(game.get('weather_impact')):+.1f}</b></div>
          <p>{esc(' • '.join(game.get('weather_reasons') or []))}</p>
        </aside></div>''',
        unsafe_allow_html=True,
    )

    hitters = [player for player in board.get("rankings", []) or [] if str(player.get("game_id") or "") == str(game.get("game_id") or "")]
    hitters.sort(key=lambda player: safe_float(player.get("dinger_score")), reverse=True)
    rows = [{
        "Player": player.get("player_name"),
        "Team": player.get("team_name"),
        "Pitcher": player.get("opposing_pitcher") or "TBD",
        "Score": safe_float(player.get("dinger_score")),
        "HR Probability": probability_fraction(player.get("probability")) * 100,
        "Last 7": safe_int(player.get("last_7_home_runs")),
        "Last 15": safe_int(player.get("last_15_home_runs")),
    } for player in hitters]
    section("Game Hitter Impact Board", "WEATHER + MATCHUP + POWER")
    columns = [
        Column("Player", "PLAYER", width="1.2fr"), Column("Team", "TEAM", width=".55fr", align="center"),
        Column("Pitcher", "PROBABLE PITCHER", width="1.25fr"), Column("Score", "DINGER SCORE", progress_max=100, accent="#ff4df2", width="1fr"),
        Column("HR Probability", "HR PROB", progress_max=35, accent="#27c7ff", width="1fr"),
        Column("Last 7", "LAST 7", progress_max=5, accent="#35f29a", width=".9fr"),
        Column("Last 15", "LAST 15", progress_max=9, accent="#ffd83d", width=".9fr"),
    ]
    render_neon_table(rows, columns, key="weather_game_hitters", max_height=620)


def weather_center(board: dict) -> None:
    games = _v16_weather_games(board)
    requested = str(st.query_params.get("game") or "")
    selected = next((game for game in games if str(game.get("game_id")) == requested), None)
    if selected:
        _v16_weather_detail(board, selected)
        return

    summary = board.get("weather_summary", {}) or {}
    providers = summary.get("providers") or []
    configuration = summary.get("configuration") or {}
    hero(
        "BALLPARK <span>WEATHER COMMAND</span>",
        "Three ballparks per row. Open any game for its full wind diagram, field-direction carry, game-time conditions, and weather-adjusted hitter board.",
        stats={"Games Connected": summary.get("games_available", 0), "Slate": board.get("date", ""), "Source": ", ".join(providers) or "WeatherAPI / NWS"},
    )

    if not games:
        st.info("No games are available for this slate.")
        return

    if not summary.get("games_available"):
        configured = bool(configuration.get("weatherapi") or configuration.get("visual_crossing"))
        title = "PROVIDER CONNECTED — STADIUM MATCHING FAILED" if configured else "WEATHER PROVIDER KEY NOT DETECTED"
        errors = summary.get("errors") or []
        detail = " • ".join(str(error) for error in errors[:3]) or "The app could not match the home team to a stadium."
        st.markdown(f'<div class="dd-weather-diagnostic"><b>{esc(title)}</b><span>{esc(detail)}</span></div>', unsafe_allow_html=True)

    st.markdown('<div class="dd-v16-weather-grid">' + "".join(_v16_weather_card(game) for game in games) + '</div>', unsafe_allow_html=True)

# ===== V17 TEMPLATE-FINISH OVERRIDES =====

def _v17_game_key(game: dict) -> str:
    return str(game.get("weather_game_key") or game.get("schedule_game_key") or game.get("mlb_game_pk") or game.get("game_id") or "")


def _v17_weather_games(board: dict) -> list[dict]:
    games: dict[str, dict] = {}
    for meta in board.get("games_meta", []) or []:
        key = _v17_game_key(meta)
        if key:
            games[key] = dict(meta)
    for player in board.get("rankings", []) or []:
        key = str(player.get("weather_game_key") or player.get("schedule_game_key") or player.get("mlb_game_pk") or "")
        if not key:
            continue
        item = games.setdefault(key, {"weather_game_key": key})
        for field in (
            "game_time", "home_team_name", "away_team_name", "home_team_id", "away_team_id", "venue_name",
            "stadium_name", "stadium_team", "stadium_image_url", "weather_available", "weather_source",
            "weather_time_local", "temperature_f", "apparent_temperature_f", "humidity_pct", "dew_point_f",
            "surface_pressure_hpa", "visibility_miles", "cloud_cover_pct", "precip_probability", "wind_speed_mph",
            "wind_gust_mph", "wind_direction_deg", "wind_field_effect", "weather_description", "weather_impact",
            "weather_grade", "weather_reasons", "weather_error", "roof_type", "roof_status",
        ):
            if item.get(field) in (None, "") and player.get(field) not in (None, ""):
                item[field] = player.get(field)
    output = list(games.values())
    output.sort(key=lambda game: (bool(game.get("weather_available")), safe_float(game.get("weather_impact"))), reverse=True)
    return output


def _v17_weather_card(game: dict) -> str:
    key = _v17_game_key(game)
    away = str(game.get("away_team_name") or "AWAY")
    home = str(game.get("home_team_name") or "HOME")
    stadium = str(game.get("stadium_name") or game.get("venue_name") or "Ballpark")
    image = str(game.get("stadium_image_url") or "")
    available = bool(game.get("weather_available"))
    lf, cf, rf = _v16_zone_values(game)
    grade = str(game.get("weather_grade") or "—")
    temp = f'{safe_float(game.get("temperature_f")):.0f}°F' if available else "—"
    wind = f'{safe_float(game.get("wind_speed_mph")):.0f} mph' if available else "PENDING"
    game_time = str(game.get("weather_time_local") or game.get("game_time") or "")
    if "T" in game_time:
        game_time = game_time.split("T", 1)[1][:5]
    background = f"background-image:linear-gradient(180deg,rgba(2,8,18,.15),rgba(2,8,18,.88)),url('{esc(image)}');" if image else ""
    border = weather_color(game) if available else "#ff6a4d"
    return f'''
<a class="dd-stadium-card-link" href="?view=weather&game={quote(key)}" target="_self">
<article class="dd-stadium-card" style="--stadium-accent:{border};{background}">
  <header><div class="dd-stadium-teams"><img src="{team_logo(game.get('away_team_id'))}"><b>{esc(away)} @ {esc(home)}</b><img src="{team_logo(game.get('home_team_id'))}"></div><span>{esc(game_time or 'GAME TIME')}</span></header>
  <div class="dd-stadium-name"><small>{esc(stadium)}</small><strong>{temp}</strong><span>{esc(game.get('weather_description') or ('Forecast pending' if not available else 'Game-time forecast'))}</span></div>
  <div class="dd-stadium-wind"><b>↗ {wind}</b><span>{esc(str(game.get('wind_field_effect') or 'unknown').upper())}</span><em>{esc(grade)}</em></div>
  <footer><div><span>LF</span><b>{_v16_signed(lf)}</b></div><div><span>CF</span><b>{_v16_signed(cf)}</b></div><div><span>RF</span><b>{_v16_signed(rf)}</b></div><div><span>HR IMPACT</span><b>{safe_float(game.get('weather_impact')):+.1f}</b></div></footer>
</article></a>'''


def _v17_weather_detail(board: dict, game: dict) -> None:
    away = str(game.get("away_team_name") or "AWAY")
    home = str(game.get("home_team_name") or "HOME")
    stadium = str(game.get("stadium_name") or game.get("venue_name") or "Ballpark")
    image = str(game.get("stadium_image_url") or "")
    st.markdown('<a class="dd-weather-back" href="?view=weather" target="_self">← ALL BALLPARKS</a>', unsafe_allow_html=True)
    background = f"background-image:linear-gradient(90deg,rgba(2,8,18,.94),rgba(2,8,18,.30),rgba(2,8,18,.86)),url('{esc(image)}');" if image else ""
    lf, cf, rf = _v16_zone_values(game)
    st.markdown(
        f'''
<section class="dd-weather-detail-hero" style="{background}">
  <div class="dd-weather-detail-title"><span>{esc(away)} @ {esc(home)}</span><h1>{esc(stadium)}</h1><p>{esc(game.get('weather_description') or 'Game-time ballpark weather')}</p></div>
  <div class="dd-weather-detail-grade"><b>{esc(game.get('weather_grade') or '—')}</b><span>WEATHER GRADE</span></div>
  <div class="dd-weather-detail-metrics"><div><span>TEMP</span><b>{safe_float(game.get('temperature_f')):.0f}°F</b></div><div><span>WIND</span><b>{safe_float(game.get('wind_speed_mph')):.0f} MPH</b></div><div><span>HUMIDITY</span><b>{safe_float(game.get('humidity_pct')):.0f}%</b></div><div><span>RAIN</span><b>{safe_float(game.get('precip_probability')):.0f}%</b></div></div>
</section>
<div class="dd-weather-direction-strip"><div><span>LEFT FIELD</span><b>{_v16_signed(lf)}</b></div><div><span>CENTER FIELD</span><b>{_v16_signed(cf)}</b></div><div><span>RIGHT FIELD</span><b>{_v16_signed(rf)}</b></div><div><span>OVERALL HR IMPACT</span><b>{safe_float(game.get('weather_impact')):+.1f}</b></div></div>''',
        unsafe_allow_html=True,
    )
    if not game.get("weather_available"):
        st.error(f"Weather unavailable: {game.get('weather_error') or 'No forecast returned'}")
        return

    selected_key = _v17_game_key(game)
    hitters = [
        player for player in board.get("rankings", []) or []
        if str(player.get("weather_game_key") or player.get("schedule_game_key") or player.get("mlb_game_pk") or "") == selected_key
    ]
    hitters.sort(key=lambda player: safe_float(player.get("dinger_score")), reverse=True)
    rows = [{
        "Player": player.get("player_name"), "Team": player.get("team_name"),
        "Pitcher": player.get("opposing_pitcher") or "TBD", "Score": safe_float(player.get("dinger_score")),
        "HR Probability": probability_fraction(player.get("probability")) * 100,
        "Last 7": safe_int(player.get("last_7_home_runs")), "Last 15": safe_int(player.get("last_15_home_runs")),
        "Best Price": player.get("best_odds") if player.get("best_odds") is not None else player.get("fair_odds"),
    } for player in hitters]
    section("Weather-Adjusted Hitter Board", "GAME INTELLIGENCE", f"{len(hitters)} hitters ranked for this matchup")
    columns = [
        Column("Player", "PLAYER", width="1.25fr"), Column("Team", "TEAM", width=".55fr", align="center"),
        Column("Pitcher", "PROBABLE PITCHER", width="1.3fr"), Column("Score", "DINGER SCORE", progress_max=100, accent="#ff4df2", width="1fr"),
        Column("HR Probability", "HR PROB", progress_max=35, accent="#27c7ff", width="1fr"),
        Column("Last 7", "LAST 7", progress_max=5, accent="#ff6a32", width=".85fr"),
        Column("Last 15", "LAST 15", progress_max=9, accent="#a85cff", width=".85fr"),
        Column("Best Price", "BEST PRICE", formatter=lambda value, row: f'<b style="color:#43f59d">{odds(value)}</b>', width=".75fr", align="center"),
    ]
    render_neon_table(rows, columns, key="v17_weather_hitters", max_height=620)


def weather_center(board: dict) -> None:
    games = _v17_weather_games(board)
    requested = str(st.query_params.get("game") or "")
    selected = next((game for game in games if _v17_game_key(game) == requested), None)
    if selected:
        _v17_weather_detail(board, selected)
        return

    summary = board.get("weather_summary", {}) or {}
    providers = ", ".join(summary.get("providers") or ["WeatherAPI / NWS"])
    hero(
        "BALLPARK <span>WEATHER COMMAND</span>",
        "Three real ballpark aerials per row. Open any game for field-direction carry, game-time conditions, and the weather-adjusted hitter board.",
        stats={"Games Today": len(games), "Connected": summary.get("games_available", 0), "Source": providers},
    )
    if not games:
        st.error("No MLB schedule games were returned for this slate.")
        return
    st.markdown('<div class="dd-stadium-grid">' + ''.join(_v17_weather_card(game) for game in games) + '</div>', unsafe_allow_html=True)
    errors = summary.get("errors") or []
    if errors:
        with st.expander("Weather diagnostics"):
            for error in errors:
                st.code(str(error))


def _v17_sim_card(sim: dict, active: bool = False) -> str:
    away = sim["away"]
    home = sim["home"]
    away_metrics = sim["teams"][away]
    home_metrics = sim["teams"][home]
    key = str(sim.get("game_key") or "")
    total_hr = safe_float(away_metrics.get("projected_hr")) + safe_float(home_metrics.get("projected_hr"))
    total_hits = safe_float(away_metrics.get("projected_hits")) + safe_float(home_metrics.get("projected_hits"))
    return f'''
<a class="dd-sim-row-link{' active' if active else ''}" href="?view=game-sims&game={quote(key)}" target="_self">
  <div class="dd-sim-row dd21-sim-row"><div class="match"><img src="{team_logo(sim.get('away_id'))}"><b>{esc(away)} @ {esc(home)}</b><img src="{team_logo(sim.get('home_id'))}"></div>
  <div><span>WIN PROB</span><b>{safe_float(away_metrics.get('win_probability'))*100:.0f}% / {safe_float(home_metrics.get('win_probability'))*100:.0f}%</b></div>
  <div><span>PROJ. SCORE</span><b>{esc(sim.get('projected_score'))}</b></div>
  <div><span>PROJ. HITS</span><b>{total_hits:.1f}</b></div>
  <div><span>PROJ. HR</span><b>{total_hr:.1f}</b></div><i>›</i></div>
</a>'''



def game_sims(board: dict) -> None:
    from services.game_simulator import build_game_sims
    hero(
        "GAME <span>SIMS</span>",
        "AI-style game projections with scores, hits, home runs, strikeouts, stolen bases, and clickable full-slate matchup intelligence.",
        stats={"Simulations / Game": "5,000", "Games": board.get("games", 0), "Outputs": "Runs • Hits • HR • K • SB"},
    )
    with st.spinner("Running the game simulation engine..."):
        sims = build_game_sims(board, iterations=5000)
    if not sims:
        st.info("Game simulations are waiting for valid matchup and team data.")
        return

    requested = str(st.query_params.get("game") or "")
    selected = next((sim for sim in sims if str(sim.get("game_key")) == requested), sims[0])
    away = selected["away"]
    home = selected["home"]
    away_metrics = selected["teams"][away]
    home_metrics = selected["teams"][home]
    st.markdown(
        f'''
<section class="dd-sim-feature">
  <div class="dd-sim-club away"><img src="{team_logo(selected.get('away_id'))}"><div><small>AWAY</small><h2>{esc(away)}</h2><span>{safe_float(away_metrics.get('win_probability'))*100:.1f}% WIN</span></div><b>{safe_float(away_metrics.get('projected_runs')):.1f}</b></div>
  <div class="dd-sim-final"><span>PROJECTED FINAL</span><h1>{esc(selected.get('projected_score'))}</h1><small>5,000 model simulations</small></div>
  <div class="dd-sim-club home"><b>{safe_float(home_metrics.get('projected_runs')):.1f}</b><div><small>HOME</small><h2>{esc(home)}</h2><span>{safe_float(home_metrics.get('win_probability'))*100:.1f}% WIN</span></div><img src="{team_logo(selected.get('home_id'))}"></div>
</section>
<div class="dd-sim-metrics"><div><span>AWAY HITS</span><b>{safe_float(away_metrics.get('projected_hits')):.1f}</b></div><div><span>AWAY HR</span><b>{safe_float(away_metrics.get('projected_hr')):.1f}</b></div><div><span>AWAY K</span><b>{safe_float(away_metrics.get('projected_so')):.1f}</b></div><div><span>HOME HITS</span><b>{safe_float(home_metrics.get('projected_hits')):.1f}</b></div><div><span>HOME HR</span><b>{safe_float(home_metrics.get('projected_hr')):.1f}</b></div><div><span>HOME K</span><b>{safe_float(home_metrics.get('projected_so')):.1f}</b></div></div>
<div class="dd-sim-narrative"><i>✦</i><div><b>AI SIMULATION READ</b><p>{esc(_sim_narrative(selected))}</p></div></div>''',
        unsafe_allow_html=True,
    )
    section("Full Slate Simulation Board", "CLICK A MATCHUP", "The selected game opens above; no dropdown required")
    st.markdown('<div class="dd-sim-click-board">' + ''.join(_v17_sim_card(sim, sim is selected) for sim in sims) + '</div>', unsafe_allow_html=True)

# ===== V18 PIXEL-TEMPLATE PAGE OVERRIDES =====

def _v18_game_time(game: dict) -> str:
    raw = str(game.get("weather_time_local") or game.get("game_time") or "")
    if not raw:
        return "GAME TIME"
    try:
        from datetime import datetime
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed.strftime("%-I:%M %p")
    except Exception:
        if "T" in raw:
            return raw.split("T", 1)[1][:5]
        return raw[:10]


def _v18_weather_card(game: dict, active: bool = False) -> str:
    key = _v17_game_key(game)
    away = str(game.get("away_team_name") or "AWAY")
    home = str(game.get("home_team_name") or "HOME")
    stadium = str(game.get("stadium_name") or game.get("venue_name") or "Ballpark")
    image = str(game.get("stadium_image_url") or "")
    available = bool(game.get("weather_available"))
    lf, cf, rf = _v16_zone_values(game)
    grade = str(game.get("weather_grade") or "—")
    temp = f'{safe_float(game.get("temperature_f")):.0f}°F' if available else "—"
    wind = f'{safe_float(game.get("wind_speed_mph")):.0f} mph' if available else "PENDING"
    effect = str(game.get("wind_field_effect") or "unknown").replace("_", " ").upper()
    description = str(game.get("weather_description") or ("Forecast pending" if not available else "Game-time forecast"))
    background = f"background-image:linear-gradient(180deg,rgba(2,8,18,.16),rgba(2,8,18,.91)),url('{esc(image)}');" if image else ""
    border = weather_color(game) if available else "#ff6a4d"
    active_class = " active" if active else ""
    return f'''
<a class="dd-stadium-card-link{active_class}" href="?view=weather&game={quote(key)}" target="_self">
<article class="dd-stadium-card" style="--stadium-accent:{border};{background}">
  <header>
    <div class="dd-stadium-teams"><img src="{team_logo(game.get('away_team_id'))}"><b>{esc(away)} @ {esc(home)}</b><img src="{team_logo(game.get('home_team_id'))}"></div>
    <span>{esc(_v18_game_time(game))}</span>
  </header>
  <div class="dd-stadium-name"><small>{esc(stadium)}</small><strong>{temp}</strong><span>{esc(description)}</span></div>
  <div class="dd-stadium-wind"><b>↗ {wind}</b><span>{esc(effect)}</span><em>{esc(grade)}</em></div>
  <footer><div><span>LF</span><b>{_v16_signed(lf)}</b></div><div><span>CF</span><b>{_v16_signed(cf)}</b></div><div><span>RF</span><b>{_v16_signed(rf)}</b></div><div><span>HR IMPACT</span><b>{safe_float(game.get('weather_impact')):+.1f}</b></div></footer>
</article></a>'''


def _v18_weather_hitter_rows(board: dict, game: dict) -> str:
    selected_key = _v17_game_key(game)
    hitters = [
        player for player in board.get("rankings", []) or []
        if str(player.get("weather_game_key") or player.get("schedule_game_key") or player.get("mlb_game_pk") or player.get("game_id") or "") == selected_key
        or str(player.get("game_id") or "") == str(game.get("game_id") or "")
    ]
    hitters.sort(key=lambda player: safe_float(player.get("dinger_score")), reverse=True)
    impact = safe_float(game.get("weather_impact"))
    rows: list[str] = []
    for rank, player in enumerate(hitters[:5], 1):
        base = probability_fraction(player.get("probability"))
        adjusted = max(0.0, min(.99, base * (1 + impact / 100.0)))
        rows.append(
            f'''<div class="dd-weather-hitter-row"><em>{rank}</em><b>{esc(player.get('player_name'))}</b><span>{esc(player.get('team_name'))}</span><small>{base*100:.1f}%</small><strong>{adjusted*100:.1f}%</strong><i>{impact:+.0f}%</i></div>'''
        )
    if not rows:
        rows.append('<div class="dd-weather-hitter-empty">Hitter board is waiting for matchup records.</div>')
    return ''.join(rows)


def _v18_weather_detail_panel(board: dict, game: dict) -> str:
    away = str(game.get("away_team_name") or "AWAY")
    home = str(game.get("home_team_name") or "HOME")
    stadium = str(game.get("stadium_name") or game.get("venue_name") or "Ballpark")
    image = str(game.get("stadium_image_url") or "")
    background = f"background-image:linear-gradient(180deg,rgba(2,8,18,.12),rgba(2,8,18,.78)),url('{esc(image)}');" if image else ""
    description = str(game.get("weather_description") or "Game-time ballpark weather")
    grade = str(game.get("weather_grade") or "—")
    reasons = [str(item) for item in (game.get("weather_reasons") or []) if item]
    ticker = "  •  ".join(reasons) or str(game.get("weather_error") or "Forecast provider connected; matchup weather is being prepared.")
    return f'''
<section class="dd-v18-weather-selected">
  <div class="dd-v18-weather-photo" style="{background}">
    <div class="dd-v18-weather-match"><b>{esc(away)} @ {esc(home)}</b><span>{esc(_v18_game_time(game))}</span></div>
    <div class="dd-v18-weather-photo-copy"><small>{esc(stadium)}</small><h2>{safe_float(game.get('temperature_f')):.0f}°F</h2><p>{esc(description)}</p></div>
  </div>
  <div class="dd-v18-weather-data">
    <header><div><span>SELECTED GAME</span><b>{esc(stadium)}</b></div><em>{esc(grade)}<small>WEATHER GRADE</small></em></header>
    <div class="dd-v18-weather-big"><i>☁</i><b>{safe_float(game.get('temperature_f')):.0f}°F</b><span>{esc(description)}</span></div>
    <div class="dd-v18-weather-metrics">
      <div><span>WIND</span><b>{safe_float(game.get('wind_speed_mph')):.0f} mph</b><small>{esc(str(game.get('wind_field_effect') or 'unknown').upper())}</small></div>
      <div><span>HUMIDITY</span><b>{safe_float(game.get('humidity_pct')):.0f}%</b><small>Game time</small></div>
      <div><span>PRESSURE</span><b>{safe_float(game.get('surface_pressure_hpa')):.0f}</b><small>hPa</small></div>
      <div><span>RAIN</span><b>{safe_float(game.get('precip_probability')):.0f}%</b><small>Probability</small></div>
    </div>
  </div>
  <div class="dd-v18-weather-hitters">
    <header><b>WEATHER-ADJUSTED HITTER BOARD</b><span>MODEL HR • ADJUSTED HR • IMPACT</span></header>
    <div class="dd-weather-hitter-head"><span>RANK</span><span>PLAYER</span><span>TEAM</span><span>MODEL</span><span>ADJ.</span><span>IMPACT</span></div>
    {_v18_weather_hitter_rows(board, game)}
  </div>
  <footer>⚡ {esc(ticker)}</footer>
</section>'''


def weather_center(board: dict) -> None:
    games = _v17_weather_games(board)
    requested = str(st.query_params.get("game") or "")
    selected = next((game for game in games if _v17_game_key(game) == requested), None)
    if selected is None and games:
        selected = next((game for game in games if game.get("weather_available")), games[0])

    summary = board.get("weather_summary", {}) or {}
    providers = ", ".join(summary.get("providers") or ["WeatherAPI / NWS"])
    hero(
        "BALLPARK <span>WEATHER COMMAND</span>",
        "Three ballparks per row. Select any game for the full stadium view, field-direction carry, game-time conditions, and weather-adjusted hitter board.",
        stats={"Games Today": len(games), "Data Source": providers, "Updated": board.get("date", "")},
    )
    if not games:
        st.error("No MLB games were returned for this slate. Confirm the selected date and refresh the model.")
        return

    st.markdown(
        '<div class="dd-stadium-grid">'
        + ''.join(_v18_weather_card(game, game is selected) for game in games)
        + '</div>',
        unsafe_allow_html=True,
    )
    if selected:
        st.markdown(_v18_weather_detail_panel(board, selected), unsafe_allow_html=True)

    errors = summary.get("errors") or []
    if errors and not summary.get("games_available"):
        with st.expander("Weather diagnostics"):
            for error in errors:
                st.code(str(error))


def _v18_sim_stat_card(label: str, value: str, subtitle: str, accent: str) -> str:
    return f'<div class="dd-v18-sim-stat" style="--sim-stat:{accent}"><i></i><b>{esc(value)}</b><span>{esc(label)}</span><small>{esc(subtitle)}</small></div>'


def game_sims(board: dict) -> None:
    from services.game_simulator import build_game_sims

    with st.spinner("Running 5,000 simulations per matchup..."):
        sims = build_game_sims(board, iterations=5000)
    if not sims:
        st.info("Game simulations are waiting for valid matchup and team data.")
        return

    requested = str(st.query_params.get("game") or "")
    selected = next((sim for sim in sims if str(sim.get("game_key")) == requested), sims[0])
    away = selected["away"]
    home = selected["home"]
    away_metrics = selected["teams"][away]
    home_metrics = selected["teams"][home]
    avg_hits = sum(safe_float(sim["teams"][sim["away"]].get("projected_hits")) + safe_float(sim["teams"][sim["home"]].get("projected_hits")) for sim in sims) / max(1, len(sims))
    home_win_avg = sum(safe_float(sim["teams"][sim["home"]].get("win_probability")) for sim in sims) / max(1, len(sims))
    projected_hr = sum(safe_float(sim["teams"][sim["away"]].get("projected_hr")) + safe_float(sim["teams"][sim["home"]].get("projected_hr")) for sim in sims)

    st.markdown(
        f'''<header class="dd-v18-sim-title"><h1>GAME SIMS</h1><span>AI-POWERED MLB GAME SIMULATIONS &amp; PROJECTIONS</span></header>
<div class="dd-v18-sim-summary">
  {_v18_sim_stat_card('GAMES SIMULATED', str(len(sims)), 'Full slate', '#a95dff')}
  {_v18_sim_stat_card('AVG. PROJECTED HITS', f'{avg_hits:.1f}', 'Across slate', '#34c7ff')}
  {_v18_sim_stat_card('HOME WIN PROB.', f'{home_win_avg*100:.1f}%', 'Average', '#35f28f')}
  {_v18_sim_stat_card('PROJECTED HR', f'{projected_hr:.1f}', 'Across slate', '#ff9f2f')}
  {_v18_sim_stat_card('SIMULATIONS', '5,000+', 'Per game', '#ff52dc')}
</div>''',
        unsafe_allow_html=True,
    )

    total_line = selected.get("sportsbook_total") or selected.get("total_line") or "—"
    over = selected.get("over_odds")
    under = selected.get("under_odds")
    st.markdown(
        f'''
<section class="dd-v18-sim-feature">
  <div class="dd-v18-sim-team away"><div class="brand"><img src="{team_logo(selected.get('away_id'))}"><span><small>AWAY</small><b>{esc(away)}</b><em>{esc(str(away_metrics.get('probable_pitcher') or 'Starter pending'))}</em></span></div><strong>{safe_float(away_metrics.get('win_probability'))*100:.0f}%</strong></div>
  <div class="dd-v18-sim-score"><span>PROJECTED SCORE</span><b>{safe_float(away_metrics.get('projected_runs')):.1f} <i>–</i> {safe_float(home_metrics.get('projected_runs')):.1f}</b><small>{esc(away)} win probability {safe_float(away_metrics.get('win_probability'))*100:.0f}%</small></div>
  <div class="dd-v18-sim-team home"><strong>{safe_float(home_metrics.get('win_probability'))*100:.0f}%</strong><div class="brand"><span><small>HOME</small><b>{esc(home)}</b><em>{esc(str(home_metrics.get('probable_pitcher') or 'Starter pending'))}</em></span><img src="{team_logo(selected.get('home_id'))}"></div></div>
  <div class="dd-v18-sim-breakdown away"><div><span>PROJ. RUNS</span><b>{safe_float(away_metrics.get('projected_runs')):.1f}</b></div><div><span>PROJ. HITS</span><b>{safe_float(away_metrics.get('projected_hits')):.1f}</b></div><div><span>PROJ. HR</span><b>{safe_float(away_metrics.get('projected_hr')):.1f}</b></div><div><span>PROJ. K'S</span><b>{safe_float(away_metrics.get('projected_so')):.1f}</b></div><div><span>PROJ. SB</span><b>{safe_float(away_metrics.get('projected_sb')):.1f}</b></div></div>
  <div class="dd21-sim-center-note"><span>MODEL OUTPUT</span><b>RUNS • HITS • HR • K • SB</b><small>Sportsbook totals hidden until the market feed is verified.</small></div>
  <div class="dd-v18-sim-breakdown home"><div><span>PROJ. RUNS</span><b>{safe_float(home_metrics.get('projected_runs')):.1f}</b></div><div><span>PROJ. HITS</span><b>{safe_float(home_metrics.get('projected_hits')):.1f}</b></div><div><span>PROJ. HR</span><b>{safe_float(home_metrics.get('projected_hr')):.1f}</b></div><div><span>PROJ. K'S</span><b>{safe_float(home_metrics.get('projected_so')):.1f}</b></div><div><span>PROJ. SB</span><b>{safe_float(home_metrics.get('projected_sb')):.1f}</b></div></div>
</section>
<div class="dd-sim-narrative"><i>✦</i><div><b>AI GAME READ</b><p>{esc(_sim_narrative(selected))}</p></div></div>''',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="dd-home-table-title"><div><i>◇</i><b>FULL SLATE SIMULATION BOARD</b><span>Click any matchup to load the full simulation above</span></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="dd-sim-click-board">' + ''.join(_v17_sim_card(sim, sim is selected) for sim in sims) + '</div>', unsafe_allow_html=True)


# ===== V20 AI-STADIUM WEATHER OVERRIDE =====

def _v20_weather_card(game: dict, selected: bool = False) -> str:
    from components.stadium_art import stadium_scene_data

    key = _v17_game_key(game)
    away = str(game.get("away_team_name") or "AWAY")
    home = str(game.get("home_team_name") or "HOME")
    stadium = str(game.get("stadium_name") or game.get("venue_name") or "MLB Ballpark")
    scene = stadium_scene_data(game)
    lf, cf, rf = _v16_zone_values(game)
    available = bool(game.get("weather_available"))
    temp = f'{safe_float(game.get("temperature_f")):.0f}°F' if available else "—"
    wind = f'{safe_float(game.get("wind_speed_mph")):.0f} mph' if available else "PENDING"
    grade = str(game.get("weather_grade") or "—")
    description = str(game.get("weather_description") or "Forecast pending")
    accent = weather_color(game) if available else "#ff6a4d"
    active = " active" if selected else ""
    background = (
        f"background-image:linear-gradient(180deg,rgba(1,7,15,.02),rgba(1,7,15,.40)),url('{scene}');"
        if scene else ""
    )
    return f'''
<a class="dd20-weather-card-link{active}" href="?view=weather&game={quote(key)}" target="_self">
<article class="dd20-weather-card" style="--weather-accent:{accent};{background}">
  <header>
    <div class="dd20-weather-match"><img src="{team_logo(game.get('away_team_id'))}"><b>{esc(away)} @ {esc(home)}</b><img src="{team_logo(game.get('home_team_id'))}"></div>
    <span>{esc(_v18_game_time(game))}</span>
  </header>
  <div class="dd20-weather-copy">
    <small>{esc(stadium)}</small>
    <div><strong>{temp}</strong><span>{esc(description)}</span></div>
  </div>
  <div class="dd20-weather-grade"><b>{esc(grade)}</b><span>WEATHER GRADE</span><small>{wind} • {esc(str(game.get('wind_field_effect') or 'unknown').upper())}</small></div>
  <footer><div><span>LF</span><b>{_v16_signed(lf)}</b></div><div><span>CF</span><b>{_v16_signed(cf)}</b></div><div><span>RF</span><b>{_v16_signed(rf)}</b></div></footer>
</article></a>'''


def _v20_weather_detail(board: dict, game: dict) -> str:
    from components.stadium_art import stadium_scene_data

    away = str(game.get("away_team_name") or "AWAY")
    home = str(game.get("home_team_name") or "HOME")
    stadium = str(game.get("stadium_name") or game.get("venue_name") or "MLB Ballpark")
    scene = stadium_scene_data(game, detail=True)
    background = (
        f"background-image:linear-gradient(90deg,rgba(1,7,15,.02),rgba(1,7,15,.38)),url('{scene}');"
        if scene else ""
    )
    description = str(game.get("weather_description") or "Game-time weather")
    grade = str(game.get("weather_grade") or "—")
    impact = safe_float(game.get("weather_impact"))
    lf, cf, rf = _v16_zone_values(game)
    reasons = " • ".join(str(item) for item in (game.get("weather_reasons") or []) if item)
    return f'''
<section class="dd20-weather-detail">
  <div class="dd20-weather-detail-scene" style="{background}">
    <header><b>{esc(away)} @ {esc(home)}</b><span>{esc(_v18_game_time(game))}</span></header>
    <div><small>{esc(stadium)}</small><h2>{safe_float(game.get('temperature_f')):.0f}°F</h2><p>{esc(description)}</p></div>
  </div>
  <div class="dd20-weather-detail-data">
    <header><span>GAME-TIME CONDITIONS</span><b>{esc(stadium)}</b><em>{esc(grade)}<small>WEATHER GRADE</small></em></header>
    <div class="dd20-weather-detail-main"><i>☁</i><b>{safe_float(game.get('temperature_f')):.0f}°F</b><span>{esc(description)}</span></div>
    <div class="dd20-weather-detail-metrics">
      <div><span>WIND</span><b>{safe_float(game.get('wind_speed_mph')):.0f} mph</b><small>{esc(str(game.get('wind_field_effect') or 'unknown').upper())}</small></div>
      <div><span>HUMIDITY</span><b>{safe_float(game.get('humidity_pct')):.0f}%</b><small>Game time</small></div>
      <div><span>PRESSURE</span><b>{safe_float(game.get('surface_pressure_hpa')):.0f}</b><small>hPa</small></div>
      <div><span>RAIN</span><b>{safe_float(game.get('precip_probability')):.0f}%</b><small>Probability</small></div>
    </div>
    <div class="dd20-weather-zones"><div><span>LF</span><b>{_v16_signed(lf)}</b></div><div><span>CF</span><b>{_v16_signed(cf)}</b></div><div><span>RF</span><b>{_v16_signed(rf)}</b></div><div><span>OVERALL</span><b>{impact:+.1f}</b></div></div>
  </div>
  <div class="dd20-weather-hitters">
    <header><b>WEATHER-ADJUSTED HITTER BOARD</b><span>MODEL HR • ADJUSTED HR • IMPACT</span></header>
    <div class="dd-weather-hitter-head"><span>RANK</span><span>PLAYER</span><span>TEAM</span><span>MODEL</span><span>ADJ.</span><span>IMPACT</span></div>
    {_v18_weather_hitter_rows(board, game)}
  </div>
  <footer>⚡ {esc(reasons or "Forecast connected. Weather impact is now shared with Dashboard, Rankings, Team Sheets, and Parlay Lab.")}</footer>
</section>'''


def weather_center(board: dict) -> None:
    games = _v17_weather_games(board)
    requested = str(st.query_params.get("game") or "")
    selected = next((game for game in games if _v17_game_key(game) == requested), None)
    if selected is None and games:
        selected = next((game for game in games if game.get("weather_available")), games[0])

    summary = board.get("weather_summary", {}) or {}
    providers = ", ".join(summary.get("providers") or ["WeatherAPI / NWS"])
    st.markdown(
        f'''<section class="dd20-weather-hero dd21-weather-hero"><div><span>MLB HOME RUN INTELLIGENCE</span><h1>BALLPARK <em>WEATHER COMMAND</em></h1></div><aside><div><span>GAMES TODAY</span><b>{len(games)}</b></div><div><span>CONNECTED</span><b>{summary.get("games_available", 0)}</b></div><div><span>DATA SOURCE</span><b>{esc(providers)}</b></div></aside></section>''',
        unsafe_allow_html=True,
    )
    if not games:
        st.error("No MLB games were returned for this slate.")
        return

    st.markdown(
        '<div class="dd20-weather-grid">'
        + ''.join(_v20_weather_card(game, game is selected) for game in games)
        + '</div>',
        unsafe_allow_html=True,
    )
    if selected:
        st.markdown(_v20_weather_detail(board, selected), unsafe_allow_html=True)

    errors = summary.get("errors") or []
    if errors and not summary.get("games_available"):
        with st.expander("Weather diagnostics"):
            for error in errors:
                st.code(str(error))


# ===== V22 WEATHER MOCKUP + GAME SIM CLARITY OVERRIDES =====

def _v22_weather_icon(description: str) -> str:
    text = str(description or "").lower()
    if "thunder" in text or "storm" in text:
        return "⛈"
    if "rain" in text or "shower" in text:
        return "🌧"
    if "snow" in text:
        return "🌨"
    if "clear" in text:
        return "☾"
    if "sun" in text:
        return "☀"
    if "cloud" in text or "overcast" in text:
        return "⛅"
    return "◐"


def _v22_updated(board: dict) -> str:
    raw = str(board.get("updated_at") or "")
    if not raw:
        return str(board.get("date") or "")
    try:
        from datetime import datetime
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed.strftime("%-I:%M %p ET")
    except Exception:
        return raw[:16]


def _v22_wind_direction(game: dict) -> str:
    value = str(
        game.get("wind_direction_cardinal")
        or game.get("wind_direction")
        or game.get("wind_field_effect")
        or "—"
    ).upper().replace("_", " ")
    return value


def _v22_weather_card(game: dict) -> str:
    from components.stadium_art import stadium_scene_data

    key = _v17_game_key(game)
    away = str(game.get("away_team_name") or "AWAY")
    home = str(game.get("home_team_name") or "HOME")
    stadium = str(game.get("stadium_name") or game.get("venue_name") or "MLB Ballpark")
    scene = stadium_scene_data(game)
    lf, cf, rf = _v16_zone_values(game)
    impact = safe_float(game.get("weather_impact"))
    grade = str(game.get("weather_grade") or "—")
    available = bool(game.get("weather_available"))
    temp = f"{safe_float(game.get('temperature_f')):.0f}°F" if available else "—"
    wind = f"{safe_float(game.get('wind_speed_mph')):.0f} mph" if available else "—"
    direction = _v22_wind_direction(game)
    description = str(game.get("weather_description") or "Forecast pending")
    accent = weather_color(game) if available else "#28bfff"
    icon = _v22_weather_icon(description)
    background = (
        f"background-image:linear-gradient(90deg,rgba(1,7,14,.18),rgba(1,7,14,.02) 52%,rgba(1,7,14,.18)),"
        f"linear-gradient(180deg,rgba(1,7,14,.05),rgba(1,7,14,.24)),url('{scene}');"
        if scene else ""
    )

    parts = [
        f'<a class="dd22-weather-card-link" href="?view=weather&game={quote(key)}" target="_self" aria-label="Open {esc(away)} at {esc(home)} weather">',
        f'<article class="dd22-weather-card" style="--wx:{accent};{background}">',
        '<header>',
        '<div class="dd22-weather-match">',
        f'<img src="{team_logo(game.get("away_team_id"))}" alt="{esc(away)}">',
        '<span>VS</span>',
        f'<img src="{team_logo(game.get("home_team_id"))}" alt="{esc(home)}">',
        f'<b>{esc(away)} @ {esc(home)}</b>',
        '</div>',
        f'<time>{esc(_v18_game_time(game))} ET</time>',
        '</header>',
        '<div class="dd22-weather-main">',
        '<div class="dd22-weather-copy">',
        f'<small>{esc(stadium)}</small>',
        f'<strong>{temp}</strong>',
        f'<span><i>{icon}</i>{esc(description)}</span>',
        '</div>',
        '<aside class="dd22-weather-grade">',
        f'<small>{wind}</small>',
        f'<em>{esc(direction)}</em>',
        f'<b>{esc(grade)}</b>',
        '<span>WEATHER<br>GRADE</span>',
        '</aside>',
        '</div>',
        '<footer>',
        f'<div><span>LF</span><b>{_v16_signed(lf)}</b></div>',
        f'<div><span>CF</span><b>{_v16_signed(cf)}</b></div>',
        f'<div><span>RF</span><b>{_v16_signed(rf)}</b></div>',
        f'<div><span>HR IMPACT</span><b>{impact:+.1f}</b></div>',
        '</footer>',
        '</article>',
        '</a>',
    ]
    return "".join(parts)

def _v22_weather_detail(board: dict, game: dict) -> str:
    from components.stadium_art import stadium_scene_data

    away = str(game.get("away_team_name") or "AWAY")
    home = str(game.get("home_team_name") or "HOME")
    stadium = str(game.get("stadium_name") or game.get("venue_name") or "MLB Ballpark")
    scene = stadium_scene_data(game, detail=True)
    lf, cf, rf = _v16_zone_values(game)
    impact = safe_float(game.get("weather_impact"))
    description = str(game.get("weather_description") or "Game-time weather")
    reasons = " • ".join(str(item) for item in (game.get("weather_reasons") or []) if item)
    background = (
        f"background-image:linear-gradient(90deg,rgba(1,7,14,.12),rgba(1,7,14,.02) 58%,rgba(1,7,14,.22)),"
        f"linear-gradient(180deg,rgba(1,7,14,.02),rgba(1,7,14,.28)),url('{scene}');"
        if scene else ""
    )

    parts = [
        '<a class="dd22-weather-back" href="?view=weather" target="_self">← ALL BALLPARKS</a>',
        '<section class="dd22-weather-detail">',
        f'<div class="dd22-weather-detail-scene" style="{background}">',
        '<header>',
        '<div>',
        f'<img src="{team_logo(game.get("away_team_id"))}" alt="{esc(away)}">',
        f'<b>{esc(away)} @ {esc(home)}</b>',
        f'<img src="{team_logo(game.get("home_team_id"))}" alt="{esc(home)}">',
        '</div>',
        f'<time>{esc(_v18_game_time(game))} ET</time>',
        '</header>',
        '<div class="dd22-weather-detail-copy">',
        f'<small>{esc(stadium)}</small>',
        f'<h1>{safe_float(game.get("temperature_f")):.0f}°F</h1>',
        f'<p>{_v22_weather_icon(description)} {esc(description)}</p>',
        '</div>',
        '<aside>',
        f'<small>{safe_float(game.get("wind_speed_mph")):.0f} mph</small>',
        f'<em>{esc(_v22_wind_direction(game))}</em>',
        f'<b>{esc(game.get("weather_grade") or "—")}</b>',
        '<span>WEATHER GRADE</span>',
        '</aside>',
        '</div>',
        '<div class="dd22-weather-detail-strip">',
        f'<div><span>LEFT FIELD</span><b>{_v16_signed(lf)}</b></div>',
        f'<div><span>CENTER FIELD</span><b>{_v16_signed(cf)}</b></div>',
        f'<div><span>RIGHT FIELD</span><b>{_v16_signed(rf)}</b></div>',
        f'<div><span>HR IMPACT</span><b>{impact:+.1f}</b></div>',
        '</div>',
        '<div class="dd22-weather-detail-metrics">',
        f'<div><span>HUMIDITY</span><b>{safe_float(game.get("humidity_pct")):.0f}%</b></div>',
        f'<div><span>RAIN CHANCE</span><b>{safe_float(game.get("precip_probability")):.0f}%</b></div>',
        f'<div><span>PRESSURE</span><b>{safe_float(game.get("surface_pressure_hpa")):.0f} hPa</b></div>',
        f'<div><span>ROOF</span><b>{esc(str(game.get("roof_status") or game.get("roof_type") or "Outdoor").title())}</b></div>',
        '</div>',
        '<section class="dd22-weather-hitters">',
        '<header><b>WEATHER-ADJUSTED HITTER BOARD</b><span>MODEL HR • WEATHER-ADJUSTED HR • IMPACT</span></header>',
        '<div class="dd-weather-hitter-head"><span>RANK</span><span>PLAYER</span><span>TEAM</span><span>MODEL</span><span>ADJ.</span><span>IMPACT</span></div>',
        _v18_weather_hitter_rows(board, game),
        '</section>',
        f'<div class="dd22-weather-ticker">⚡ {esc(reasons or "Live game-time weather connected to this matchup.")}</div>',
        '</section>',
    ]
    return "".join(parts)

def weather_center(board: dict) -> None:
    games = _v17_weather_games(board)
    requested = str(st.query_params.get("game") or "")
    selected = next((game for game in games if _v17_game_key(game) == requested), None)

    summary = board.get("weather_summary", {}) or {}
    providers = " / ".join(summary.get("providers") or ["WeatherAPI", "NWS"])

    if selected is not None:
        st.markdown(_v22_weather_detail(board, selected), unsafe_allow_html=True)
        return

    st.markdown(
        f'''
<section class="dd22-weather-hero">
  <div>
    <span>MLB HOME RUN INTELLIGENCE</span>
    <h1>BALLPARK <em>WEATHER COMMAND</em></h1>
  </div>
  <aside>
    <div><span>GAMES TODAY</span><b>{len(games)}</b></div>
    <div><span>DATA SOURCE</span><b>{esc(providers)}</b></div>
    <div><span>UPDATED</span><b>{esc(_v22_updated(board))}</b><small>● Live</small></div>
  </aside>
</section>
''',
        unsafe_allow_html=True,
    )

    if not games:
        st.error("No MLB games were returned for this slate.")
        return

    st.markdown(
        '<div class="dd22-weather-grid">'
        + "".join(_v22_weather_card(game) for game in games)
        + "</div>",
        unsafe_allow_html=True,
    )


def _v22_sim_row(sim: dict, active: bool = False) -> str:
    away = sim["away"]
    home = sim["home"]
    away_metrics = sim["teams"][away]
    home_metrics = sim["teams"][home]
    key = str(sim.get("game_key") or "")
    away_hits = safe_float(away_metrics.get("projected_hits"))
    home_hits = safe_float(home_metrics.get("projected_hits"))
    total_hr = safe_float(away_metrics.get("projected_hr")) + safe_float(home_metrics.get("projected_hr"))
    return f'''
<a class="dd-sim-row-link{' active' if active else ''}" href="?view=game-sims&game={quote(key)}" target="_self">
  <div class="dd-sim-row dd22-sim-row">
    <div class="match"><img src="{team_logo(sim.get('away_id'))}"><b>{esc(away)} @ {esc(home)}</b><img src="{team_logo(sim.get('home_id'))}"></div>
    <div><span>WIN PROB</span><b>{safe_float(away_metrics.get('win_probability'))*100:.0f}% / {safe_float(home_metrics.get('win_probability'))*100:.0f}%</b></div>
    <div><span>PROJ. SCORE</span><b>{esc(sim.get('projected_score'))}</b></div>
    <div><span>TEAM HITS</span><b>{away_hits:.1f} / {home_hits:.1f}</b></div>
    <div><span>PROJ. HR</span><b>{total_hr:.1f}</b></div>
    <i>›</i>
  </div>
</a>'''


def game_sims(board: dict) -> None:
    from services.game_simulator import build_game_sims

    with st.spinner("Running 5,000 simulations per matchup..."):
        sims = build_game_sims(board, iterations=5000)
    if not sims:
        st.info("Game simulations are waiting for valid matchup and team data.")
        return

    requested = str(st.query_params.get("game") or "")
    selected = next((sim for sim in sims if str(sim.get("game_key")) == requested), sims[0])
    away = selected["away"]
    home = selected["home"]
    away_metrics = selected["teams"][away]
    home_metrics = selected["teams"][home]

    avg_team_hits = (
        sum(
            safe_float(sim["teams"][sim["away"]].get("projected_hits"))
            + safe_float(sim["teams"][sim["home"]].get("projected_hits"))
            for sim in sims
        )
        / max(1, len(sims))
        / 2
    )
    home_win_avg = sum(
        safe_float(sim["teams"][sim["home"]].get("win_probability"))
        for sim in sims
    ) / max(1, len(sims))
    projected_hr = sum(
        safe_float(sim["teams"][sim["away"]].get("projected_hr"))
        + safe_float(sim["teams"][sim["home"]].get("projected_hr"))
        for sim in sims
    )

    st.markdown(
        f'''<header class="dd-v18-sim-title"><h1>GAME SIMS</h1><span>AI-POWERED MLB GAME SIMULATIONS &amp; PROJECTIONS</span></header>
<div class="dd-v18-sim-summary">
  {_v18_sim_stat_card('GAMES SIMULATED', str(len(sims)), 'Full slate', '#a95dff')}
  {_v18_sim_stat_card('AVG. TEAM HITS', f'{avg_team_hits:.1f}', 'Per team, not combined', '#34c7ff')}
  {_v18_sim_stat_card('HOME WIN PROB.', f'{home_win_avg*100:.1f}%', 'Average', '#35f28f')}
  {_v18_sim_stat_card('PROJECTED HR', f'{projected_hr:.1f}', 'Across slate', '#ff9f2f')}
  {_v18_sim_stat_card('SIMULATIONS', '5,000+', 'Per game', '#ff52dc')}
</div>''',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'''
<section class="dd-v18-sim-feature">
  <div class="dd-v18-sim-team away"><div class="brand"><img src="{team_logo(selected.get('away_id'))}"><span><small>AWAY</small><b>{esc(away)}</b><em>{esc(str(away_metrics.get('probable_pitcher') or 'Starter pending'))}</em></span></div><strong>{safe_float(away_metrics.get('win_probability'))*100:.0f}%</strong></div>
  <div class="dd-v18-sim-score"><span>PROJECTED SCORE</span><b>{safe_float(away_metrics.get('projected_runs')):.1f} <i>–</i> {safe_float(home_metrics.get('projected_runs')):.1f}</b><small>{esc(away)} win probability {safe_float(away_metrics.get('win_probability'))*100:.0f}%</small></div>
  <div class="dd-v18-sim-team home"><strong>{safe_float(home_metrics.get('win_probability'))*100:.0f}%</strong><div class="brand"><span><small>HOME</small><b>{esc(home)}</b><em>{esc(str(home_metrics.get('probable_pitcher') or 'Starter pending'))}</em></span><img src="{team_logo(selected.get('home_id'))}"></div></div>

  <div class="dd-v18-sim-breakdown away">
    <div><span>PROJ. RUNS</span><b>{safe_float(away_metrics.get('projected_runs')):.1f}</b></div>
    <div><span>PROJ. HITS</span><b>{safe_float(away_metrics.get('projected_hits')):.1f}</b></div>
    <div><span>PROJ. HR</span><b>{safe_float(away_metrics.get('projected_hr')):.1f}</b></div>
    <div><span>PROJ. K'S</span><b>{safe_float(away_metrics.get('projected_so')):.1f}</b></div>
    <div><span>PROJ. SB</span><b>{safe_float(away_metrics.get('projected_sb')):.1f}</b></div>
  </div>

  <div class="dd22-sim-center-note">
    <span>HIT PROJECTIONS</span>
    <b>{safe_float(away_metrics.get('projected_hits')):.1f} AWAY / {safe_float(home_metrics.get('projected_hits')):.1f} HOME</b>
    <small>These are per-team estimates. The old 15+ number was the two-team combined total.</small>
  </div>

  <div class="dd-v18-sim-breakdown home">
    <div><span>PROJ. RUNS</span><b>{safe_float(home_metrics.get('projected_runs')):.1f}</b></div>
    <div><span>PROJ. HITS</span><b>{safe_float(home_metrics.get('projected_hits')):.1f}</b></div>
    <div><span>PROJ. HR</span><b>{safe_float(home_metrics.get('projected_hr')):.1f}</b></div>
    <div><span>PROJ. K'S</span><b>{safe_float(home_metrics.get('projected_so')):.1f}</b></div>
    <div><span>PROJ. SB</span><b>{safe_float(home_metrics.get('projected_sb')):.1f}</b></div>
  </div>
</section>

<div class="dd-sim-narrative"><i>✦</i><div><b>AI GAME READ</b><p>{esc(_sim_narrative(selected))}</p></div></div>''',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="dd-home-table-title"><div><i>◇</i><b>FULL SLATE SIMULATION BOARD</b><span>Click any matchup to load the full simulation above</span></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="dd-sim-click-board">'
        + ''.join(_v22_sim_row(sim, sim is selected) for sim in sims)
        + '</div>',
        unsafe_allow_html=True,
    )
