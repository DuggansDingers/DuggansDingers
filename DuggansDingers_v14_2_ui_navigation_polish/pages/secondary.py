from __future__ import annotations

import secrets

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
