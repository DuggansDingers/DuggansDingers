from __future__ import annotations

from html import escape as esc

import streamlit as st

from components.ui import odds, probability_fraction, safe_float, safe_int


def _alerts(board: dict) -> list[dict]:
    players = list(board.get("rankings", []) or [])
    alerts: list[dict] = []
    if players:
        top = max(players, key=lambda p: safe_float(p.get("dinger_score")))
        alerts.append({"level":"elite","title":"Top Model Play","body":f"{top.get('player_name')} leads the slate with a {safe_float(top.get('dinger_score')):.1f} Dinger Score and {probability_fraction(top.get('probability'))*100:.1f}% HR probability."})
        hot = max(players, key=lambda p: safe_int(p.get("last_7_home_runs")))
        alerts.append({"level":"hot","title":"Hot Bat Alert","body":f"{hot.get('player_name')} has {safe_int(hot.get('last_7_home_runs'))} home runs over the last seven games."})
        value = max(players, key=lambda p: safe_float(p.get("edge_pct")) if p.get("edge_pct") is not None else -999)
        if value.get("edge_pct") is not None:
            alerts.append({"level":"value","title":"Sportsbook Edge","body":f"{value.get('player_name')} shows {safe_float(value.get('edge_pct')):+.1f}% model edge at {value.get('best_book') or 'the best available book'} {odds(value.get('best_odds'))}."})
        matchup = max(players, key=lambda p: safe_float(p.get("pitcher_hr9")))
        if matchup.get("pitching_data_available"):
            alerts.append({"level":"matchup","title":"Pitcher Target","body":f"{matchup.get('player_name')} faces {matchup.get('opposing_pitcher') or 'the projected starter'}, who has allowed {safe_float(matchup.get('pitcher_hr9')):.2f} HR/9."})

    weather_games = [game for game in board.get("games_meta", []) or [] if game.get("weather_available")]
    if weather_games:
        best = max(weather_games, key=lambda g: safe_float(g.get("weather_impact")))
        alerts.append({"level":"weather","title":"Weather Boost","body":f"{best.get('away_team_name')} at {best.get('home_team_name')} carries the slate's strongest weather boost at {safe_float(best.get('weather_impact')):+.1f}."})
        risky = [g for g in weather_games if safe_float(g.get("precip_probability")) >= 40]
        for game in risky[:2]:
            alerts.append({"level":"risk","title":"Rain Risk","body":f"{game.get('away_team_name')} at {game.get('home_team_name')} has a {safe_float(game.get('precip_probability')):.0f}% precipitation probability."})
    return alerts


def news_alerts(board: dict) -> None:
    alerts = _alerts(board)
    st.session_state.last_alert_count = len(alerts)
    st.markdown(
        f'''<section class="dd25-page-hero"><span>LIVE INTELLIGENCE FEED</span><h1>NEWS &amp; <em>ALERTS</em></h1><p>Automated model, matchup, weather, and sportsbook alerts generated from the current slate.</p><aside><div><span>ACTIVE ALERTS</span><b>{len(alerts)}</b></div><div><span>SLATE</span><b>{esc(str(board.get('date') or 'Today'))}</b></div></aside></section>''',
        unsafe_allow_html=True,
    )
    cards = []
    for item in alerts:
        cards.append(
            f'''<article class="dd25-alert {esc(item['level'])}"><i></i><div><span>{esc(item['title'])}</span><p>{esc(item['body'])}</p></div><b>LIVE</b></article>'''
        )
    st.markdown('<div class="dd25-alert-grid">' + "".join(cards) + '</div>', unsafe_allow_html=True)


def _configured(*names: str) -> bool:
    try:
        return any(bool(str(st.secrets.get(name, "")).strip()) for name in names)
    except Exception:
        return False


def _source_statuses(board: dict) -> list[dict]:
    players = list(board.get("rankings", []) or [])
    games = list(board.get("games_meta", []) or [])
    weather_count = sum(1 for game in games if game.get("weather_available"))
    priced_count = sum(1 for player in players if player.get("best_odds") is not None)
    pitcher_count = sum(
        1 for player in players
        if str(player.get("opposing_pitcher") or "").lower()
        not in {"", "not announced", "awaiting announcement", "projected starter"}
    )
    statcast_count = sum(
        1 for player in players
        if player.get("statcast_available")
        or safe_float(player.get("barrel_pct")) > 0
        or safe_float(player.get("hard_hit_pct")) > 0
    )

    def row(name: str, state: str, detail: str) -> dict:
        return {"name": name, "state": state, "detail": detail}

    return [
        row("Ballpark Pal", "connected" if players else ("configured" if _configured("BALLPARKPAL_API_KEY") else "missing"), f"{len(players)} ranked hitters" if players else "API key not detected"),
        row("MLB Stats", "connected" if any(safe_int(p.get("season_home_runs")) for p in players) else "waiting", "Season and rolling history loaded" if players else "Waiting for board data"),
        row("Weather", "connected" if weather_count else ("configured" if _configured("WEATHERAPI_KEY", "WEATHER_API_KEY", "VISUAL_CROSSING_API_KEY") else "missing"), f"{weather_count} game forecasts loaded" if weather_count else "Configured; no forecast rows in this board" if _configured("WEATHERAPI_KEY", "WEATHER_API_KEY", "VISUAL_CROSSING_API_KEY") else "Add WEATHERAPI_KEY"),
        row("Sportsbook Odds", "connected" if priced_count else ("configured" if _configured("ODDS_API_IO_KEY") else "missing"), f"{priced_count} priced players matched" if priced_count else "Configured; props not returned yet" if _configured("ODDS_API_IO_KEY") else "Add ODDS_API_IO_KEY"),
        row("Statcast", "connected" if statcast_count else ("snapshot" if board.get("fast_start") else "waiting"), f"{statcast_count} hitter profiles loaded" if statcast_count else "Available through the prepared snapshot builder" if board.get("fast_start") else "Waiting for Statcast refresh"),
        row("Probable Pitchers", "connected" if pitcher_count else "waiting", f"{pitcher_count} hitters matched to starters" if pitcher_count else "MLB probable starters have not populated"),
        row("Fast Start Snapshot", "connected" if board.get("fast_start") else "live", "Prepared snapshot is active" if board.get("fast_start") else "Live fallback is active for this date"),
    ]


def settings(board: dict) -> None:
    st.markdown(
        '<section class="dd25-page-hero dd26-settings-hero"><span>APPLICATION CONTROL CENTER</span><h1>SITE <em>SETTINGS</em></h1><p>Control display density, startup behavior, and live-data refresh preferences. Connection cards below are inferred from data actually loaded and configured secret names, never stale labels.</p></section>',
        unsafe_allow_html=True,
    )
    left, right = st.columns(2)
    with left:
        st.subheader("Display")
        st.toggle("Compact tables", key="setting_compact_tables", value=bool(st.session_state.get("setting_compact_tables", False)))
        st.toggle("Reduce animations", key="setting_reduce_motion", value=bool(st.session_state.get("setting_reduce_motion", False)))
        st.toggle("Show sportsbook prices on player cards", key="setting_show_odds", value=bool(st.session_state.get("setting_show_odds", True)))
        st.slider("Players shown per ranking page", 10, 50, int(st.session_state.get("setting_player_count", 25)), 5, key="setting_player_count")
    with right:
        st.subheader("Data")
        st.toggle("Prefer prepared fast-start snapshot", key="setting_fast_start", value=bool(st.session_state.get("setting_fast_start", True)))
        st.toggle("Load weather on dashboard", key="setting_dashboard_weather", value=bool(st.session_state.get("setting_dashboard_weather", True)))
        st.toggle("Load sportsbook prices on dashboard", key="setting_dashboard_odds", value=bool(st.session_state.get("setting_dashboard_odds", True)))
        if st.button("Clear cache and refresh live data", use_container_width=True):
            from data_service import load_board
            load_board.clear()
            st.session_state["_force_live_refresh"] = True
            st.rerun()

    cards = []
    for source in _source_statuses(board):
        cards.append(
            f'<article class="dd26-source-card {esc(source["state"])}"><i></i><div><span>{esc(source["name"])}</span><b>{esc(source["state"].replace("_", " ").upper())}</b><p>{esc(source["detail"])}</p></div></article>'
        )
    st.markdown(
        '<section class="dd26-source-panel"><header><div><span>CONNECTION HEALTH</span><b>LIVE DATA SOURCES</b></div><em>Secret values remain hidden</em></header><div>'
        + "".join(cards)
        + '</div></section>',
        unsafe_allow_html=True,
    )
