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


def settings(board: dict) -> None:
    st.markdown(
        '''<section class="dd25-page-hero"><span>APPLICATION CONTROL CENTER</span><h1>SITE <em>SETTINGS</em></h1><p>Control display density, startup behavior, and live-data refresh preferences.</p></section>''',
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

    sources = board.get("data_sources", {}) or {}
    tiles = "".join(
        f'<div><span>{esc(str(name))}</span><b>{esc(str(status))}</b></div>'
        for name, status in sources.items()
    )
    st.markdown('<section class="dd25-source-panel"><header><b>CONNECTED DATA SOURCES</b></header><div>' + tiles + '</div></section>', unsafe_allow_html=True)
