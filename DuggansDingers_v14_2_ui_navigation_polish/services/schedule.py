from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

BASE_DIR = Path(__file__).resolve().parents[1]
CACHE_FILE = BASE_DIR / "data" / "cache" / "mlb_schedule.json"
MLB_BASE_URL = "https://statsapi.mlb.com/api/v1"
CACHE_TTL_MINUTES = 30
STALE_TTL_HOURS = 12

TEAM_ALIASES = {
    "ARIZONA DIAMONDBACKS": "ARI", "DIAMONDBACKS": "ARI",
    "ATLANTA BRAVES": "ATL", "BRAVES": "ATL",
    "BALTIMORE ORIOLES": "BAL", "ORIOLES": "BAL",
    "BOSTON RED SOX": "BOS", "RED SOX": "BOS",
    "CHICAGO CUBS": "CHC", "CUBS": "CHC",
    "CHICAGO WHITE SOX": "CWS", "WHITE SOX": "CWS",
    "CINCINNATI REDS": "CIN", "REDS": "CIN",
    "CLEVELAND GUARDIANS": "CLE", "GUARDIANS": "CLE",
    "COLORADO ROCKIES": "COL", "ROCKIES": "COL",
    "DETROIT TIGERS": "DET", "TIGERS": "DET",
    "HOUSTON ASTROS": "HOU", "ASTROS": "HOU",
    "KANSAS CITY ROYALS": "KC", "ROYALS": "KC", "KCR": "KC",
    "LOS ANGELES ANGELS": "LAA", "ANGELS": "LAA",
    "LOS ANGELES DODGERS": "LAD", "DODGERS": "LAD",
    "MIAMI MARLINS": "MIA", "MARLINS": "MIA",
    "MILWAUKEE BREWERS": "MIL", "BREWERS": "MIL",
    "MINNESOTA TWINS": "MIN", "TWINS": "MIN",
    "NEW YORK METS": "NYM", "METS": "NYM",
    "NEW YORK YANKEES": "NYY", "YANKEES": "NYY",
    "ATHLETICS": "ATH", "OAKLAND ATHLETICS": "ATH", "SACRAMENTO ATHLETICS": "ATH", "OAK": "ATH",
    "PHILADELPHIA PHILLIES": "PHI", "PHILLIES": "PHI",
    "PITTSBURGH PIRATES": "PIT", "PIRATES": "PIT",
    "SAN DIEGO PADRES": "SD", "PADRES": "SD", "SDP": "SD",
    "SAN FRANCISCO GIANTS": "SF", "GIANTS": "SF", "SFG": "SF",
    "SEATTLE MARINERS": "SEA", "MARINERS": "SEA",
    "ST LOUIS CARDINALS": "STL", "ST. LOUIS CARDINALS": "STL", "CARDINALS": "STL",
    "TAMPA BAY RAYS": "TB", "RAYS": "TB", "TBR": "TB",
    "TEXAS RANGERS": "TEX", "RANGERS": "TEX",
    "TORONTO BLUE JAYS": "TOR", "BLUE JAYS": "TOR",
    "WASHINGTON NATIONALS": "WSH", "NATIONALS": "WSH", "WSN": "WSH",
}


def normalize_team(value: Any) -> str:
    raw = " ".join(str(value or "").replace(".", " ").upper().split())
    return TEAM_ALIASES.get(raw, raw)


def _load_cache() -> dict[str, Any]:
    try:
        payload = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_cache(payload: dict[str, Any]) -> None:
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass


def _parsed_time(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _standardize_game(game: dict[str, Any]) -> dict[str, Any]:
    teams = game.get("teams") or {}
    home = teams.get("home") or {}
    away = teams.get("away") or {}
    home_team = home.get("team") or {}
    away_team = away.get("team") or {}
    venue = game.get("venue") or {}
    home_pitcher = home.get("probablePitcher") or {}
    away_pitcher = away.get("probablePitcher") or {}
    game_pk = game.get("gamePk")
    return {
        "schedule_game_key": str(game_pk or ""),
        "mlb_game_pk": game_pk,
        "game_time": game.get("gameDate"),
        "venue_id": venue.get("id"),
        "venue_name": venue.get("name"),
        "home_team_id": home_team.get("id"),
        "away_team_id": away_team.get("id"),
        "home_team_name": normalize_team(home_team.get("abbreviation") or home_team.get("teamName") or home_team.get("name")),
        "away_team_name": normalize_team(away_team.get("abbreviation") or away_team.get("teamName") or away_team.get("name")),
        "home_probable_pitcher_id": home_pitcher.get("id"),
        "home_probable_pitcher": home_pitcher.get("fullName") or "Not announced",
        "away_probable_pitcher_id": away_pitcher.get("id"),
        "away_probable_pitcher": away_pitcher.get("fullName") or "Not announced",
        "status": ((game.get("status") or {}).get("detailedState") or ""),
    }


def fetch_schedule(target_date: str, *, force: bool = False) -> list[dict[str, Any]]:
    cache = _load_cache()
    entry = cache.get(target_date) if isinstance(cache.get(target_date), dict) else None
    now = datetime.now(timezone.utc)
    stale_games: list[dict[str, Any]] = []
    if entry:
        updated = _parsed_time(entry.get("updated_at"))
        games = entry.get("games") if isinstance(entry.get("games"), list) else []
        if updated and games:
            age = now - updated.astimezone(timezone.utc)
            if age <= timedelta(minutes=CACHE_TTL_MINUTES) and not force:
                return games
            if age <= timedelta(hours=STALE_TTL_HOURS):
                stale_games = games

    try:
        response = requests.get(
            f"{MLB_BASE_URL}/schedule",
            params={
                "sportId": 1,
                "date": target_date,
                "hydrate": "probablePitcher,team,venue",
            },
            timeout=25,
        )
        response.raise_for_status()
        games: list[dict[str, Any]] = []
        for day in response.json().get("dates", []):
            for game in day.get("games", []):
                games.append(_standardize_game(game))
        cache[target_date] = {"updated_at": now.isoformat(), "games": games}
        cache["last_updated"] = now.isoformat()
        if len(cache) > 40:
            date_keys = sorted([key for key in cache if key[:4].isdigit()])[-25:]
            cache = {key: cache[key] for key in date_keys} | {"last_updated": now.isoformat()}
        _save_cache(cache)
        return games
    except requests.RequestException:
        if stale_games:
            return stale_games
        raise


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _pair_from_meta(meta: dict[str, Any]) -> frozenset[str]:
    return frozenset(filter(None, [normalize_team(meta.get("home_team_name")), normalize_team(meta.get("away_team_name"))]))


def match_meta_to_schedule(meta: dict[str, Any], schedule: list[dict[str, Any]]) -> dict[str, Any] | None:
    home_id = _safe_int(meta.get("home_team_id"))
    away_id = _safe_int(meta.get("away_team_id"))
    if home_id and away_id:
        for game in schedule:
            if _safe_int(game.get("home_team_id")) == home_id and _safe_int(game.get("away_team_id")) == away_id:
                return game
        for game in schedule:
            if {_safe_int(game.get("home_team_id")), _safe_int(game.get("away_team_id"))} == {home_id, away_id}:
                return game

    pair = _pair_from_meta(meta)
    if len(pair) == 2:
        for game in schedule:
            if _pair_from_meta(game) == pair:
                return game

    venue = " ".join(str(meta.get("venue_name") or "").lower().split())
    if venue:
        for game in schedule:
            candidate = " ".join(str(game.get("venue_name") or "").lower().split())
            if venue == candidate or venue in candidate or candidate in venue:
                return game
    return None


def match_player_to_schedule(player: dict[str, Any], schedule: list[dict[str, Any]]) -> dict[str, Any] | None:
    team_id = _safe_int(player.get("team_id"))
    opponent_id = _safe_int(player.get("opponent_team_id"))
    if team_id and opponent_id:
        for game in schedule:
            if {_safe_int(game.get("home_team_id")), _safe_int(game.get("away_team_id"))} == {team_id, opponent_id}:
                return game

    team = normalize_team(player.get("team_name"))
    opponent = normalize_team(player.get("opponent"))
    if team and opponent:
        pair = frozenset([team, opponent])
        for game in schedule:
            if _pair_from_meta(game) == pair:
                return game
    if team:
        matches = [game for game in schedule if team in _pair_from_meta(game)]
        if len(matches) == 1:
            return matches[0]
    return None


def repair_board_games(board: dict[str, Any], schedule: list[dict[str, Any]]) -> dict[str, Any]:
    rankings = board.get("rankings", []) or []
    existing = [dict(meta) for meta in (board.get("games_meta", []) or [])]
    repaired: list[dict[str, Any]] = []
    used_schedule: set[str] = set()

    players_by_game: dict[str, list[dict[str, Any]]] = {}
    for player in rankings:
        players_by_game.setdefault(str(player.get("game_id") or ""), []).append(player)

    for meta in existing:
        match = match_meta_to_schedule(meta, schedule)
        if not match:
            player_sample = players_by_game.get(str(meta.get("game_id") or ""), [])
            match = next((match_player_to_schedule(player, schedule) for player in player_sample if match_player_to_schedule(player, schedule)), None)
        if match:
            merged = {**meta, **{key: value for key, value in match.items() if value not in (None, "")}}
            merged["game_id"] = meta.get("game_id") or match.get("schedule_game_key")
            repaired.append(merged)
            used_schedule.add(str(match.get("schedule_game_key") or ""))
        else:
            repaired.append(meta)

    for game in schedule:
        key = str(game.get("schedule_game_key") or "")
        if key in used_schedule:
            continue
        matched_players = [player for player in rankings if match_player_to_schedule(player, [game])]
        board_game_id = next((str(player.get("game_id")) for player in matched_players if player.get("game_id")), key)
        repaired.append({**game, "game_id": board_game_id})

    # Synchronize every player with the authoritative MLB schedule game.
    for player in rankings:
        match = match_player_to_schedule(player, schedule)
        if not match:
            continue
        player["schedule_game_key"] = match.get("schedule_game_key")
        player["mlb_game_pk"] = match.get("mlb_game_pk")
        player["game_time"] = match.get("game_time") or player.get("game_time")
        player["venue_name"] = match.get("venue_name") or player.get("venue_name")
        player["home_team_name"] = match.get("home_team_name")
        player["away_team_name"] = match.get("away_team_name")
        player["home_team_id"] = match.get("home_team_id")
        player["away_team_id"] = match.get("away_team_id")

    board["games_meta"] = repaired
    board["games"] = max(int(board.get("games") or 0), len(schedule))
    return board
