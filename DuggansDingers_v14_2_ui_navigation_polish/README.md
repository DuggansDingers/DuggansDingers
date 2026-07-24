# Duggan's Dingers v15 — Neon Intelligence Rebuild

A responsive MLB home-run intelligence dashboard built with Streamlit.

## Major v15 upgrades

- Multi-provider weather: WeatherAPI.com, Visual Crossing, then the U.S. National Weather Service fallback
- Short weather cache, failure backoff, and stale-success fallback
- Probable pitchers matched from the MLB schedule and included in hitter scoring
- Absolute-aware Dinger Score so a weak-slate percentile cannot masquerade as an elite projection
- Simple model reasons on every top-six home-run pick
- Matchup-first Team Sheets with both clubs, projected pitchers, neon status bars, and selectable game tabs
- Game Sims with projected scores, hits, home runs, strikeouts, stolen bases, and win probability
- Parlay Lab player locks, reroll-unlocked behavior, and mixed anchor/long-price builds
- DraftKings and FanDuel side-by-side sportsbook prices
- Custom neon charts and tables; no native white dataframe surfaces
- Concurrent MLB player-stat retrieval for faster cold loads

## Weather provider order

1. `WEATHERAPI_KEY` when configured — recommended for every MLB park, including Toronto.
2. `VISUAL_CROSSING_API_KEY` when configured — optional secondary keyed provider.
3. `api.weather.gov` — free fallback for U.S. stadiums; no key required.

Fixed-roof parks are treated as climate controlled and do not make a weather request.

## Run locally

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Copy `.env.example` to `.env` and insert your real credentials. Never upload `.env` to GitHub.

## Model note

Game Sims and Dinger Scores are analytical estimates, not guarantees or sportsbook lines.
