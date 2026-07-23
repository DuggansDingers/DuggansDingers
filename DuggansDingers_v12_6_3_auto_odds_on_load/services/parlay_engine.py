from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class ParlayProfile:
    name: str
    description: str
    min_score: float
    max_probability: float | None
    min_american_odds: float | None
    pool_limit: int
    score_weight: float
    payout_weight: float
    randomness: float


PROFILES: dict[str, ParlayProfile] = {
    "Balanced": ParlayProfile(
        name="Balanced",
        description="Stronger model grades with a reasonable payout ceiling.",
        min_score=72,
        max_probability=None,
        min_american_odds=None,
        pool_limit=28,
        score_weight=0.72,
        payout_weight=0.28,
        randomness=0.28,
    ),
    "Longshot": ParlayProfile(
        name="Longshot",
        description="Bigger prices with enough model support to stay interesting.",
        min_score=55,
        max_probability=0.28,
        min_american_odds=250,
        pool_limit=55,
        score_weight=0.45,
        payout_weight=0.55,
        randomness=0.55,
    ),
    "Pipedream": ParlayProfile(
        name="Pipedream",
        description="The highest-payout, lowest-probability chaos build on the board.",
        min_score=20,
        max_probability=0.20,
        min_american_odds=400,
        pool_limit=90,
        score_weight=0.16,
        payout_weight=0.84,
        randomness=0.85,
    ),
}


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def probability_fraction(value: Any) -> float:
    value = safe_float(value)
    if value > 1:
        value /= 100
    return max(0.0, min(1.0, value))


def american_to_decimal(value: Any) -> float:
    odds = safe_float(value)
    if odds > 0:
        return 1 + odds / 100
    if odds < 0:
        return 1 + 100 / abs(odds)
    return 1.0


def decimal_to_american(decimal_odds: float) -> float:
    if decimal_odds <= 1:
        return 0.0
    if decimal_odds >= 2:
        return (decimal_odds - 1) * 100
    return -100 / (decimal_odds - 1)


def player_price(player: dict[str, Any]) -> Any:
    return player.get("best_odds") if player.get("best_odds") is not None else player.get("fair_odds")


def combined_decimal_odds(players: Iterable[dict[str, Any]]) -> float:
    decimals = [american_to_decimal(player_price(player)) for player in players]
    return math.prod(decimals) if decimals else 1.0


def combined_model_probability(players: Iterable[dict[str, Any]]) -> float:
    probabilities = [probability_fraction(player.get("probability")) for player in players]
    return math.prod(probabilities) if probabilities else 0.0


def potential_return(decimal_odds: float, stake: float) -> tuple[float, float]:
    total_return = stake * decimal_odds
    return round(total_return - stake, 2), round(total_return, 2)


def _candidate_score(player: dict[str, Any], profile: ParlayProfile) -> float:
    score = safe_float(player.get("dinger_score")) / 100
    american = max(0.0, safe_float(player_price(player)))
    payout_signal = min(1.0, american / 900)
    probability = probability_fraction(player.get("probability"))
    # Pipedreams should reward price and lower probability; balanced builds should not.
    low_probability_bonus = (1 - probability) if profile.name == "Pipedream" else 0.0
    base = score * profile.score_weight + payout_signal * profile.payout_weight
    return max(0.001, base + low_probability_bonus * (0.20 if profile.name == "Pipedream" else 0.0))


def filter_candidates(
    rankings: list[dict[str, Any]],
    profile_name: str,
    min_score_override: float | None = None,
    selected_teams: set[str] | None = None,
) -> list[dict[str, Any]]:
    profile = PROFILES.get(profile_name, PROFILES["Balanced"])
    min_score = profile.min_score if min_score_override is None else min_score_override
    selected_teams = selected_teams or set()

    candidates: list[dict[str, Any]] = []
    for player in rankings:
        score = safe_float(player.get("dinger_score"))
        probability = probability_fraction(player.get("probability"))
        american = safe_float(player_price(player))
        team = str(player.get("team_name") or "")
        if score < min_score:
            continue
        if selected_teams and team not in selected_teams:
            continue
        if profile.max_probability is not None and probability > profile.max_probability:
            continue
        if profile.min_american_odds is not None and american < profile.min_american_odds:
            continue
        candidates.append(player)

    # Graceful fallback: never leave the generator dead because one feed uses a narrower odds range.
    if len(candidates) < 2:
        candidates = [
            player for player in rankings
            if safe_float(player.get("dinger_score")) >= min_score
            and (not selected_teams or str(player.get("team_name") or "") in selected_teams)
        ]

    candidates.sort(
        key=lambda player: _candidate_score(player, profile),
        reverse=True,
    )
    return candidates[: profile.pool_limit]


def generate_parlay(
    rankings: list[dict[str, Any]],
    profile_name: str,
    legs: int,
    *,
    min_score_override: float | None = None,
    selected_teams: set[str] | None = None,
    unique_teams: bool = True,
    unique_games: bool = True,
    locked_player_ids: set[int] | None = None,
    seed: int | None = None,
) -> list[dict[str, Any]]:
    profile = PROFILES.get(profile_name, PROFILES["Balanced"])
    rng = random.Random(seed)
    locked_player_ids = locked_player_ids or set()
    candidates = filter_candidates(rankings, profile_name, min_score_override, selected_teams)

    locked = [player for player in rankings if int(player.get("player_id") or -1) in locked_player_ids]
    picks: list[dict[str, Any]] = locked[:legs]
    used_teams = {str(player.get("team_name")) for player in picks}
    used_games = {str(player.get("game_id")) for player in picks}
    used_ids = {int(player.get("player_id") or -1) for player in picks}

    pool = [player for player in candidates if int(player.get("player_id") or -1) not in used_ids]
    while len(picks) < legs and pool:
        eligible = [
            player for player in pool
            if (not unique_teams or str(player.get("team_name")) not in used_teams)
            and (not unique_games or str(player.get("game_id")) not in used_games)
        ]
        if not eligible:
            # Relax game uniqueness first, then team uniqueness, rather than failing.
            eligible = [
                player for player in pool
                if (not unique_teams or str(player.get("team_name")) not in used_teams)
            ]
        if not eligible:
            eligible = pool[:]

        weights: list[float] = []
        for player in eligible:
            base = _candidate_score(player, profile)
            noise = rng.random() * profile.randomness
            weights.append(max(0.001, base * (1 + noise)))
        chosen = rng.choices(eligible, weights=weights, k=1)[0]
        picks.append(chosen)
        pool.remove(chosen)
        used_teams.add(str(chosen.get("team_name")))
        used_games.add(str(chosen.get("game_id")))

    return picks
