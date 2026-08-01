from __future__ import annotations

from html import escape as esc
from statistics import mean
from urllib.parse import quote

import streamlit as st

from components.stadium_art import stadium_scene_data
from components.ui import headshot, odds, probability_fraction, safe_float, safe_int, team_logo


def _game_key(value: object) -> str:
    return str(value or "")


def _groups(board: dict) -> list[dict]:
    rankings = list(board.get("rankings", []) or [])
    meta_map = {
        _game_key(meta.get("game_id") or meta.get("id")): meta
        for meta in (board.get("games_meta", []) or [])
    }
    grouped: dict[str, list[dict]] = {}
    for player in rankings:
        key = _game_key(player.get("game_id") or player.get("schedule_game_key") or player.get("weather_game_key"))
        if key:
            grouped.setdefault(key, []).append(player)

    games: list[dict] = []
    for key, players in grouped.items():
        meta = dict(meta_map.get(key, {}))
        players.sort(key=lambda item: safe_float(item.get("dinger_score")), reverse=True)

        teams: list[str] = []
        for player in players:
            team = str(player.get("team_name") or "")
            if team and team not in teams:
                teams.append(team)

        away = str(meta.get("away_team_name") or (teams[0] if teams else "AWAY"))
        home = str(meta.get("home_team_name") or (teams[1] if len(teams) > 1 else "HOME"))
        away_players = [p for p in players if str(p.get("team_name")) == away]
        home_players = [p for p in players if str(p.get("team_name")) == home]

        if not away_players or not home_players:
            split = max(1, len(players) // 2)
            away_players = players[:split]
            home_players = players[split:]
            if away_players:
                away = str(away_players[0].get("team_name") or away)
            if home_players:
                home = str(home_players[0].get("team_name") or home)

        top_six = players[:6]
        game_score = mean(safe_float(p.get("dinger_score")) for p in top_six) if top_six else 0.0
        games.append({
            "key": key,
            "meta": meta,
            "players": players,
            "away": away,
            "home": home,
            "away_players": away_players,
            "home_players": home_players,
            "game_score": game_score,
            "top_player": players[0] if players else {},
        })

    games.sort(key=lambda game: game["game_score"], reverse=True)
    return games


def _pitcher_for_batters(players: list[dict], meta: dict, pitcher_side: str) -> dict:
    sample = players[0] if players else {}
    prefix = f"{pitcher_side}_"
    name = meta.get(prefix + "probable_pitcher") or sample.get("opposing_pitcher") or "Awaiting announcement"
    hand = meta.get(prefix + "probable_pitcher_hand") or sample.get("opposing_pitcher_hand") or "—"
    return {
        "name": str(name),
        "hand": str(hand),
        "era": safe_float(meta.get(prefix + "pitcher_era") or sample.get("pitcher_era")),
        "whip": safe_float(meta.get(prefix + "pitcher_whip") or sample.get("pitcher_whip")),
        "hr9": safe_float(meta.get(prefix + "pitcher_hr9") or sample.get("pitcher_hr9")),
        "k9": safe_float(meta.get(prefix + "pitcher_strikeouts_per9") or sample.get("pitcher_strikeouts_per9")),
        "hard_hit": safe_float(sample.get("pitcher_hard_hit_pct")),
        "status": str(sample.get("probable_pitcher_status") or "Projected starter"),
    }


def _platoon(player: dict) -> tuple[str, str]:
    bat = str(player.get("bat_side") or player.get("bats") or "—").upper()
    hand = str(player.get("opposing_pitcher_hand") or "—").upper()
    if bat == "S":
        return "SWITCH EDGE", "#35f28f"
    if (bat == "L" and hand == "R") or (bat == "R" and hand == "L"):
        return "PLATOON EDGE", "#35f28f"
    if bat in {"L", "R"} and hand == bat:
        return "SAME-SIDE", "#ffba35"
    return "NEUTRAL", "#43cfff"


def _matchup_score(player: dict) -> float:
    direct = safe_float(player.get("pitcher_matchup_score"))
    if direct:
        return max(0.0, min(100.0, direct))
    score = (
        safe_float(player.get("dinger_score")) * 0.48
        + min(100.0, safe_float(player.get("pitcher_hr9")) * 38.0) * 0.24
        + min(100.0, safe_float(player.get("barrel_pct")) * 4.5) * 0.16
        + min(100.0, safe_float(player.get("hard_hit_pct")) * 1.65) * 0.12
    )
    return max(0.0, min(100.0, score))


def _time(meta: dict) -> str:
    for field in ("game_time_local", "game_time", "start_time", "gameTime"):
        value = str(meta.get(field) or "")
        if value:
            return value[-8:-3] if "T" in value else value[:12]
    return "Game time TBD"


def _ids(game: dict) -> tuple[object, object]:
    meta = game["meta"]
    away_id = meta.get("away_team_id") or next((p.get("team_id") for p in game["away_players"]), None)
    home_id = meta.get("home_team_id") or next((p.get("team_id") for p in game["home_players"]), None)
    return away_id, home_id


def _thumbnail(game: dict) -> str:
    meta = game["meta"]
    away, home = game["away"], game["home"]
    away_id, home_id = _ids(game)
    scene = stadium_scene_data(meta)
    top = game["top_player"]
    weather = safe_float(meta.get("weather_impact") or top.get("weather_impact"))
    grade = str(meta.get("weather_grade") or top.get("weather_grade") or "—")
    away_pitcher = _pitcher_for_batters(game["home_players"], meta, "away")
    home_pitcher = _pitcher_for_batters(game["away_players"], meta, "home")
    parts = [
        f'<a class="dd26-match-card-link" href="?view=matchups&game={quote(game["key"])}" target="_self">',
        f'<article class="dd26-match-card" style="background-image:linear-gradient(90deg,rgba(1,7,15,.72),rgba(1,7,15,.18) 55%,rgba(1,7,15,.66)),url(\'{scene}\')">',
        '<header><div>',
        f'<span class="logo-plate"><img src="{team_logo(away_id)}"></span><b>{esc(away)}</b><i>@</i><b>{esc(home)}</b><span class="logo-plate"><img src="{team_logo(home_id)}"></span>',
        f'</div><time>{esc(_time(meta))}</time></header>',
        '<div class="dd26-match-card-main">',
        f'<div class="dd26-match-score"><small>MATCHUP POWER</small><strong>{game["game_score"]:.1f}</strong><span>Top-six Dinger Score</span></div>',
        '<div class="dd26-match-starters">',
        f'<div><small>{esc(away)} STARTER</small><b>{esc(away_pitcher["name"])}</b><span>{esc(away_pitcher["hand"])}HP • {away_pitcher["hr9"]:.2f} HR/9 • {away_pitcher["era"]:.2f} ERA</span></div>',
        f'<div><small>{esc(home)} STARTER</small><b>{esc(home_pitcher["name"])}</b><span>{esc(home_pitcher["hand"])}HP • {home_pitcher["hr9"]:.2f} HR/9 • {home_pitcher["era"]:.2f} ERA</span></div>',
        '</div></div><footer>',
        f'<div><span>TOP BAT</span><b>{esc(str(top.get("player_name") or "—"))}</b></div>',
        f'<div><span>HR PROB</span><b>{probability_fraction(top.get("probability"))*100:.1f}%</b></div>',
        f'<div><span>WEATHER</span><b>{grade} • {weather:+.1f}</b></div>',
        '<em>OPEN MATCHUP ›</em></footer></article></a>',
    ]
    return "".join(parts)


def _pitcher_card(team: str, team_id: object, pitcher: dict, accent: str) -> str:
    return (
        f'<article class="dd26-pitcher-card" style="--accent:{accent}">'
        f'<header><span class="logo-plate large"><img src="{team_logo(team_id)}"></span><div><small>{esc(team)} PROJECTED STARTER</small><h2>{esc(pitcher["name"])}</h2><p>{esc(pitcher["status"])}</p></div></header>'
        '<div class="dd26-pitcher-stats">'
        f'<div><span>HAND</span><b>{esc(pitcher["hand"])}HP</b></div>'
        f'<div><span>ERA</span><b>{pitcher["era"]:.2f}</b></div>'
        f'<div><span>WHIP</span><b>{pitcher["whip"]:.2f}</b></div>'
        f'<div><span>HR/9</span><b>{pitcher["hr9"]:.2f}</b></div>'
        f'<div><span>K/9</span><b>{pitcher["k9"]:.1f}</b></div>'
        f'<div><span>HARD-HIT</span><b>{pitcher["hard_hit"]:.1f}%</b></div>'
        '</div></article>'
    )


def _batter_row(player: dict, rank: int) -> str:
    probability = probability_fraction(player.get("probability")) * 100
    score = safe_float(player.get("dinger_score"))
    matchup = _matchup_score(player)
    platoon, platoon_color = _platoon(player)
    best_price = player.get("best_odds") if player.get("best_odds") is not None else player.get("fair_odds")
    return (
        f'<a class="dd26-batter-row" href="?view=player-intelligence&player={safe_int(player.get("player_id"))}" target="_self">'
        f'<span class="rank">{rank}</span>'
        f'<span class="player"><img src="{headshot(player.get("player_id"), 180)}"><span><b>{esc(str(player.get("player_name") or "—"))}</b><small>{esc(str(player.get("position") or "—"))} • Bats {esc(str(player.get("bat_side") or "—"))}</small></span></span>'
        f'<span class="metric score"><small>DINGER</small><b>{score:.1f}</b><i><em style="width:{score:.1f}%"></em></i></span>'
        f'<span class="metric prob"><small>HR PROB</small><b>{probability:.1f}%</b><i><em style="width:{min(100, probability*3):.1f}%"></em></i></span>'
        f'<span class="metric"><small>BARREL</small><b>{safe_float(player.get("barrel_pct")):.1f}%</b></span>'
        f'<span class="metric"><small>HARD-HIT</small><b>{safe_float(player.get("hard_hit_pct")):.1f}%</b></span>'
        f'<span class="metric"><small>PITCHER HR/9</small><b>{safe_float(player.get("pitcher_hr9")):.2f}</b></span>'
        f'<span class="metric matchup"><small>MATCHUP</small><b>{matchup:.0f}</b><i><em style="width:{matchup:.1f}%"></em></i></span>'
        f'<span class="platoon" style="--platoon:{platoon_color}">{platoon}</span>'
        f'<span class="price"><small>BEST PRICE</small><b>{odds(best_price)}</b><em>{esc(str(player.get("best_book") or "Fair"))}</em></span></a>'
    )


def _team_batter_board(title: str, team_id: object, pitcher: dict, players: list[dict], accent: str) -> str:
    rows = "".join(_batter_row(player, rank) for rank, player in enumerate(players[:9], 1))
    return (
        f'<section class="dd26-batter-board" style="--accent:{accent}">'
        f'<header><div><span class="logo-plate"><img src="{team_logo(team_id)}"></span><span><small>{esc(title)}</small><b>BATTERS VS {esc(pitcher["name"])}</b></span></div><em>{esc(pitcher["hand"])}HP • {pitcher["hr9"]:.2f} HR/9</em></header>'
        '<div class="dd26-batter-head"><span>#</span><span>PLAYER</span><span>DINGER</span><span>HR PROB</span><span>BARREL</span><span>HARD-HIT</span><span>P HR/9</span><span>MATCHUP</span><span>PLATOON</span><span>PRICE</span></div>'
        f'<div>{rows or "<div class=dd26-empty>No projected hitters are connected.</div>"}</div></section>'
    )


def _detail(board: dict, game: dict) -> None:
    meta = game["meta"]
    away, home = game["away"], game["home"]
    away_id, home_id = _ids(game)
    away_pitcher = _pitcher_for_batters(game["home_players"], meta, "away")
    home_pitcher = _pitcher_for_batters(game["away_players"], meta, "home")
    scene = stadium_scene_data(meta)
    venue = str(meta.get("stadium_name") or meta.get("venue_name") or "MLB Ballpark")
    weather = safe_float(meta.get("weather_impact") or game["top_player"].get("weather_impact"))
    grade = str(meta.get("weather_grade") or game["top_player"].get("weather_grade") or "—")

    st.markdown('<a class="dd26-back" href="?view=matchups" target="_self">← ALL MATCHUPS</a>', unsafe_allow_html=True)
    st.markdown(
        f'<section class="dd26-match-detail-hero" style="background-image:linear-gradient(90deg,rgba(2,8,18,.86),rgba(2,8,18,.30) 52%,rgba(2,8,18,.82)),url(\'{scene}\')">'
        '<div class="dd26-versus">'
        f'<div><span class="logo-plate hero"><img src="{team_logo(away_id)}"></span><small>AWAY</small><h1>{esc(away)}</h1></div><i>VS</i>'
        f'<div><span class="logo-plate hero"><img src="{team_logo(home_id)}"></span><small>HOME</small><h1>{esc(home)}</h1></div></div>'
        '<aside>'
        f'<div><span>VENUE</span><b>{esc(venue)}</b></div><div><span>GAME TIME</span><b>{esc(_time(meta))}</b></div>'
        f'<div><span>WEATHER</span><b>{grade} • {weather:+.1f}</b></div><div><span>MATCHUP POWER</span><b>{game["game_score"]:.1f}</b></div>'
        '</aside></section>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="dd26-pitcher-grid">'
        + _pitcher_card(away, away_id, away_pitcher, "#31c7ff")
        + _pitcher_card(home, home_id, home_pitcher, "#ff4dd2")
        + '</div>',
        unsafe_allow_html=True,
    )

    avg_barrel = mean([safe_float(p.get("barrel_pct")) for p in game["players"]]) if game["players"] else 0
    avg_hard_hit = mean([safe_float(p.get("hard_hit_pct")) for p in game["players"]]) if game["players"] else 0
    st.markdown(
        '<section class="dd26-key-strip">'
        f'<div><span>TOP BAT</span><b>{esc(str(game["top_player"].get("player_name") or "—"))}</b></div>'
        f'<div><span>TOP HR PROBABILITY</span><b>{probability_fraction(game["top_player"].get("probability"))*100:.1f}%</b></div>'
        f'<div><span>AVERAGE BARREL</span><b>{avg_barrel:.1f}%</b></div>'
        f'<div><span>AVERAGE HARD-HIT</span><b>{avg_hard_hit:.1f}%</b></div>'
        f'<div><span>PROJECTED HITTERS</span><b>{len(game["players"])}</b></div></section>',
        unsafe_allow_html=True,
    )

    st.markdown(
        _team_batter_board(f"{away} OFFENSE", away_id, home_pitcher, game["away_players"], "#31c7ff")
        + _team_batter_board(f"{home} OFFENSE", home_id, away_pitcher, game["home_players"], "#ff4dd2"),
        unsafe_allow_html=True,
    )


def render(board: dict) -> None:
    games = _groups(board)
    requested = str(st.query_params.get("game") or "")
    selected = next((game for game in games if game["key"] == requested), None)
    if selected is not None:
        _detail(board, selected)
        return

    starter_count = sum(
        1 for game in games
        if _pitcher_for_batters(game["away_players"], game["meta"], "home")["name"]
        not in {"Awaiting announcement", "Not announced"}
    )
    st.markdown(
        f'<section class="dd26-match-hero"><div><span>STARTER • CONTACT • POWER • PRICE</span><h1>PITCHER VS <em>BATTER</em></h1><p>Every game ranked by projected power, starting-pitcher vulnerability, Statcast contact quality, platoon edge, weather, and sportsbook price.</p></div><aside><div><span>GAMES</span><b>{len(games)}</b></div><div><span>HITTERS</span><b>{len(board.get("rankings", []) or [])}</b></div><div><span>LIVE STARTERS</span><b>{starter_count}</b></div></aside></section>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="dd26-match-grid">' + "".join(_thumbnail(game) for game in games) + '</div>', unsafe_allow_html=True)
