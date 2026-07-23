import json
from datetime import date
from pathlib import Path

import requests

MLB_BASE_URL = "https://statsapi.mlb.com/api/v1"
STATS_CACHE_FILE = Path("mlb_stats_cache.json")


def load_stats_cache():
    if not STATS_CACHE_FILE.exists():
        return {}

    try:
        with STATS_CACHE_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}


def save_stats_cache(cache):
    with STATS_CACHE_FILE.open("w", encoding="utf-8") as file:
        json.dump(cache, file, indent=2)


def safe_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def calculate_hr_rate(home_runs, plate_appearances):
    home_runs = safe_number(home_runs)
    plate_appearances = safe_number(plate_appearances)

    if plate_appearances <= 0:
        return 0.0

    return home_runs / plate_appearances


def get_player_hitting_stats(player_id, season, cache):
    """
    Gets:
    - Full-season home runs and plate appearances
    - Home runs and plate appearances from the player's last 15 games
    """

    today = date.today().isoformat()
    cache_key = f"{today}_{season}_{player_id}"

    if cache_key in cache:
        return cache[cache_key]

    url = f"{MLB_BASE_URL}/people/{player_id}/stats"

    response = requests.get(
        url,
        params={
            "stats": "season,gameLog",
            "group": "hitting",
            "season": season,
        },
        timeout=30,
    )

    response.raise_for_status()
    result = response.json()

    season_home_runs = 0
    season_plate_appearances = 0
    game_log_splits = []

    for stats_group in result.get("stats", []):
        stats_type = (
            stats_group.get("type", {})
            .get("displayName", "")
            .lower()
        )

        splits = stats_group.get("splits", [])

        if stats_type == "season":
            if splits:
                season_stat = splits[0].get("stat", {})

                season_home_runs = safe_number(
                    season_stat.get("homeRuns")
                )

                season_plate_appearances = safe_number(
                    season_stat.get("plateAppearances")
                )

        elif stats_type == "game log":
            game_log_splits.extend(splits)

    game_log_splits.sort(
        key=lambda split: split.get("date", ""),
        reverse=True,
    )

    last_15_games = game_log_splits[:15]

    recent_home_runs = 0
    recent_plate_appearances = 0

    for game in last_15_games:
        game_stat = game.get("stat", {})

        recent_home_runs += safe_number(
            game_stat.get("homeRuns")
        )

        recent_plate_appearances += safe_number(
            game_stat.get("plateAppearances")
        )

    player_stats = {
        "season_home_runs": int(season_home_runs),
        "season_plate_appearances": int(
            season_plate_appearances
        ),
        "season_hr_rate": calculate_hr_rate(
            season_home_runs,
            season_plate_appearances,
        ),
        "recent_games": len(last_15_games),
        "recent_home_runs": int(recent_home_runs),
        "recent_plate_appearances": int(
            recent_plate_appearances
        ),
        "recent_hr_rate": calculate_hr_rate(
            recent_home_runs,
            recent_plate_appearances,
        ),
    }

    cache[cache_key] = player_stats
    return player_stats


def add_mlb_stats_to_rankings(rankings, season):
    cache = load_stats_cache()
    completed_rankings = []

    total_players = len(rankings)

    for number, player in enumerate(rankings, start=1):
        print(
            f"Getting MLB stats for player "
            f"{number} of {total_players}: "
            f"{player['player_name']}"
        )

        try:
            player_stats = get_player_hitting_stats(
                player_id=player["player_id"],
                season=season,
                cache=cache,
            )

        except requests.RequestException as error:
            print(
                f"Could not retrieve stats for "
                f"{player['player_name']}: {error}"
            )

            player_stats = {
                "season_home_runs": 0,
                "season_plate_appearances": 0,
                "season_hr_rate": 0.0,
                "recent_games": 0,
                "recent_home_runs": 0,
                "recent_plate_appearances": 0,
                "recent_hr_rate": 0.0,
            }

        completed_player = {
            **player,
            **player_stats,
        }

        completed_rankings.append(completed_player)

        # Save continuously so progress is not lost.
        if number % 10 == 0:
            save_stats_cache(cache)

    save_stats_cache(cache)

    return completed_rankings