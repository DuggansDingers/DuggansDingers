from __future__ import annotations

from html import escape as esc
import math
import random
import secrets

import streamlit as st

from components.ui import headshot, odds, probability_fraction, safe_float, safe_int, team_logo
from views import secondary
from views.prop_center import _market_rows, MARKETS


def _american_from_probability(probability: float) -> int:
    probability = max(0.01, min(0.99, probability))
    if probability >= 0.5:
        return int(round(-100 * probability / (1 - probability)))
    return int(round(100 * (1 - probability) / probability))


def _mixed_pool(board: dict) -> list[dict]:
    pool: list[dict] = []
    for market in ("total-bases", "hits", "pitcher-ks", "stolen-bases"):
        for row in _market_rows(board, market)[:35]:
            if market == "pitcher-ks":
                name = str(row.get("pitcher_name") or "—")
                player_id = safe_int(row.get("pitcher_id"))
                image = headshot(player_id, 180) if player_id else team_logo(row.get("team_id"))
            else:
                name = str(row.get("player_name") or "—")
                player_id = safe_int(row.get("player_id"))
                image = headshot(player_id, 180)

            confidence = max(0.05, min(0.92, safe_float(row.get("prop_probability")) / 100))
            pool.append({
                "key": f"{market}:{player_id or name}",
                "market": market,
                "market_label": MARKETS[market]["label"],
                "accent": MARKETS[market]["accent"],
                "name": name,
                "player_id": player_id,
                "image": image,
                "team": str(row.get("team_name") or "—"),
                "line": safe_float(row.get("prop_line")),
                "projection": safe_float(row.get("prop_projection")),
                "score": safe_float(row.get("prop_score")),
                "confidence": confidence,
                "fair_odds": _american_from_probability(confidence),
                "reason": " • ".join((row.get("prop_reasons") or [])[:2]),
            })
    return pool


def _mixed_ticket_html(picks: list[dict], stake: float) -> str:
    combined_probability = math.prod(p["confidence"] for p in picks)
    decimal = 1 / max(0.0001, combined_probability)
    american = int(round((decimal - 1) * 100)) if decimal >= 2 else int(round(-100 / max(0.01, decimal - 1)))
    profit = stake * (decimal - 1)

    legs = []
    for index, pick in enumerate(picks, 1):
        legs.append(
            f'<article class="dd30-kitchen-leg" style="--flavor:{pick["accent"]}">'
            f'<span class="number">{index}</span><img src="{pick["image"]}">'
            f'<div class="copy"><small>{esc(pick["market_label"])}</small><b>{esc(pick["name"])}</b>'
            f'<em>{esc(pick["team"])} • Over {pick["line"]:.1f}</em><p>{esc(pick["reason"])}</p></div>'
            f'<div class="metrics"><span><small>PROJ.</small><b>{pick["projection"]:.2f}</b></span>'
            f'<span><small>SCORE</small><b>{pick["score"]:.1f}</b></span>'
            f'<span><small>FAIR</small><b>{odds(pick["fair_odds"])}</b></span></div>'
            '</article>'
        )

    return (
        '<section class="dd30-kitchen-ticket"><header><div><span>CHEF\'S TICKET</span><b>MIXED PROP PARLAY</b></div>'
        f'<aside><span><small>LEGS</small><b>{len(picks)}</b></span>'
        f'<span><small>FAIR ODDS</small><b>{odds(american)}</b></span>'
        f'<span><small>MODEL HIT RATE</small><b>{combined_probability*100:.1f}%</b></span>'
        f'<span><small>${stake:.0f} PROFIT</small><b>${profit:,.2f}</b></span></aside></header>'
        + "".join(legs) + '</section>'
    )


def _mixed_parlay(board: dict) -> None:
    pool = _mixed_pool(board)
    if not pool:
        st.info("Mixed-prop ingredients are waiting for the slate data.")
        return

    st.session_state.setdefault("kitchen_mixed_keys", [])
    st.session_state.setdefault("kitchen_mixed_locks", [])

    c1, c2, c3, c4 = st.columns([1, 1, 1.25, 1.75])
    legs = c1.slider("Legs", 2, 8, 4, key="kitchen_mixed_legs")
    stake = c2.number_input("Stake ($)", 1.0, 10000.0, 10.0, 5.0, key="kitchen_mixed_stake")
    risk = c3.select_slider("Recipe", ["Safer", "Balanced", "Spicy"], value="Balanced")
    chosen_markets = c4.multiselect(
        "Markets",
        list(MARKETS),
        default=["total-bases", "hits", "pitcher-ks"],
        format_func=lambda slug: MARKETS[slug]["label"],
    )

    filtered = [row for row in pool if row["market"] in chosen_markets]
    if risk == "Safer":
        filtered = [row for row in filtered if row["score"] >= 72]
    elif risk == "Spicy":
        filtered = [row for row in filtered if row["score"] >= 55]

    key_map = {row["key"]: row for row in filtered}
    current_keys = [key for key in st.session_state.kitchen_mixed_keys if key in key_map]
    locks = set(st.session_state.kitchen_mixed_locks)

    b1, b2, b3 = st.columns([1.4, 1.2, 1])
    cook = b1.button("🔥 Cook New Mixed Parlay", type="primary", use_container_width=True)
    reroll = b2.button("↻ Reroll Unlocked Legs", use_container_width=True, disabled=not current_keys)
    clear = b3.button("Clear Board", use_container_width=True)

    if clear:
        st.session_state.kitchen_mixed_keys = []
        st.session_state.kitchen_mixed_locks = []
        st.rerun()

    if cook or reroll:
        locked_rows = [key_map[key] for key in current_keys if key in locks and key in key_map]
        blocked_names = {row["name"] for row in locked_rows}
        candidates = [row for row in filtered if row["name"] not in blocked_names]

        # Weighted random: stronger score is favored, but still creates varied tickets.
        selected = list(locked_rows)
        rng = random.Random(secrets.randbits(32))
        while len(selected) < legs and candidates:
            weights = [max(1.0, row["score"] - (45 if risk == "Spicy" else 52)) for row in candidates]
            choice = rng.choices(candidates, weights=weights, k=1)[0]
            selected.append(choice)
            candidates = [
                row for row in candidates
                if row["name"] != choice["name"]
                and not (row["market"] == choice["market"] and row["team"] == choice["team"])
            ]

        st.session_state.kitchen_mixed_keys = [row["key"] for row in selected[:legs]]
        st.session_state.kitchen_mixed_locks = [key for key in locks if key in st.session_state.kitchen_mixed_keys]
        st.rerun()

    picks = [key_map[key] for key in st.session_state.kitchen_mixed_keys if key in key_map]
    if not picks:
        st.markdown(
            '<div class="dd30-kitchen-empty"><b>THE BOARD IS COLD</b><span>Choose your markets and cook a mixed-prop parlay. Lock any legs you like, then reroll the rest.</span></div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(_mixed_ticket_html(picks, stake), unsafe_allow_html=True)

    st.markdown('<div class="dd30-lock-title"><b>LOCK YOUR FAVORITE LEGS</b><span>Locked ingredients survive the next reroll.</span></div>', unsafe_allow_html=True)
    columns = st.columns(min(4, len(picks)))
    new_locks: list[str] = []
    for index, pick in enumerate(picks):
        with columns[index % len(columns)]:
            checked = st.checkbox(
                f'{pick["name"]} — {pick["market_label"]}',
                value=pick["key"] in locks,
                key=f'kitchen_lock_{pick["key"]}',
            )
            if checked:
                new_locks.append(pick["key"])
    st.session_state.kitchen_mixed_locks = new_locks


def render(board: dict) -> None:
    st.markdown(
        '<section class="dd30-kitchen-hero"><div><span>PARLAY CREATION CENTER</span>'
        '<h1>THE <em>KITCHEN</em></h1><p>Cook up straight home-run parlays or combine total bases, hits, pitcher strikeouts, and stolen bases into one mixed-prop ticket.</p></div>'
        '<aside><div><span>RECIPES</span><b>HR + MIXED</b></div><div><span>LOCKS</span><b>ON</b></div><div><span>REROLL</span><b>UNLOCKED</b></div></aside></section>',
        unsafe_allow_html=True,
    )

    mode = st.radio(
        "Kitchen station",
        ["Home Run Parlays", "Mixed Prop Parlays"],
        horizontal=True,
        label_visibility="collapsed",
        key="kitchen_station",
    )
    st.markdown(
        '<div class="dd30-kitchen-tabs">'
        f'<div class={"active" if mode == "Home Run Parlays" else ""}><span>⚾</span><b>HOME RUN PARLAYS</b><em>Dinger Score recipes</em></div>'
        f'<div class={"active" if mode == "Mixed Prop Parlays" else ""}><span>◆</span><b>MIXED PROP PARLAYS</b><em>TB • Hits • K • SB</em></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    if mode == "Home Run Parlays":
        secondary.parlay(board)
    else:
        _mixed_parlay(board)
