from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import numpy as np
import requests
import streamlit as st

MLB_BASE_URL = "https://statsapi.mlb.com/api/v1"


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _team_season_stats(team_id: int, season: int) -> dict[str, float]:
    response = requests.get(
        f"{MLB_BASE_URL}/teams/{team_id}/stats",
        params={"stats": "season", "group": "hitting", "season": season},
        timeout=25,
    )
    response.raise_for_status()
    splits: list[dict[str, Any]] = []
    for group in response.json().get("stats", []):
        splits.extend(group.get("splits") or [])
    stat = (splits[0].get("stat") if splits else {}) or {}
    games = max(1.0, _num(stat.get("gamesPlayed"), 1.0))
    return {
        "games": games,
        "runs_pg": _num(stat.get("runs"), 4.4 * games) / games,
        "hits_pg": _num(stat.get("hits"), 8.2 * games) / games,
        "hr_pg": _num(stat.get("homeRuns"), 1.1 * games) / games,
        "so_pg": _num(stat.get("strikeOuts"), 8.5 * games) / games,
        "sb_pg": _num(stat.get("stolenBases"), 0.7 * games) / games,
        "source": "MLB season stats",
    }


@st.cache_data(ttl=21600, show_spinner=False)
def fetch_team_stats(team_ids: tuple[int, ...], season: int) -> dict[int, dict[str, float]]:
    output: dict[int, dict[str, float]] = {}
    with ThreadPoolExecutor(max_workers=min(8, max(1, len(team_ids)))) as executor:
        futures = {executor.submit(_team_season_stats, team_id, season): team_id for team_id in team_ids}
        for future in as_completed(futures):
            team_id = futures[future]
            try:
                output[team_id] = future.result()
            except requests.RequestException:
                output[team_id] = {
                    "games": 1,
                    "runs_pg": 4.4,
                    "hits_pg": 8.2,
                    "hr_pg": 1.1,
                    "so_pg": 8.5,
                    "sb_pg": 0.7,
                    "source": "league-average fallback",
                }
    return output


def _player_probability(player: dict[str, Any]) -> float:
    value = _num(player.get("probability"))
    return max(0.0, min(1.0, value if value <= 1 else value / 100))


def _poisson_nonnegative(rng: np.random.Generator, mean: float, size: int) -> np.ndarray:
    return rng.poisson(max(0.05, mean), size=size)


def _opposing_pitcher_adjustment(players: list[dict[str, Any]]) -> tuple[float, float]:
    announced = [p for p in players if p.get("pitching_data_available")]
    if not announced:
        return 1.0, 1.0
    sample = announced[0]
    era = _num(sample.get("pitcher_era"), 4.2)
    hr9 = _num(sample.get("pitcher_hr9"), 1.15)
    run_factor = max(0.78, min(1.28, 1 + (era - 4.2) * 0.055))
    hr_factor = max(0.72, min(1.35, 1 + (hr9 - 1.15) * 0.22))
    return run_factor, hr_factor


def simulate_game(
    game_key: str,
    away: str,
    home: str,
    away_id: int,
    home_id: int,
    players: list[dict[str, Any]],
    team_stats: dict[int, dict[str, float]],
    slate_date: str,
    iterations: int = 5000,
) -> dict[str, Any]:
    seed_bytes = hashlib.sha256(f"{slate_date}|{game_key}|v15".encode()).digest()[:8]
    rng = np.random.default_rng(int.from_bytes(seed_bytes, "big"))

    by_team = {
        away: [p for p in players if str(p.get("team_name")) == away],
        home: [p for p in players if str(p.get("team_name")) == home],
    }
    results: dict[str, Any] = {}
    for team, team_id in ((away, away_id), (home, home_id)):
        stats = team_stats.get(team_id, {})
        hitters = by_team.get(team, [])
        model_hr = sum(_player_probability(player) for player in hitters[:10])
        baseline_hr = _num(stats.get("hr_pg"), 1.1)
        projected_hr = max(0.25, baseline_hr * 0.48 + model_hr * 0.72)
        run_factor, hr_factor = _opposing_pitcher_adjustment(hitters)
        projected_hr *= hr_factor
        # Project runs first because the hit model uses the simulated run environment.
        projected_runs = max(
            1.8,
            _num(stats.get("runs_pg"), 4.4) * 0.68 * run_factor + projected_hr * 1.18,
        )

        # Blend actual team hits/game with projected runs.
        # The public UI displays this as a per-team estimate, not a combined total.
        actual_hits_pg = _num(stats.get("hits_pg"), 8.2)
        run_implied_hits = 5.15 + projected_runs * 0.58
        projected_hits = max(
            5.2,
            min(
                10.8,
                actual_hits_pg * 0.72
                + run_implied_hits * 0.28
                + (run_factor - 1.0) * 0.65,
            ),
        )
        projected_so = max(4.0, _num(stats.get("so_pg"), 8.5))
        projected_sb = max(0.05, _num(stats.get("sb_pg"), 0.7))

        runs = _poisson_nonnegative(rng, projected_runs, iterations)
        hits = np.maximum(runs, _poisson_nonnegative(rng, projected_hits, iterations))
        hrs = np.minimum(hits, _poisson_nonnegative(rng, projected_hr, iterations))
        strikeouts = _poisson_nonnegative(rng, projected_so, iterations)
        steals = _poisson_nonnegative(rng, projected_sb, iterations)
        results[team] = {
            "runs_array": runs,
            "hits_array": hits,
            "hr_array": hrs,
            "so_array": strikeouts,
            "sb_array": steals,
            "projected_runs": float(np.mean(runs)),
            "projected_hits": float(np.mean(hits)),
            "projected_hr": float(np.mean(hrs)),
            "projected_so": float(np.mean(strikeouts)),
            "projected_sb": float(np.mean(steals)),
            "source": stats.get("source", "model baseline"),
        }

    away_runs = results[away]["runs_array"]
    home_runs = results[home]["runs_array"]
    ties = away_runs == home_runs
    home_win = np.mean((home_runs > away_runs) | (ties & (rng.random(iterations) > 0.5)))
    away_win = 1 - home_win
    results[away]["win_probability"] = float(away_win)
    results[home]["win_probability"] = float(home_win)

    for team in (away, home):
        for key in list(results[team]):
            if key.endswith("_array"):
                del results[team][key]

    return {
        "game_key": game_key,
        "away": away,
        "home": home,
        "away_id": away_id,
        "home_id": home_id,
        "iterations": iterations,
        "teams": results,
        "projected_score": f"{away} {results[away]['projected_runs']:.1f} – {home} {results[home]['projected_runs']:.1f}",
    }


def _build_game_sims_uncached(board: dict[str, Any], iterations: int = 5000) -> list[dict[str, Any]]:
    rankings = board.get("rankings", []) or []
    meta_map = {str(meta.get("game_id")): meta for meta in board.get("games_meta", []) or []}
    by_game: dict[str, list[dict[str, Any]]] = {}
    for player in rankings:
        by_game.setdefault(str(player.get("game_id") or ""), []).append(player)

    team_ids: set[int] = set()
    games: list[tuple[str, str, str, int, int, list[dict[str, Any]], dict[str, Any]]] = []
    for key, players in by_game.items():
        meta = meta_map.get(key, {})
        away = str(meta.get("away_team_name") or "")
        home = str(meta.get("home_team_name") or "")
        if not away or not home:
            teams = list(dict.fromkeys(str(p.get("team_name") or "") for p in players if p.get("team_name")))
            if len(teams) < 2:
                continue
            away, home = teams[:2]
        away_id = int(next((p.get("team_id") for p in players if str(p.get("team_name")) == away and p.get("team_id")), 0) or 0)
        home_id = int(next((p.get("team_id") for p in players if str(p.get("team_name")) == home and p.get("team_id")), 0) or 0)
        if not away_id or not home_id:
            continue
        team_ids.update({away_id, home_id})
        games.append((key, away, home, away_id, home_id, players, meta))

    season = int(str(board.get("date") or "2026")[:4])
    stats = fetch_team_stats(tuple(sorted(team_ids)), season)
    sims = []
    for key, away, home, away_id, home_id, players, meta in games:
        sim = simulate_game(key, away, home, away_id, home_id, players, stats, str(board.get("date")), iterations)
        for field in ("sportsbook_total", "over_odds", "under_odds", "total_book", "venue_name", "game_time"):
            if meta.get(field) is not None:
                sim[field] = meta.get(field)
        sims.append(sim)
    sims.sort(
        key=lambda sim: sim["teams"][sim["away"]]["projected_hr"] + sim["teams"][sim["home"]]["projected_hr"],
        reverse=True,
    )
    return sims


@st.cache_data(ttl=3600, show_spinner=False)
def _build_game_sims_cached(board_date: str, games_meta_json: str, rankings_json: str, iterations: int) -> list[dict[str, Any]]:
    import json
    board = {
        "date": board_date,
        "games_meta": json.loads(games_meta_json),
        "rankings": json.loads(rankings_json),
    }
    return _build_game_sims_uncached(board, iterations)


def build_game_sims(board: dict[str, Any], iterations: int = 5000) -> list[dict[str, Any]]:
    """Cache simulations by the compact input fields the engine uses."""
    import json
    rankings = []
    for player in board.get("rankings", []) or []:
        rankings.append({
            key: player.get(key) for key in (
                "game_id", "team_name", "team_id", "probability",
                "pitching_data_available", "pitcher_era", "pitcher_hr9",
            )
        })
    metas = []
    for meta in board.get("games_meta", []) or []:
        metas.append({
            key: meta.get(key) for key in (
                "game_id", "away_team_name", "home_team_name",
                "away_team_id", "home_team_id", "venue_name", "game_time",
            )
        })
    return _build_game_sims_cached(
        str(board.get("date") or ""),
        json.dumps(metas, sort_keys=True, default=str),
        json.dumps(rankings, sort_keys=True, default=str),
        int(iterations),
    )
