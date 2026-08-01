from __future__ import annotations

from html import escape as esc
import math

import streamlit as st

from components.ui import headshot, odds, probability_fraction, safe_float, safe_int, team_logo


def _pitcher_image(player: dict) -> str:
    pitcher_id = safe_int(player.get("opposing_pitcher_id"))
    if pitcher_id:
        return headshot(pitcher_id, 120)
    return team_logo(player.get("opponent_team_id") or player.get("opposing_team_id"))


def _leaders(rankings: list[dict]) -> str:
    rows = []
    for rank, player in enumerate(rankings[:5], 1):
        probability = probability_fraction(player.get("probability")) * 100
        score = safe_float(player.get("dinger_score"))
        pitcher = str(player.get("opposing_pitcher") or "Starter pending")
        hand = str(player.get("opposing_pitcher_hand") or "—")
        rows.append(
            f'<a class="dd33-leader-row" href="?view=player-intelligence&player={safe_int(player.get("player_id"))}" target="_self">'
            f'<span class="rank">{rank}</span>'
            f'<img class="hitter" src="{headshot(player.get("player_id"), 150)}">'
            f'<div class="player"><b>{esc(str(player.get("player_name") or "—"))}</b><span>{esc(str(player.get("team_name") or "—"))}</span></div>'
            f'<div class="score"><small>DINGER SCORE</small><b>{score:.1f}</b></div>'
            f'<div class="prob"><small>HR PROB</small><b>{probability:.0f}%</b></div>'
            f'<span class="vs">VS</span>'
            f'<img class="pitcher" src="{_pitcher_image(player)}">'
            f'<div class="starter"><b>{esc(pitcher)}</b><span>{esc(hand)}HP</span></div>'
            '</a>'
        )
    return '<section class="dd33-panel dd33-leaders"><header><b>TODAY’S TOP DINGERZ</b><a href="?view=daily-board" target="_self">VIEW FULL BOARD</a></header>' + "".join(rows) + '</section>'


def _overview(board: dict, rankings: list[dict]) -> str:
    games = len(board.get("games_meta", []) or []) or safe_int(board.get("games"))
    weather_games = {
        str(game.get("game_id") or game.get("id"))
        for game in (board.get("games_meta", []) or [])
        if game.get("weather_available")
    }
    priced = sum(1 for player in rankings if player.get("best_odds") is not None)
    return (
        '<section class="dd33-panel dd33-overview"><header><b>SLATE OVERVIEW</b></header>'
        '<div class="dd33-overview-grid">'
        f'<div><i>▣</i><b>{games}</b><span>GAMES</span></div>'
        f'<div><i>♧</i><b>{len(rankings)}</b><span>HITTERS</span></div>'
        f'<div><i>☁</i><b>{len(weather_games)}</b><span>WEATHER<br><em>LIVE</em></span></div>'
        f'<div><i>✓</i><b>{priced}</b><span>PRICED PROPS</span></div>'
        '</div><footer>MODEL STATUS <i></i> ONLINE</footer></section>'
    )


def _weather_panel(board: dict) -> str:
    games = [g for g in (board.get("games_meta", []) or []) if g.get("weather_available")]
    favorable = sum(1 for g in games if safe_float(g.get("weather_impact")) >= 2)
    negative = sum(1 for g in games if safe_float(g.get("weather_impact")) <= -1)
    neutral = max(0, len(games) - favorable - negative)
    dots = []
    positions = [(18,62),(28,48),(40,72),(54,41),(64,62),(75,34),(86,55),(34,31),(59,80),(78,75),(46,54),(91,28)]
    for i, (x,y) in enumerate(positions[:max(1,min(len(games),len(positions)))]):
        impact = safe_float(games[i].get("weather_impact")) if i < len(games) else 0
        color = "#45f276" if impact >= 2 else "#ffcf32" if impact > -1 else "#ff4b43"
        dots.append(f'<i style="left:{x}%;top:{y}%;background:{color};box-shadow:0 0 10px {color}"></i>')
    return (
        '<section class="dd33-panel dd33-weather"><header><b>☁ WEATHER IMPACT</b></header>'
        '<div class="dd33-weather-body"><div class="legend">'
        f'<span class="good">● FAVORABLE <b>{favorable} GAMES</b></span>'
        f'<span class="neutral">● NEUTRAL <b>{neutral} GAMES</b></span>'
        f'<span class="bad">● NEGATIVE <b>{negative} GAMES</b></span></div>'
        '<div class="map"><svg viewBox="0 0 230 120"><path d="M9 28 24 19l20 2 10-9 18 8 18-3 16 12 25 2 9 9 20-1 12 13 26 5 14 17-9 19-34 5-24-2-20 9-23-5-21 2-16-11-28-3-8-17 7-13-12-13Z"/></svg>'
        + "".join(dots) + '</div></div></section>'
    )


def _live_props(rankings: list[dict]) -> str:
    rows = []
    for player in rankings[:3]:
        prob = probability_fraction(player.get("probability")) * 100
        price = player.get("best_odds") if player.get("best_odds") is not None else player.get("fair_odds")
        rows.append(
            '<div class="dd33-prop-row">'
            f'<img src="{headshot(player.get("player_id"), 90)}"><div><b>{esc(str(player.get("player_name") or "—"))}</b><span>Over 0.5 HR</span></div>'
            f'<strong>{prob:.0f}%</strong><i><em style="width:{prob:.1f}%"></em></i><b class="price">{odds(price)}</b>'
            '</div>'
        )
    return '<section class="dd33-panel dd33-live-props"><header><b>LIVE PROPS TRACKER</b><a href="?view=props">VIEW ALL</a></header>' + "".join(rows) + '</section>'


def _kitchen() -> str:
    return (
        '<section class="dd33-panel dd33-kitchen"><header><b>THE KITCHEN</b><a href="?view=the-kitchen">BUILD PARLAYS</a></header>'
        '<a href="?view=the-kitchen" class="recipe hr"><span>⚾</span><div><b>HR PARLAYS</b><p>Cook up the hottest home run parlays</p></div></a>'
        '<a href="?view=the-kitchen" class="recipe mixed"><span>♨</span><div><b>MIXED PROP PARLAYS</b><p>Combine HR, Hits, Ks, SBs & more</p></div></a>'
        '</section>'
    )


def render(board: dict) -> None:
    rankings = list(board.get("rankings", []) or [])
    if not rankings:
        st.error("No rankings are available. Refresh the slate data.")
        return

    st.markdown(
        '<main class="dd33-home-grid">'
        '<div class="dd33-col-left">' + _leaders(rankings) + '</div>'
        '<div class="dd33-col-center">' + _overview(board, rankings) + _live_props(rankings) + '</div>'
        '<div class="dd33-col-right">' + _weather_panel(board) + _kitchen() + '</div>'
        '</main>'
        '<footer class="dd33-brand-footer">REAL DATA. <b>SMART MODELS.</b> BETTER DECISIONS. <em>MORE WINS.</em></footer>',
        unsafe_allow_html=True,
    )
