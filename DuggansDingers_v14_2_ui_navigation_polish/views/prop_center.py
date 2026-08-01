from __future__ import annotations

from html import escape as esc
from statistics import mean
from urllib.parse import quote

import streamlit as st

from components.ui import headshot, odds, probability_fraction, safe_float, safe_int, team_logo


MARKETS = {
    "total-bases": {"label":"Total Bases","short":"TB","accent":"#ff4d8d","icon":"◆"},
    "hits": {"label":"Hits","short":"H","accent":"#35d5ff","icon":"●"},
    "pitcher-ks": {"label":"Pitcher Strikeouts","short":"K","accent":"#b55cff","icon":"K"},
    "stolen-bases": {"label":"Stolen Bases","short":"SB","accent":"#35f28f","icon":"↗"},
}


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def _percentile(values: list[float]) -> list[float]:
    if not values:
        return []
    ordered = sorted(set(values))
    if len(ordered) == 1:
        return [50.0 for _ in values]
    lookup = {value: index / (len(ordered)-1) * 100 for index, value in enumerate(ordered)}
    return [lookup[value] for value in values]


def _recent(player: dict, key: str, fallback: float = 0.0) -> float:
    value = safe_float(player.get(key))
    return value if value else fallback


def _hitter_rows(board: dict, market: str) -> list[dict]:
    players = list(board.get("rankings", []) or [])
    raw: list[dict] = []
    for player in players:
        games = max(1, safe_int(player.get("season_games")))
        pa = max(1, safe_int(player.get("season_plate_appearances")))
        season_avg = safe_float(player.get("season_avg"))
        season_slg = safe_float(player.get("season_slg"))
        last10_avg = safe_float(player.get("last_10_avg")) or season_avg
        barrel = safe_float(player.get("barrel_pct"))
        hard_hit = safe_float(player.get("hard_hit_pct"))
        weather = safe_float(player.get("weather_impact"))
        matchup = safe_float(player.get("pitcher_matchup_score"))
        hr_prob = probability_fraction(player.get("probability")) * 100

        if market == "total-bases":
            season_tb = (
                safe_int(player.get("season_hits"))
                + safe_int(player.get("season_doubles"))
                + safe_int(player.get("season_triples")) * 2
                + safe_int(player.get("season_home_runs")) * 3
            )
            recent_tb_pg = _recent(player, "last_10_total_bases") / max(1, safe_int(player.get("last_10_games")))
            season_tb_pg = season_tb / games
            projection = max(0.0, season_tb_pg * .52 + recent_tb_pg * .30 + hr_prob / 100 * 1.25 + weather * .025)
            raw_score = season_slg * 115 + recent_tb_pg * 17 + barrel * 1.25 + hard_hit * .25 + matchup * .12 + hr_prob * .33
            line = 1.5
            reasons = [
                f"{season_slg:.3f} season SLG",
                f"{recent_tb_pg:.2f} TB/game over last 10",
                f"{barrel:.1f}% barrel rate",
            ]
        elif market == "hits":
            recent_hits_pg = _recent(player, "last_10_hits") / max(1, safe_int(player.get("last_10_games")))
            season_hits_pg = safe_int(player.get("season_hits")) / games
            projection = max(0.0, season_hits_pg * .52 + recent_hits_pg * .34 + hard_hit / 100 * .18)
            raw_score = season_avg * 180 + last10_avg * 155 + hard_hit * .35 + barrel * .55 + matchup * .10
            line = 0.5
            reasons = [
                f"{season_avg:.3f} season AVG",
                f"{last10_avg:.3f} average over last 10",
                f"{hard_hit:.1f}% hard-hit rate",
            ]
        else:
            sb_pg = safe_int(player.get("season_stolen_bases")) / games
            recent_sb_pg = _recent(player, "last_10_stolen_bases") / max(1, safe_int(player.get("last_10_games")))
            on_base = safe_float(player.get("season_obp"))
            projection = max(0.0, sb_pg * .58 + recent_sb_pg * .32 + max(0.0, on_base-.300) * .45)
            raw_score = sb_pg * 320 + recent_sb_pg * 280 + on_base * 65 + season_avg * 45
            line = 0.5
            reasons = [
                f"{safe_int(player.get('season_stolen_bases'))} season stolen bases",
                f"{recent_sb_pg:.2f} SB/game over last 10",
                f"{on_base:.3f} OBP",
            ]

        raw.append({
            **player,
            "prop_projection": projection,
            "prop_raw_score": raw_score,
            "prop_line": line,
            "prop_reasons": reasons,
        })

    scores = _percentile([safe_float(row["prop_raw_score"]) for row in raw])
    for row, percentile in zip(raw, scores):
        absolute = _clamp(safe_float(row["prop_projection"]) / (2.5 if market=="total-bases" else 1.25 if market=="hits" else .35) * 100)
        row["prop_score"] = round(_clamp(absolute*.56 + percentile*.44), 1)
        row["prop_probability"] = round(_clamp(16 + row["prop_score"]*.72), 1)
    raw.sort(key=lambda row: safe_float(row["prop_score"]), reverse=True)
    return raw


def _pitcher_rows(board: dict) -> list[dict]:
    grouped: dict[str, dict] = {}
    for player in board.get("rankings", []) or []:
        name = str(player.get("opposing_pitcher") or "")
        if not name or name.lower() in {"not announced","awaiting announcement","projected starter"}:
            continue
        key = f"{name}|{player.get('game_id')}"
        row = grouped.setdefault(key, {
            "pitcher_name": name,
            "pitcher_id": player.get("opposing_pitcher_id"),
            "team_id": player.get("opponent_team_id") or player.get("opposing_team_id"),
            "team_name": player.get("opponent_team_name") or player.get("opposing_team") or "—",
            "game_id": player.get("game_id"),
            "hand": player.get("opposing_pitcher_hand") or "—",
            "k9": safe_float(player.get("pitcher_strikeouts_per9")),
            "era": safe_float(player.get("pitcher_era")),
            "whip": safe_float(player.get("pitcher_whip")),
            "opponent_ks": [],
            "best_odds": None,
            "best_book": "",
        })
        row["opponent_ks"].append(
            safe_int(player.get("season_strikeouts")) / max(1, safe_int(player.get("season_plate_appearances"))) * 100
        )

    rows = list(grouped.values())
    raw_values = []
    for row in rows:
        opponent_k_rate = mean(row["opponent_ks"]) if row["opponent_ks"] else 22.0
        projected_innings = 5.65
        projection = safe_float(row["k9"]) / 9 * projected_innings * (opponent_k_rate / 22.0)
        raw_score = safe_float(row["k9"]) * 7.0 + opponent_k_rate * 1.3 - safe_float(row["whip"]) * 5
        row.update({
            "opponent_k_rate": opponent_k_rate,
            "prop_projection": projection,
            "prop_raw_score": raw_score,
            "prop_line": max(3.5, round(projection*2)/2),
            "prop_reasons": [
                f"{safe_float(row['k9']):.1f} K/9",
                f"{opponent_k_rate:.1f}% opponent strikeout rate",
                f"{safe_float(row['era']):.2f} ERA",
            ],
        })
        raw_values.append(raw_score)

    percentiles = _percentile(raw_values)
    for row, percentile in zip(rows, percentiles):
        absolute = _clamp(safe_float(row["prop_projection"]) / 8.0 * 100)
        row["prop_score"] = round(_clamp(absolute*.60 + percentile*.40),1)
        row["prop_probability"] = round(_clamp(18 + row["prop_score"]*.69),1)
    rows.sort(key=lambda row: safe_float(row["prop_score"]), reverse=True)
    return rows


def _pitcher_image(row: dict, size: int = 240) -> str:
    pitcher_id = safe_int(row.get("pitcher_id"))
    if pitcher_id > 0:
        return headshot(pitcher_id, size)
    team_id = safe_int(row.get("team_id"))
    if team_id > 0:
        return team_logo(team_id)
    return ""


def _market_rows(board: dict, market: str) -> list[dict]:
    return _pitcher_rows(board) if market == "pitcher-ks" else _hitter_rows(board, market)


def _market_nav(active: str) -> str:
    links = []
    for slug, meta in MARKETS.items():
        cls = " active" if slug == active else ""
        links.append(
            f'<a class="dd28-market-tab{cls}" style="--market:{meta["accent"]}" href="?view=props&market={slug}" target="_self">'
            f'<i>{meta["icon"]}</i><span>{meta["label"]}</span></a>'
        )
    return '<nav class="dd28-market-nav">'+"".join(links)+'</nav>'


def _top_cards(rows: list[dict], market: str) -> str:
    meta = MARKETS[market]
    cards = []
    for rank, row in enumerate(rows[:5],1):
        if market == "pitcher-ks":
            image = _pitcher_image(row, 280)
            name = str(row.get("pitcher_name") or "—")
            subtitle = f'{row.get("hand")}HP • {safe_float(row.get("k9")):.1f} K/9'
        else:
            image = headshot(row.get("player_id"), 240)
            name = str(row.get("player_name") or "—")
            subtitle = f'{row.get("team_name") or "—"} • {row.get("position") or "—"}'
        cards.append(
            f'<article class="dd28-prop-card" style="--market:{meta["accent"]}">'
            f'<span class="rank">{rank}</span><small>{meta["label"].upper()}</small>'
            f'<img src="{image}" alt="{esc(name)}"><h3>{esc(name)}</h3><p>{esc(subtitle)}</p>'
            f'<div class="numbers"><strong>{safe_float(row.get("prop_score")):.1f}<em>PROP SCORE</em></strong>'
            f'<strong>{safe_float(row.get("prop_projection")):.2f}<em>PROJECTED {meta["short"]}</em></strong></div>'
            f'<div class="confidence"><i><em style="width:{safe_float(row.get("prop_score")):.1f}%"></em></i><span>{safe_float(row.get("prop_probability")):.0f}% model confidence</span></div>'
            + (
                f'<div class="pitcher-rail"><span><small>ERA</small><b>{safe_float(row.get("era")):.2f}</b></span>'
                f'<span><small>WHIP</small><b>{safe_float(row.get("whip")):.2f}</b></span>'
                f'<span><small>OPP K%</small><b>{safe_float(row.get("opponent_k_rate")):.1f}%</b></span></div>'
                if market == "pitcher-ks" else ""
              )
            + f'<footer><b>LINE {safe_float(row.get("prop_line")):.1f}</b><span>{esc(row.get("prop_reasons",[""])[0])}</span></footer>'
            '</article>'
        )
    return '<div class="dd28-prop-card-row">'+"".join(cards)+'</div>'


def _board(rows: list[dict], market: str) -> str:
    meta = MARKETS[market]
    body = []
    for rank,row in enumerate(rows[:30],1):
        if market == "pitcher-ks":
            image = _pitcher_image(row, 200)
            name = str(row.get("pitcher_name") or "—")
            subtitle = f'{row.get("hand")}HP • {safe_float(row.get("era")):.2f} ERA'
        else:
            image = headshot(row.get("player_id"), 160)
            name = str(row.get("player_name") or "—")
            subtitle = f'{row.get("team_name") or "—"} • {row.get("position") or "—"}'
        reasons = row.get("prop_reasons") or []
        body.append(
            f'<div class="dd28-prop-row">'
            f'<span class="rank">{rank}</span><span class="player"><img src="{image}"><span><b>{esc(name)}</b><small>{esc(subtitle)}</small></span></span>'
            f'<span class="score"><b>{safe_float(row.get("prop_score")):.1f}</b><i><em style="width:{safe_float(row.get("prop_score")):.1f}%"></em></i></span>'
            f'<span><small>PROJECTION</small><b>{safe_float(row.get("prop_projection")):.2f}</b></span>'
            f'<span><small>LINE</small><b>{safe_float(row.get("prop_line")):.1f}</b></span>'
            f'<span><small>CONFIDENCE</small><b>{safe_float(row.get("prop_probability")):.0f}%</b></span>'
            f'<span class="reason"><small>MODEL READ</small><b>{esc(" • ".join(reasons[:2]))}</b></span>'
            f'<span class="price"><small>BEST PRICE</small><b>{odds(row.get("best_odds"))}</b><em>{esc(str(row.get("best_book") or "Model"))}</em></span>'
            '</div>'
        )
    return (
        f'<section class="dd28-prop-board" style="--market:{meta["accent"]}"><header><div><span>FULL SLATE</span><b>{meta["label"].upper()} RANKINGS</b></div>'
        f'<em>{len(rows)} qualified projections</em></header>'
        '<div class="dd28-prop-head"><span>#</span><span>PLAYER</span><span>PROP SCORE</span><span>PROJ.</span><span>LINE</span><span>CONF.</span><span>MODEL READ</span><span>PRICE</span></div>'
        + "".join(body) + '</section>'
    )


def render(board: dict, forced_market: str | None = None) -> None:
    requested = forced_market or str(st.query_params.get("market") or "total-bases")
    market = requested if requested in MARKETS else "total-bases"
    meta = MARKETS[market]
    rows = _market_rows(board, market)

    st.markdown(
        f'<section class="dd28-prop-hero" style="--market:{meta["accent"]}"><div><span>MULTI-MARKET PLAYER INTELLIGENCE</span>'
        f'<h1>PROP <em>COMMAND</em></h1><p>Model-driven rankings for total bases, hits, pitcher strikeouts, and stolen bases using the same projection, MLB, Statcast, matchup, weather, and sportsbook data powering DuggansDingers.</p></div>'
        f'<aside><div><span>MARKET</span><b>{meta["label"]}</b></div><div><span>PROJECTIONS</span><b>{len(rows)}</b></div><div><span>SLATE</span><b>{esc(str(board.get("date") or "Today"))}</b></div></aside></section>',
        unsafe_allow_html=True,
    )
    st.markdown(_market_nav(market),unsafe_allow_html=True)
    if not rows:
        st.info("No qualified projections are available for this market yet.")
        return
    st.markdown(_top_cards(rows,market),unsafe_allow_html=True)
    st.markdown(_board(rows,market),unsafe_allow_html=True)
    st.caption("Prop Scores are model-generated comparison scores, not guarantees. Sportsbook lines and prices appear only when matched live data is available.")
