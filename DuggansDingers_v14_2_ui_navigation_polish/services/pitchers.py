from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

BASE_DIR = Path(__file__).resolve().parents[1]
CACHE_FILE = BASE_DIR / "data" / "cache" / "probable_pitchers.json"
MLB_BASE_URL = "https://statsapi.mlb.com/api/v1"

ALIASES = {
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
    "ST LOUIS CARDINALS": "STL", "CARDINALS": "STL",
    "TAMPA BAY RAYS": "TB", "RAYS": "TB", "TBR": "TB",
    "TEXAS RANGERS": "TEX", "RANGERS": "TEX",
    "TORONTO BLUE JAYS": "TOR", "BLUE JAYS": "TOR",
    "WASHINGTON NATIONALS": "WSH", "NATIONALS": "WSH", "WSN": "WSH",
}


def _num(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _norm(value: Any) -> str:
    raw = " ".join(str(value or "").replace(".", " ").upper().split())
    if raw in ALIASES:
        return ALIASES[raw]
    compact = "".join(ch for ch in raw if ch.isalnum())
    return ALIASES.get(compact, raw)


def _load_cache() -> dict[str, Any]:
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_cache(payload: dict[str, Any]) -> None:
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass


def _team_abbr(team: dict[str, Any]) -> str:
    return _norm(team.get("abbreviation") or team.get("teamName") or team.get("name"))


def _schedule(target_date: str) -> list[dict[str, Any]]:
    response = requests.get(
        f"{MLB_BASE_URL}/schedule",
        params={"sportId": 1, "date": target_date, "hydrate": "probablePitcher,team,venue"},
        timeout=25,
    )
    response.raise_for_status()
    output: list[dict[str, Any]] = []
    for day in response.json().get("dates", []):
        for game in day.get("games", []):
            teams = game.get("teams") or {}
            home = teams.get("home") or {}
            away = teams.get("away") or {}
            home_team = home.get("team") or {}
            away_team = away.get("team") or {}
            output.append({
                "mlb_game_pk": game.get("gamePk"),
                "game_time": game.get("gameDate"),
                "venue_name": (game.get("venue") or {}).get("name"),
                "home": _team_abbr(home_team),
                "away": _team_abbr(away_team),
                "home_team_id": home_team.get("id"),
                "away_team_id": away_team.get("id"),
                "home_pitcher": home.get("probablePitcher") or {},
                "away_pitcher": away.get("probablePitcher") or {},
            })
    return output


def _find_schedule_game(meta: dict[str, Any], schedule: list[dict[str, Any]]) -> dict[str, Any] | None:
    home = _norm(meta.get("home_team_name"))
    away = _norm(meta.get("away_team_name"))
    for game in schedule:
        if game["home"] == home and game["away"] == away:
            return game
    for game in schedule:
        if {game["home"], game["away"]} == {home, away}:
            return game
    return None


def _pitcher_payload(pitcher_id: int, season: int) -> dict[str, Any]:
    detail_response = requests.get(f"{MLB_BASE_URL}/people/{pitcher_id}", timeout=20)
    detail_response.raise_for_status()
    person = (detail_response.json().get("people") or [{}])[0]

    stats_response = requests.get(
        f"{MLB_BASE_URL}/people/{pitcher_id}/stats",
        params={"stats": "season", "group": "pitching", "season": season},
        timeout=25,
    )
    stats_response.raise_for_status()
    splits: list[dict[str, Any]] = []
    for group in stats_response.json().get("stats", []):
        splits.extend(group.get("splits") or [])
    stat = (splits[0].get("stat") if splits else {}) or {}
    return {
        "id": pitcher_id,
        "name": person.get("fullName") or f"Pitcher {pitcher_id}",
        "hand": (person.get("pitchHand") or {}).get("code") or "—",
        "era": _num(stat.get("era")),
        "whip": _num(stat.get("whip")),
        "hr9": _num(stat.get("homeRunsPer9")),
        "home_runs_allowed": int(_num(stat.get("homeRuns"))),
        "innings": _num(stat.get("inningsPitched")),
        "strikeouts": int(_num(stat.get("strikeOuts"))),
        "strikeouts_per9": _num(stat.get("strikeoutsPer9Inn")),
    }


def enrich_probable_pitchers(
    players: list[dict[str, Any]],
    games_meta: list[dict[str, Any]],
    target_date: str,
    season: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    try:
        schedule = _schedule(target_date)
    except requests.RequestException as exc:
        for player in players:
            player.setdefault("opposing_pitcher", "Not announced")
            player.setdefault("probable_pitcher_status", "schedule unavailable")
        return players, games_meta, f"unavailable: {exc}"

    schedule_by_board_game: dict[str, dict[str, Any]] = {}
    pitcher_ids: set[int] = set()
    for meta in games_meta:
        match = _find_schedule_game(meta, schedule)
        if not match:
            continue
        key = str(meta.get("game_id") or "")
        schedule_by_board_game[key] = match
        meta["mlb_game_pk"] = match.get("mlb_game_pk")
        meta["game_time"] = meta.get("game_time") or match.get("game_time")
        for side in ("home", "away"):
            pitcher = match.get(f"{side}_pitcher") or {}
            pitcher_id = int(pitcher.get("id") or 0)
            meta[f"{side}_probable_pitcher_id"] = pitcher_id or None
            meta[f"{side}_probable_pitcher"] = pitcher.get("fullName") or "Not announced"
            if pitcher_id:
                pitcher_ids.add(pitcher_id)

    cache = _load_cache()
    cache_key = f"{target_date}_{season}"
    day_cache = cache.get(cache_key) if isinstance(cache.get(cache_key), dict) else {}
    pitcher_data: dict[int, dict[str, Any]] = {}
    missing: list[int] = []
    for pitcher_id in pitcher_ids:
        cached = day_cache.get(str(pitcher_id))
        if isinstance(cached, dict) and cached.get("name"):
            pitcher_data[pitcher_id] = cached
        else:
            missing.append(pitcher_id)

    with ThreadPoolExecutor(max_workers=min(6, max(1, len(missing)))) as executor:
        futures = {executor.submit(_pitcher_payload, pitcher_id, season): pitcher_id for pitcher_id in missing}
        for future in as_completed(futures):
            pitcher_id = futures[future]
            try:
                pitcher_data[pitcher_id] = future.result()
            except requests.RequestException:
                pitcher_data[pitcher_id] = {"id": pitcher_id}

    day_cache.update({str(pid): data for pid, data in pitcher_data.items() if data})
    cache[cache_key] = day_cache
    cache["updated_at"] = datetime.now(timezone.utc).isoformat()
    if len(cache) > 40:
        keep = {k: v for k, v in list(cache.items())[-30:]}
        cache = keep
    _save_cache(cache)

    announced = 0
    for meta in games_meta:
        for side in ("home", "away"):
            pitcher_id = int(meta.get(f"{side}_probable_pitcher_id") or 0)
            info = pitcher_data.get(pitcher_id, {})
            if info.get("name"):
                announced += 1
                meta[f"{side}_probable_pitcher"] = info.get("name")
                meta[f"{side}_probable_pitcher_hand"] = info.get("hand")
                meta[f"{side}_pitcher_era"] = info.get("era")
                meta[f"{side}_pitcher_hr9"] = info.get("hr9")

    for player in players:
        game = schedule_by_board_game.get(str(player.get("game_id") or ""))
        if not game:
            player["opposing_pitcher"] = "Not announced"
            player["opposing_pitcher_hand"] = "—"
            player["probable_pitcher_status"] = "game not matched"
            player["pitching_data_available"] = False
            continue
        team = _norm(player.get("team_name"))
        opponent_side = "away" if team == game.get("home") else "home" if team == game.get("away") else ""
        pitcher = game.get(f"{opponent_side}_pitcher") if opponent_side else {}
        pitcher = pitcher or {}
        pitcher_id = int(pitcher.get("id") or 0)
        info = pitcher_data.get(pitcher_id, {})
        player["opposing_pitcher_id"] = pitcher_id or None
        player["opposing_pitcher"] = info.get("name") or pitcher.get("fullName") or "Not announced"
        player["opposing_pitcher_hand"] = info.get("hand") or "—"
        player["probable_pitcher_status"] = "announced" if pitcher_id else "not announced"
        player["pitcher_era"] = info.get("era")
        player["pitcher_whip"] = info.get("whip")
        player["pitcher_hr9"] = info.get("hr9")
        player["pitcher_home_runs_allowed"] = info.get("home_runs_allowed")
        player["pitcher_innings"] = info.get("innings")
        player["pitcher_strikeouts"] = info.get("strikeouts")
        player["pitcher_strikeouts_per9"] = info.get("strikeouts_per9")
        player["pitching_data_available"] = bool(info.get("name"))
        # The model uses this only when real pitcher data is available.
        player["pitcher_vulnerability_signal"] = round(
            _num(info.get("hr9")) * 32.0 + max(0.0, _num(info.get("era")) - 3.5) * 5.0,
            2,
        ) if info.get("name") else 0.0

    status = "live" if announced else "awaiting announcements"
    return players, games_meta, status
