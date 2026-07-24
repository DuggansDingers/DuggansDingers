from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

from services.schedule import fetch_schedule, match_meta_to_schedule, match_player_to_schedule, repair_board_games

BASE_DIR = Path(__file__).resolve().parents[1]
CACHE_FILE = BASE_DIR / "data" / "cache" / "probable_pitchers.json"
MLB_BASE_URL = "https://statsapi.mlb.com/api/v1"
BALLPARK_BASE_URL = "https://www.ballparkpal.com/api/v1"
BALLPARK_API_KEY = (os.getenv("BALLPARKPAL_API_KEY") or "").strip()

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
    return fetch_schedule(target_date)


def _find_schedule_game(meta: dict[str, Any], schedule: list[dict[str, Any]]) -> dict[str, Any] | None:
    return match_meta_to_schedule(meta, schedule)


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



def _first(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def _walk_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def _ballpark_matchups(target_date: str) -> dict[int, dict[str, Any]]:
    """One-call fallback for projected starters from Ballpark Pal matchups.

    Ballpark Pal exposes batter-vs-pitcher matchup data for a full date. Field
    names can evolve, so this parser accepts common nested and flat variants.
    The result is keyed by batter/player id and is used only when MLB's
    probablePitcher field has not been published yet.
    """
    if not BALLPARK_API_KEY:
        return {}
    response = requests.get(
        f"{BALLPARK_BASE_URL}/matchups",
        params={"date": target_date},
        headers={"X-API-Key": BALLPARK_API_KEY},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    output: dict[int, dict[str, Any]] = {}
    for item in _walk_dicts(payload):
        batter = _first(item.get("batter"), item.get("hitter"), item.get("player"), item.get("subject"))
        pitcher = _first(item.get("pitcher"), item.get("opposingPitcher"), item.get("starter"))

        batter_id = _first(
            item.get("batterId"), item.get("hitterId"), item.get("playerId"),
            batter.get("id") if isinstance(batter, dict) else None,
        )
        pitcher_id = _first(
            item.get("pitcherId"), item.get("opposingPitcherId"), item.get("starterId"),
            pitcher.get("id") if isinstance(pitcher, dict) else None,
        )
        pitcher_name = _first(
            item.get("pitcherName"), item.get("opposingPitcherName"), item.get("starterName"),
            pitcher.get("fullName") if isinstance(pitcher, dict) else None,
            pitcher.get("name") if isinstance(pitcher, dict) else None,
        )
        hand = _first(
            item.get("pitcherHand"), item.get("throws"),
            pitcher.get("hand") if isinstance(pitcher, dict) else None,
            pitcher.get("pitchHand") if isinstance(pitcher, dict) else None,
        )
        if isinstance(hand, dict):
            hand = _first(hand.get("code"), hand.get("description"))
        try:
            batter_key = int(batter_id or 0)
        except (TypeError, ValueError):
            batter_key = 0
        try:
            pitcher_key = int(pitcher_id or 0)
        except (TypeError, ValueError):
            pitcher_key = 0
        if batter_key and (pitcher_key or pitcher_name):
            output[batter_key] = {
                "id": pitcher_key or None,
                "name": str(pitcher_name or "Projected starter"),
                "hand": str(hand or "—")[:1].upper(),
                "source": "Ballpark Pal matchup",
            }
    return output

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

    try:
        matchup_fallback = _ballpark_matchups(target_date)
    except requests.RequestException:
        matchup_fallback = {}

    repaired_board = repair_board_games({"games_meta": games_meta, "rankings": players, "games": len(games_meta)}, schedule)
    games_meta = repaired_board.get("games_meta", games_meta)

    schedule_by_board_game: dict[str, dict[str, Any]] = {}
    pitcher_ids: set[int] = set()
    for meta in games_meta:
        match = _find_schedule_game(meta, schedule)
        if not match:
            continue
        key = str(meta.get("game_id") or match.get("schedule_game_key") or "")
        schedule_by_board_game[key] = match
        if match.get("schedule_game_key"):
            schedule_by_board_game[str(match.get("schedule_game_key"))] = match
        meta["mlb_game_pk"] = match.get("mlb_game_pk")
        meta["game_time"] = match.get("game_time") or meta.get("game_time")
        meta["venue_name"] = match.get("venue_name") or meta.get("venue_name")
        meta["home_team_name"] = match.get("home_team_name") or meta.get("home_team_name")
        meta["away_team_name"] = match.get("away_team_name") or meta.get("away_team_name")
        meta["home_team_id"] = match.get("home_team_id") or meta.get("home_team_id")
        meta["away_team_id"] = match.get("away_team_id") or meta.get("away_team_id")
        for side in ("home", "away"):
            pitcher_id = int(match.get(f"{side}_probable_pitcher_id") or 0)
            pitcher_name = match.get(f"{side}_probable_pitcher") or "Awaiting announcement"
            meta[f"{side}_probable_pitcher_id"] = pitcher_id or None
            meta[f"{side}_probable_pitcher"] = pitcher_name
            if pitcher_id:
                pitcher_ids.add(pitcher_id)

    for fallback in matchup_fallback.values():
        try:
            fallback_id = int(fallback.get("id") or 0)
        except (TypeError, ValueError):
            fallback_id = 0
        if fallback_id:
            pitcher_ids.add(fallback_id)

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

    with ThreadPoolExecutor(max_workers=min(12, max(1, len(missing)))) as executor:
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
        game = (
            schedule_by_board_game.get(str(player.get("game_id") or ""))
            or schedule_by_board_game.get(str(player.get("schedule_game_key") or ""))
            or match_player_to_schedule(player, schedule)
        )
        fallback = matchup_fallback.get(int(player.get("player_id") or 0), {})
        if not game and not fallback:
            player["opposing_pitcher"] = "Awaiting announcement"
            player["opposing_pitcher_hand"] = "—"
            player["probable_pitcher_status"] = "game not matched"
            player["pitching_data_available"] = False
            continue
        game = game or {}
        player["schedule_game_key"] = game.get("schedule_game_key") or player.get("schedule_game_key")
        player["mlb_game_pk"] = game.get("mlb_game_pk")
        player["game_time"] = game.get("game_time") or player.get("game_time")
        player["venue_name"] = game.get("venue_name") or player.get("venue_name")
        player["home_team_name"] = game.get("home_team_name")
        player["away_team_name"] = game.get("away_team_name")
        team = _norm(player.get("team_name"))
        try:
            player_team_id = int(player.get("team_id") or 0)
        except (TypeError, ValueError):
            player_team_id = 0
        if player_team_id and player_team_id == int(game.get("home_team_id") or 0):
            opponent_side = "away"
        elif player_team_id and player_team_id == int(game.get("away_team_id") or 0):
            opponent_side = "home"
        else:
            opponent_side = (
                "away" if team == _norm(game.get("home_team_name"))
                else "home" if team == _norm(game.get("away_team_name"))
                else ""
            )
        pitcher = {
            "id": game.get(f"{opponent_side}_probable_pitcher_id") if game and opponent_side else None,
            "fullName": game.get(f"{opponent_side}_probable_pitcher") if game and opponent_side else None,
        }
        fallback = matchup_fallback.get(int(player.get("player_id") or 0), {})
        pitcher_id = int(pitcher.get("id") or fallback.get("id") or 0)
        info = pitcher_data.get(pitcher_id, {})
        player["opposing_pitcher_id"] = pitcher_id or None
        player["opposing_pitcher"] = (
            info.get("name")
            or pitcher.get("fullName")
            or fallback.get("name")
            or "Awaiting announcement"
        )
        player["opposing_pitcher_hand"] = info.get("hand") or fallback.get("hand") or "—"
        player["probable_pitcher_status"] = (
            "announced by MLB" if pitcher.get("id")
            else "projected by Ballpark Pal" if fallback
            else "awaiting announcement"
        )
        player["pitcher_era"] = info.get("era")
        player["pitcher_whip"] = info.get("whip")
        player["pitcher_hr9"] = info.get("hr9")
        player["pitcher_home_runs_allowed"] = info.get("home_runs_allowed")
        player["pitcher_innings"] = info.get("innings")
        player["pitcher_strikeouts"] = info.get("strikeouts")
        player["pitcher_strikeouts_per9"] = info.get("strikeouts_per9")
        player["pitching_data_available"] = bool(info.get("name") or fallback.get("name"))
        # The model uses this only when real pitcher data is available.
        player["pitcher_vulnerability_signal"] = round(
            _num(info.get("hr9")) * 32.0 + max(0.0, _num(info.get("era")) - 3.5) * 5.0,
            2,
        ) if info.get("name") else 0.0

    fallback_count = sum(1 for player in players if str(player.get("probable_pitcher_status") or "").startswith("projected"))
    status = "live" if announced else f"projected fallback ({fallback_count})" if fallback_count else "awaiting announcements"
    return players, games_meta, status
