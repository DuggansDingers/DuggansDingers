from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

BALLPARK_API_KEY = (os.getenv("BALLPARKPAL_API_KEY") or "").strip()
BALLPARK_BASE_URL = "https://www.ballparkpal.com/api/v1"
MLB_BASE_URL = "https://statsapi.mlb.com/api/v1"

BASE_DIR = Path(__file__).resolve().parent
NAME_CACHE_FILE = BASE_DIR / "name_cache.json"
STATS_CACHE_FILE = BASE_DIR / "mlb_stats_cache.json"

BALLPARK_HEADERS = {"X-API-Key": BALLPARK_API_KEY} if BALLPARK_API_KEY else {}


def get_json(url: str, *, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
    response = requests.get(url, params=params, headers=headers, timeout=35)
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, dict) else {}


def load_json_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8-sig") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return default


def save_json_file(path: Path, data: Any) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)
    except OSError:
        # A locked OneDrive file should not prevent the live board from loading.
        pass


def safe_number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def safe_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def first_value(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def load_name_cache() -> dict[str, Any]:
    cache = load_json_file(NAME_CACHE_FILE, {})
    if not isinstance(cache, dict):
        cache = {}
    cache.setdefault("players", {})
    cache.setdefault("player_details", {})
    cache.setdefault("teams", {})
    cache.setdefault("team_details", {})
    return cache


def get_player_details(player_id: Any, cache: dict[str, Any]) -> dict[str, Any]:
    key = str(player_id)
    cached = cache["player_details"].get(key)
    if isinstance(cached, dict) and cached.get("player_name"):
        return cached

    # Preserve compatibility with the original name-only cache.
    cached_name = cache["players"].get(key)
    result = get_json(f"{MLB_BASE_URL}/people/{player_id}")
    people = result.get("people", [])
    person = people[0] if people else {}
    details = {
        "player_name": first_value(person.get("fullName"), cached_name, f"Player {player_id}"),
        "position": first_value((person.get("primaryPosition") or {}).get("abbreviation"), "—"),
        "bat_side": first_value((person.get("batSide") or {}).get("code"), "—"),
        "current_team_id": (person.get("currentTeam") or {}).get("id"),
    }
    cache["players"][key] = details["player_name"]
    cache["player_details"][key] = details
    return details


def get_team_details(team_id: Any, cache: dict[str, Any]) -> dict[str, Any]:
    if not team_id:
        return {"team_name": "N/A", "team_full_name": "N/A"}
    key = str(team_id)
    cached = cache["team_details"].get(key)
    if isinstance(cached, dict) and cached.get("team_name"):
        return cached

    result = get_json(f"{MLB_BASE_URL}/teams/{team_id}")
    teams = result.get("teams", [])
    team = teams[0] if teams else {}
    abbreviation = first_value(team.get("abbreviation"), cache["teams"].get(key), team.get("teamName"), f"Team {team_id}")
    details = {
        "team_name": abbreviation,
        "team_full_name": first_value(team.get("name"), team.get("clubName"), abbreviation),
        "league": (team.get("league") or {}).get("name", ""),
        "division": (team.get("division") or {}).get("name", ""),
    }
    cache["teams"][key] = abbreviation
    cache["team_details"][key] = details
    return details


def hr_rate(home_runs: Any, plate_appearances: Any) -> float:
    pa = safe_number(plate_appearances)
    return round(safe_number(home_runs) / pa * 100, 2) if pa > 0 else 0.0


def window_stats(game_log: list[dict[str, Any]], games: int) -> dict[str, Any]:
    sample = game_log[:games]
    home_runs = sum(safe_number((row.get("stat") or {}).get("homeRuns")) for row in sample)
    plate_appearances = sum(safe_number((row.get("stat") or {}).get("plateAppearances")) for row in sample)
    hits = sum(safe_number((row.get("stat") or {}).get("hits")) for row in sample)
    at_bats = sum(safe_number((row.get("stat") or {}).get("atBats")) for row in sample)
    return {
        "games": len(sample),
        "home_runs": int(home_runs),
        "plate_appearances": int(plate_appearances),
        "hits": int(hits),
        "at_bats": int(at_bats),
        "hr_rate": hr_rate(home_runs, plate_appearances),
        "avg": round(hits / at_bats, 3) if at_bats else 0.0,
    }


def empty_player_stats() -> dict[str, Any]:
    return {
        "season_games": 0,
        "season_home_runs": 0,
        "season_plate_appearances": 0,
        "season_hr_rate": 0.0,
        "season_avg": 0.0,
        "season_obp": 0.0,
        "season_slg": 0.0,
        "season_ops": 0.0,
        "season_rbi": 0,
        "season_hits": 0,
        "season_doubles": 0,
        "season_triples": 0,
        "season_walks": 0,
        "season_strikeouts": 0,
        "last_7_games": 0,
        "last_7_home_runs": 0,
        "last_7_plate_appearances": 0,
        "last_7_hr_rate": 0.0,
        "last_15_games": 0,
        "last_15_home_runs": 0,
        "last_15_plate_appearances": 0,
        "last_15_hr_rate": 0.0,
        "last_30_games": 0,
        "last_30_home_runs": 0,
        "last_30_plate_appearances": 0,
        "last_30_hr_rate": 0.0,
        "recent_games": 0,
        "recent_home_runs": 0,
        "recent_plate_appearances": 0,
        "recent_hr_rate": 0.0,
        "recent_game_hr_series": [],
        "recent_game_dates": [],
    }


def get_player_hitting_stats(player_id: Any, season: int, target_date: str, stats_cache: dict[str, Any]) -> dict[str, Any]:
    cache_key = f"v8_{target_date}_{season}_{player_id}"
    cached = stats_cache.get(cache_key)
    if isinstance(cached, dict) and "last_30_home_runs" in cached:
        return cached

    result = get_json(
        f"{MLB_BASE_URL}/people/{player_id}/stats",
        params={"stats": "season,gameLog", "group": "hitting", "season": season},
    )

    season_stat: dict[str, Any] = {}
    game_log: list[dict[str, Any]] = []
    for stats_group in result.get("stats", []):
        display_name = str((stats_group.get("type") or {}).get("displayName", "")).replace(" ", "").lower()
        splits = stats_group.get("splits", []) or []
        if display_name == "season" and splits:
            season_stat = splits[0].get("stat", {}) or {}
        elif display_name in {"gamelog", "gamebygame"}:
            game_log.extend(splits)

    game_log.sort(key=lambda split: str(split.get("date", "")), reverse=True)
    # MLB may include postponed/future rows. Keep played rows through the selected slate date.
    game_log = [row for row in game_log if not row.get("date") or str(row.get("date")) <= target_date]

    seven = window_stats(game_log, 7)
    fifteen = window_stats(game_log, 15)
    thirty = window_stats(game_log, 30)

    stats = {
        "season_games": safe_int(season_stat.get("gamesPlayed")),
        "season_home_runs": safe_int(season_stat.get("homeRuns")),
        "season_plate_appearances": safe_int(season_stat.get("plateAppearances")),
        "season_hr_rate": hr_rate(season_stat.get("homeRuns"), season_stat.get("plateAppearances")),
        "season_avg": safe_number(season_stat.get("avg")),
        "season_obp": safe_number(season_stat.get("obp")),
        "season_slg": safe_number(season_stat.get("slg")),
        "season_ops": safe_number(season_stat.get("ops")),
        "season_rbi": safe_int(season_stat.get("rbi")),
        "season_hits": safe_int(season_stat.get("hits")),
        "season_doubles": safe_int(season_stat.get("doubles")),
        "season_triples": safe_int(season_stat.get("triples")),
        "season_walks": safe_int(season_stat.get("baseOnBalls")),
        "season_strikeouts": safe_int(season_stat.get("strikeOuts")),
        "last_7_games": seven["games"],
        "last_7_home_runs": seven["home_runs"],
        "last_7_plate_appearances": seven["plate_appearances"],
        "last_7_hr_rate": seven["hr_rate"],
        "last_7_avg": seven["avg"],
        "last_15_games": fifteen["games"],
        "last_15_home_runs": fifteen["home_runs"],
        "last_15_plate_appearances": fifteen["plate_appearances"],
        "last_15_hr_rate": fifteen["hr_rate"],
        "last_15_avg": fifteen["avg"],
        "last_30_games": thirty["games"],
        "last_30_home_runs": thirty["home_runs"],
        "last_30_plate_appearances": thirty["plate_appearances"],
        "last_30_hr_rate": thirty["hr_rate"],
        "last_30_avg": thirty["avg"],
        # Backward-compatible recent fields use the 15-game window.
        "recent_games": fifteen["games"],
        "recent_home_runs": fifteen["home_runs"],
        "recent_plate_appearances": fifteen["plate_appearances"],
        "recent_hr_rate": fifteen["hr_rate"],
        "recent_game_hr_series": [safe_int((row.get("stat") or {}).get("homeRuns")) for row in reversed(game_log[:15])],
        "recent_game_dates": [str(row.get("date", "")) for row in reversed(game_log[:15])],
    }
    stats_cache[cache_key] = stats
    return stats


def percentile_scores(values: list[float]) -> list[float]:
    if not values:
        return []
    if len(values) == 1:
        return [100.0]
    sorted_unique = sorted(set(values))
    if len(sorted_unique) == 1:
        return [50.0 for _ in values]
    lookup = {value: index / (len(sorted_unique) - 1) * 100 for index, value in enumerate(sorted_unique)}
    return [round(lookup[value], 1) for value in values]


def add_dinger_scores(rankings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create an absolute-aware 0-100 score.

    Earlier versions were almost entirely percentile based, which could make a
    low absolute HR probability look elite on a weak slate. V15 anchors the
    score to the player's actual model probability first, then layers real
    season/recent power, Statcast, and the announced opposing starter.
    """
    def clamp(value: float) -> float:
        return max(0.0, min(100.0, value))

    projection_values = [safe_number(player.get("probability")) for player in rankings]
    statcast_values = [safe_number(player.get("hitter_statcast_signal")) for player in rankings]
    pitcher_values = [safe_number(player.get("pitcher_vulnerability_signal")) for player in rankings]

    projection_percentiles = percentile_scores(projection_values)
    statcast_percentiles = percentile_scores(statcast_values)
    pitcher_percentiles = percentile_scores(pitcher_values)

    scored: list[dict[str, Any]] = []
    for index, player in enumerate(rankings):
        probability = safe_number(player.get("probability"))
        if probability > 1:
            probability /= 100
        probability = max(0.0, min(1.0, probability))

        projection_absolute = clamp(probability / 0.35 * 100)
        season_absolute = clamp(safe_number(player.get("season_hr_rate")) / 8.0 * 100)
        seven_absolute = clamp(safe_number(player.get("last_7_hr_rate")) / 12.0 * 100)
        thirty_absolute = clamp(safe_number(player.get("last_30_hr_rate")) / 9.0 * 100)
        slug_absolute = clamp((safe_number(player.get("season_slg")) - 0.300) / 0.350 * 100)
        statcast_score = statcast_percentiles[index] if player.get("statcast_available") else 50.0
        pitcher_score = pitcher_percentiles[index] if player.get("pitching_data_available") else 50.0

        dinger_score = (
            projection_absolute * 0.45
            + projection_percentiles[index] * 0.15
            + season_absolute * 0.10
            + seven_absolute * 0.07
            + thirty_absolute * 0.06
            + slug_absolute * 0.06
            + statcast_score * 0.06
            + pitcher_score * 0.05
        )
        dinger_score = round(clamp(dinger_score), 1)

        if dinger_score >= 85:
            tier = "Elite"
        elif dinger_score >= 78:
            tier = "Premium"
        elif dinger_score >= 70:
            tier = "Strong"
        elif dinger_score >= 60:
            tier = "Upside"
        else:
            tier = "Speculative"

        reasons: list[str] = [f"{probability * 100:.1f}% model HR probability"]
        if safe_number(player.get("last_7_hr_rate")) > max(
            safe_number(player.get("season_hr_rate")), safe_number(player.get("last_30_hr_rate"))
        ) and safe_int(player.get("last_7_home_runs")):
            reasons.append(f"{safe_int(player.get('last_7_home_runs'))} HR in the last 7 games")
        elif safe_int(player.get("last_30_home_runs")) >= 5:
            reasons.append(f"{safe_int(player.get('last_30_home_runs'))} HR in the last 30 games")
        if player.get("pitching_data_available"):
            reasons.append(
                f"vs {player.get('opposing_pitcher')} ({safe_number(player.get('pitcher_hr9')):.2f} HR/9)"
            )
        elif player.get("opposing_pitcher") and player.get("opposing_pitcher") != "Not announced":
            reasons.append(f"vs {player.get('opposing_pitcher')}")
        if player.get("statcast_available") and safe_number(player.get("barrel_pct")) >= 10:
            reasons.append(f"{safe_number(player.get('barrel_pct')):.1f}% barrel rate")
        if safe_number(player.get("season_slg")) >= 0.500:
            reasons.append(f"{safe_number(player.get('season_slg')):.3f} season SLG")

        scored.append({
            **player,
            "ballpark_score": round(projection_absolute, 1),
            "projection_percentile": projection_percentiles[index],
            "season_power_score": round(season_absolute, 1),
            "recent_power_score": round(seven_absolute, 1),
            "month_power_score": round(thirty_absolute, 1),
            "slug_power_score": round(slug_absolute, 1),
            "statcast_power_score": round(statcast_score, 1),
            "pitcher_matchup_score": round(pitcher_score, 1),
            "dinger_score": dinger_score,
            "model_tier": tier,
            "projection_reasons": reasons[:3],
        })

    scored.sort(key=lambda player: safe_number(player.get("dinger_score")), reverse=True)
    team_counts: dict[str, int] = {}
    for overall_rank, player in enumerate(scored, 1):
        team = str(player.get("team_name") or "N/A")
        team_counts[team] = team_counts.get(team, 0) + 1
        player["overall_rank"] = overall_rank
        player["team_rank"] = team_counts[team]
    return scored

def game_metadata(game: dict[str, Any]) -> dict[str, Any]:
    teams = game.get("teams") or {}
    home = game.get("homeTeam") or (teams.get("home") or {}).get("team") or {}
    away = game.get("awayTeam") or (teams.get("away") or {}).get("team") or {}
    venue = game.get("venue") or {}
    return {
        "game_id": first_value(game.get("gameId"), game.get("id"), game.get("gamePk")),
        "game_time": first_value(game.get("gameTime"), game.get("gameDate"), game.get("startTime")),
        "home_team_id": first_value(game.get("homeTeamId"), home.get("id")),
        "away_team_id": first_value(game.get("awayTeamId"), away.get("id")),
        "home_team_name": first_value(game.get("homeTeamAbbreviation"), home.get("abbreviation"), home.get("name")),
        "away_team_name": first_value(game.get("awayTeamAbbreviation"), away.get("abbreviation"), away.get("name")),
        "venue_name": first_value(game.get("venueName"), venue.get("name"), game.get("ballpark")),
    }


def get_home_run_rankings(target_date: str | None = None) -> dict[str, Any]:
    if not BALLPARK_API_KEY:
        raise RuntimeError("BALLPARKPAL_API_KEY was not found in your .env file.")

    slate_date = target_date or date.today().isoformat()
    try:
        season = int(slate_date[:4])
    except (TypeError, ValueError):
        season = date.today().year

    name_cache = load_name_cache()
    stats_cache = load_json_file(STATS_CACHE_FILE, {})
    if not isinstance(stats_cache, dict):
        stats_cache = {}

    games_result = get_json(
        f"{BALLPARK_BASE_URL}/games",
        params={"date": slate_date},
        headers=BALLPARK_HEADERS,
    )
    games = ((games_result.get("data") or {}).get("items") or [])
    game_map: dict[str, dict[str, Any]] = {}
    for game in games:
        meta = game_metadata(game)
        if meta.get("game_id"):
            game_map[str(meta["game_id"])] = meta

    home_run_props: list[dict[str, Any]] = []
    for game in games:
        meta = game_metadata(game)
        game_id = meta.get("game_id")
        if not game_id:
            continue
        result = get_json(
            f"{BALLPARK_BASE_URL}/projections/probabilities",
            params={"gameId": game_id},
            headers=BALLPARK_HEADERS,
        )
        items = ((result.get("data") or {}).get("items") or [])
        for item in items:
            display_name = str(item.get("displayName", "")).lower()
            side = str(item.get("side", "")).lower()
            line = safe_number(item.get("line"))
            subject = item.get("subject") or {}
            if not ("home run" in display_name and side == "over" and line == 0.5 and subject.get("type") == "player"):
                continue
            player_id = subject.get("id")
            if not player_id:
                continue
            team_id = item.get("teamId")
            opponent_team_id = None
            if team_id and meta.get("home_team_id") and meta.get("away_team_id"):
                opponent_team_id = meta["away_team_id"] if str(team_id) == str(meta["home_team_id"]) else meta["home_team_id"]
            home_run_props.append({
                **meta,
                "player_id": player_id,
                "team_id": team_id,
                "opponent_team_id": opponent_team_id,
                "probability": safe_number(item.get("probability")),
                "fair_odds": item.get("odds"),
                "projected_hr_average": item.get("average"),
            })

    # Keep the strongest projection if the feed includes a duplicate player.
    unique_players: dict[str, dict[str, Any]] = {}
    for prop in home_run_props:
        key = str(prop["player_id"])
        if key not in unique_players or safe_number(prop.get("probability")) > safe_number(unique_players[key].get("probability")):
            unique_players[key] = prop
    home_run_props = list(unique_players.values())

    def enrich_player(prop: dict[str, Any]) -> dict[str, Any]:
        enriched = dict(prop)
        try:
            enriched.update(get_player_details(enriched["player_id"], name_cache))
        except requests.RequestException:
            enriched.update({"player_name": f"Player {enriched['player_id']}", "position": "—", "bat_side": "—"})

        try:
            enriched.update(get_team_details(enriched.get("team_id"), name_cache))
        except requests.RequestException:
            enriched.update({"team_name": str(enriched.get("team_id") or "N/A"), "team_full_name": "N/A"})

        if enriched.get("opponent_team_id"):
            try:
                opponent = get_team_details(enriched["opponent_team_id"], name_cache)
                enriched["opponent"] = opponent.get("team_name", "—")
            except requests.RequestException:
                enriched["opponent"] = "—"
        else:
            enriched["opponent"] = "—"

        try:
            enriched.update(get_player_hitting_stats(enriched["player_id"], season, slate_date, stats_cache))
        except requests.RequestException:
            enriched.update(empty_player_stats())
        return enriched

    # MLB player detail and rolling-stat calls are independent. Running a
    # bounded pool cuts a cold load dramatically without overwhelming StatsAPI.
    enriched_props: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=min(10, max(1, len(home_run_props)))) as executor:
        futures = {executor.submit(enrich_player, prop): index for index, prop in enumerate(home_run_props)}
        completed: dict[int, dict[str, Any]] = {}
        for future in as_completed(futures):
            index = futures[future]
            try:
                completed[index] = future.result()
            except Exception:
                fallback = dict(home_run_props[index])
                fallback.update(empty_player_stats())
                completed[index] = fallback
        enriched_props = [completed[index] for index in range(len(home_run_props))]
    home_run_props = enriched_props

    save_json_file(NAME_CACHE_FILE, name_cache)
    save_json_file(STATS_CACHE_FILE, stats_cache)

    from services.statcast import enrich_players
    from services.pitchers import enrich_probable_pitchers

    home_run_props, statcast_status = enrich_players(home_run_props, slate_date, season)
    games_meta = list(game_map.values())
    home_run_props, games_meta, pitcher_status = enrich_probable_pitchers(
        home_run_props, games_meta, slate_date, season
    )
    scored_rankings = add_dinger_scores(home_run_props)
    teams = sorted({str(player.get("team_name") or "N/A") for player in scored_rankings if player.get("team_name")})
    return {
        "date": slate_date,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "games": len(games),
        "games_meta": games_meta,
        "teams": teams,
        "rankings": scored_rankings,
        "data_sources": {
            "Ballpark Pal": "live",
            "MLB Stats": "live",
            "Weather": "not connected",
            "Sportsbook Odds": "not connected",
            "Statcast": statcast_status,
            "Probable Pitchers": pitcher_status,
        },
    }
