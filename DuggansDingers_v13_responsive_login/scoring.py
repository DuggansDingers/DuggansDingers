def percentile_scores(values):
    """
    Converts a list of numbers into scores from 0 to 100.

    The best value receives a score near 100.
    The lowest value receives a score near 0.
    """

    if not values:
        return []

    indexed_values = list(enumerate(values))

    sorted_values = sorted(
        indexed_values,
        key=lambda item: item[1],
    )

    scores = [0.0] * len(values)
    total = len(values)

    if total == 1:
        return [100.0]

    for position, item in enumerate(sorted_values):
        original_index = item[0]

        score = position / (total - 1) * 100
        scores[original_index] = score

    return scores


def add_dinger_scores(rankings):
    ballpark_values = [
        player.get("probability") or 0
        for player in rankings
    ]

    season_values = [
        player.get("season_hr_rate") or 0
        for player in rankings
    ]

    recent_values = [
        player.get("recent_hr_rate") or 0
        for player in rankings
    ]

    ballpark_scores = percentile_scores(ballpark_values)
    season_scores = percentile_scores(season_values)
    recent_scores = percentile_scores(recent_values)

    scored_players = []

    for index, player in enumerate(rankings):
        ballpark_score = ballpark_scores[index]
        season_score = season_scores[index]
        recent_score = recent_scores[index]

        dinger_score = (
            ballpark_score * 0.50
            + season_score * 0.30
            + recent_score * 0.20
        )

        scored_player = {
            **player,
            "ballpark_score": round(ballpark_score, 1),
            "season_power_score": round(season_score, 1),
            "recent_power_score": round(recent_score, 1),
            "dinger_score": round(dinger_score, 1),
        }

        scored_players.append(scored_player)

    scored_players.sort(
        key=lambda player: player["dinger_score"],
        reverse=True,
    )

    return scored_players