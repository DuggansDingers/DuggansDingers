from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import requests

BASE_DIR = Path(__file__).resolve().parents[1]
CACHE_FILE = BASE_DIR / "data" / "cache" / "statcast_pitching.json"
MLB_BASE_URL = "https://statsapi.mlb.com/api/v1"


def _num(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


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


def _team_tokens(team: dict[str, Any]) -> set[str]:
    values = {
        str(team.get("id") or ""),
        str(team.get("abbreviation") or ""),
        str(team.get("teamName") or ""),
        str(team.get("clubName") or ""),
        str(team.get("name") or ""),
        str(team.get("shortName") or ""),
    }
    tokens: set[str] = set()
    for value in values:
        text = "".join(ch.lower() for ch in value if ch.isalnum())
        if text:
            tokens.add(text)
    return tokens


def _schedule_probables(target_date: str) -> list[dict[str, Any]]:
    response = requests.get(
        f"{MLB_BASE_URL}/schedule",
        params={
            "sportId": 1,
            "date": target_date,
            "hydrate": "probablePitcher,team",
        },
        timeout=30,
    )
    response.raise_for_status()
    games: list[dict[str, Any]] = []
    for day in response.json().get("dates", []):
        for game in day.get("games", []):
            teams = game.get("teams", {})
            home = teams.get("home", {})
            away = teams.get("away", {})
            home_team = home.get("team") or {}
            away_team = away.get("team") or {}
            games.append({
                "game_pk": game.get("gamePk"),
                "home_tokens": _team_tokens(home_team),
                "away_tokens": _team_tokens(away_team),
                "home_pitcher": home.get("probablePitcher") or {},
                "away_pitcher": away.get("probablePitcher") or {},
            })
    return games


def _norm_team(value: Any) -> str:
    return "".join(ch.lower() for ch in str(value or "") if ch.isalnum())


def _find_game(schedule: list[dict[str, Any]], player: dict[str, Any]) -> dict[str, Any]:
    home_candidates = {
        _norm_team(player.get("home_team_id")),
        _norm_team(player.get("home_team_name")),
    }
    away_candidates = {
        _norm_team(player.get("away_team_id")),
        _norm_team(player.get("away_team_name")),
    }
    team_token = _norm_team(player.get("team_name"))
    opp_token = _norm_team(player.get("opponent"))
    home_candidates.discard("")
    away_candidates.discard("")

    for game in schedule:
        if home_candidates & game.get("home_tokens", set()) and away_candidates & game.get("away_tokens", set()):
            return game
        if away_candidates & game.get("home_tokens", set()) and home_candidates & game.get("away_tokens", set()):
            return game
        tokens = game.get("home_tokens", set()) | game.get("away_tokens", set())
        if team_token and opp_token and team_token in tokens and opp_token in tokens:
            return game
    return {}


def _pitcher_stats(pitcher_id: int, season: int) -> dict[str, Any]:
    response = requests.get(
        f"{MLB_BASE_URL}/people/{pitcher_id}/stats",
        params={"stats": "season", "group": "pitching", "season": season},
        timeout=30,
    )
    response.raise_for_status()
    splits = []
    for group in response.json().get("stats", []):
        splits.extend(group.get("splits", []) or [])
    stat = (splits[0].get("stat") if splits else {}) or {}
    return {
        "pitcher_era": _num(stat.get("era")),
        "pitcher_whip": _num(stat.get("whip")),
        "pitcher_hr9": _num(stat.get("homeRunsPer9")),
        "pitcher_home_runs_allowed": int(_num(stat.get("homeRuns"))),
        "pitcher_innings": _num(stat.get("inningsPitched")),
        "pitcher_strikeouts": int(_num(stat.get("strikeOuts"))),
    }


def _leaderboards(season: int) -> tuple[dict[int, dict[str, Any]], dict[int, dict[str, Any]], str]:
    try:
        try:
            from pybaseball import statcast_batter_exitvelo_barrels as batter_barrels
            from pybaseball import statcast_pitcher_exitvelo_barrels as pitcher_barrels
        except ImportError:
            from pybaseball import statcast_batter_exit_velocity_barrels as batter_barrels
            from pybaseball import statcast_pitcher_exit_velocity_barrels as pitcher_barrels
    except Exception:
        return {}, {}, "pybaseball import failed"

    def rows(frame: Any, pitcher: bool) -> dict[int, dict[str, Any]]:
        if frame is None or getattr(frame, "empty", True):
            return {}
        output: dict[int, dict[str, Any]] = {}
        for _, row in frame.iterrows():
            raw_id = row.get("player_id")
            try:
                player_id = int(raw_id)
            except (TypeError, ValueError):
                continue
            prefix = "pitcher_" if pitcher else ""
            output[player_id] = {
                f"{prefix}avg_exit_velocity": _num(row.get("avg_hit_speed")),
                f"{prefix}max_exit_velocity": _num(row.get("max_hit_speed")),
                f"{prefix}barrel_pct": _num(row.get("brl_percent")),
                f"{prefix}hard_hit_pct": _num(row.get("ev95percent")),
                f"{prefix}sweet_spot_pct": _num(row.get("anglesweetspotpercent")),
            }
        return output

    try:
        import inspect

        def call_supported(func: Any, **kwargs: Any) -> Any:
            params = inspect.signature(func).parameters
            return func(**{k: v for k, v in kwargs.items() if k in params})

        hitters = call_supported(batter_barrels, year=season, season=season, minPA=25)
        pitchers = call_supported(pitcher_barrels, year=season, season=season, minBBE=25)
        return rows(hitters, False), rows(pitchers, True), "live"
    except Exception as exc:
        return {}, {}, f"unavailable: {exc}"


def enrich_players(players: list[dict[str, Any]], target_date: str, season: int) -> tuple[list[dict[str, Any]], str]:
    cache = _load_cache()
    cache_key = f"statcast_v2_{target_date}_{season}"
    cached = cache.get(cache_key)
    if isinstance(cached, dict) and str(cached.get("status") or "").lower() not in {"pybaseball not installed", "pybaseball import failed"} and not str(cached.get("status") or "").lower().startswith("unavailable"):
        hitter_board = {int(k): v for k, v in (cached.get("hitters") or {}).items()}
        pitcher_board = {int(k): v for k, v in (cached.get("pitchers") or {}).items()}
        statcast_status = str(cached.get("status") or "cached")
    else:
        hitter_board, pitcher_board, statcast_status = _leaderboards(season)
        cache[cache_key] = {
            "hitters": {str(k): v for k, v in hitter_board.items()},
            "pitchers": {str(k): v for k, v in pitcher_board.items()},
            "status": statcast_status,
        }
        _save_cache(cache)

    try:
        schedule = _schedule_probables(target_date)
    except requests.RequestException:
        schedule = {}

    pitcher_stats_cache: dict[int, dict[str, Any]] = {}
    for player in players:
        player_id = int(player.get("player_id") or 0)
        player.update(hitter_board.get(player_id, {}))

        game = _find_game(schedule, player)
        team_token = _norm_team(player.get("team_name"))
        home_tokens = game.get("home_tokens", set())
        away_tokens = game.get("away_tokens", set())
        if team_token and team_token in home_tokens:
            pitcher = game.get("away_pitcher") or {}
        elif team_token and team_token in away_tokens:
            pitcher = game.get("home_pitcher") or {}
        else:
            # Ballpark Pal team ids are not MLB Stats API ids, so fall back to
            # the opponent abbreviation/name when direct matching is unavailable.
            opp_token = _norm_team(player.get("opponent"))
            if opp_token in home_tokens:
                pitcher = game.get("home_pitcher") or {}
            elif opp_token in away_tokens:
                pitcher = game.get("away_pitcher") or {}
            else:
                pitcher = {}
        pitcher_id = int(pitcher.get("id") or 0)
        player["opposing_pitcher_id"] = pitcher_id or None
        player["opposing_pitcher"] = pitcher.get("fullName") or "TBD"
        player["opposing_pitcher_hand"] = "—"

        if pitcher_id:
            player.update(pitcher_board.get(pitcher_id, {}))
            if pitcher_id not in pitcher_stats_cache:
                try:
                    pitcher_stats_cache[pitcher_id] = _pitcher_stats(pitcher_id, season)
                except requests.RequestException:
                    pitcher_stats_cache[pitcher_id] = {}
            player.update(pitcher_stats_cache[pitcher_id])
            try:
                details = requests.get(f"{MLB_BASE_URL}/people/{pitcher_id}", timeout=20).json().get("people", [{}])[0]
                player["opposing_pitcher_hand"] = (details.get("pitchHand") or {}).get("code") or "—"
            except Exception:
                pass

        hitter_signal = (
            _num(player.get("barrel_pct")) * 0.45
            + _num(player.get("hard_hit_pct")) * 0.35
            + max(0.0, _num(player.get("avg_exit_velocity")) - 80.0) * 0.20
        )
        pitcher_signal = (
            _num(player.get("pitcher_hr9")) * 28.0
            + _num(player.get("pitcher_barrel_pct")) * 0.45
            + _num(player.get("pitcher_hard_hit_pct")) * 0.20
        )
        player["hitter_statcast_signal"] = round(hitter_signal, 2)
        player["pitcher_vulnerability_signal"] = round(pitcher_signal, 2)
        player["statcast_available"] = bool(player.get("barrel_pct") or player.get("hard_hit_pct"))
        player["pitching_data_available"] = pitcher_id > 0

    return players, statcast_status
