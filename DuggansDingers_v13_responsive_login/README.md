# DuggansDingers v8 — Power Board Edition

A premium Streamlit home-run research dashboard built around Ballpark Pal projections and MLB Stats history.

## New in v8

- Screenshot-inspired dark sportsbook dashboard
- Six feature cards with real season, last-7, last-15, and last-30 history
- Full player card rankings with search, team, score, and risk filters
- Daily top-five home-run cheat sheet for every team
- Random home-run parlay generator with:
  - **Balanced** — stronger grades and moderate prices
  - **Longshot** — larger fair odds with model support
  - **Pipedream** — highest-payout, lowest-probability chaos builds
- Parlay filters for leg count, teams, minimum score, unique teams, unique games, and locked players
- Estimated fair payout for any stake
- Player profiles with rolling windows, game-by-game HR pulse, score breakdown, and MLB year-by-year history
- CSV exports for rankings, team cheat sheets, and generated tickets
- Date selector for any available slate
- Honest source-status indicators: unconnected data is never presented as live

## Setup

1. Copy `.env.example` to `.env`.
2. Add your Ballpark Pal key:

```env
BALLPARKPAL_API_KEY=your_key_here
```

3. Install packages:

```powershell
C:\venvs\DuggansDingers_v4\Scripts\python.exe -m pip install -r requirements.txt
```

4. Run:

```powershell
C:\venvs\DuggansDingers_v4\Scripts\python.exe -m streamlit run app.py
```

## Stadium backgrounds

Add team stadium images to:

```text
assets/stadiums/NYY.jpg
assets/stadiums/BOS.jpg
assets/stadiums/LAD.jpg
```

The player profile automatically uses the matching team image.

## Data notes

- Ballpark Pal supplies the current home-run probability and fair-odds projection.
- MLB Stats supplies season statistics and game logs used for last-7, last-15, and last-30 history.
- Multi-season history is fetched only when a player profile is opened.
- Parlay payouts are based on model fair odds and are not live sportsbook quotes.
- Combined parlay hit rates assume independent outcomes and are estimates, not guarantees.


## v10 Weather Connection

- Live game-time weather from Open-Meteo (no API key required)
- 30 MLB stadium coordinate/timezone map in `data/stadiums.json`
- Temperature, humidity, precipitation risk, wind speed/gust/direction
- Wind converted to out/in/cross using the stadium center-field bearing
- Weather grades and explainable impact scores
- Retractable roofs marked unconfirmed and treated as outdoor scenarios until confirmed
- Weather cached locally for 35 minutes in `data/cache/weather_cache.json`

Weather is displayed separately and does **not** change the Dinger Score yet. This lets you validate the feed before weighting it in the model.

## v11 Sportsbook Odds Connection

- New **Sportsbook Odds** page in the sidebar
- Upload a CSV containing DraftKings, FanDuel, BetMGM, or other HR prices
- Multiple books per player are supported; the app automatically selects the best payout
- Matching priority: MLB `player_id`, then normalized player name + team + game
- Calculates sportsbook implied probability, model edge, expected value per $10, and ROI
- Rankings and player profiles show best book, best odds, edge, and EV
- Parlay Lab uses sportsbook prices when connected and falls back to model fair odds only for missing legs
- Downloadable CSV template and matched-edge export included

Required CSV columns:

```csv
date,player_id,player_name,team,book,american_odds,game_id
2026-07-22,592450,Aaron Judge,NYY,DraftKings,+240,
```

`player_id` and `game_id` are optional, but MLB player ID is strongly recommended for reliable matching.

## Automatic Odds-API.io connection

Add these lines to `.env`:

```env
ODDS_API_IO_KEY=your_new_private_key
ODDS_API_IO_BASE_URL=https://api.odds-api.io/v3
```

Open **Sportsbook Odds** and click **Refresh Live Odds**. The app automatically finds MLB events (`usa-mlb`), requests each event's odds, extracts home-run props, and matches them to the Dinger Board. Manual CSV import remains available as a fallback.


## v12.5 updates
- Live odds load automatically on initial site load and refresh from cache every 5 minutes.
- Manual Refresh Live Odds remains available as a backup.
- Cleaner typography, stronger section separation, and smaller dashboard player headshots.

## v12.6 additions
- Brighter broadcast-style background, larger typography, and a redesigned professional sidebar.
- Smaller dashboard headshots so the model data stays prominent.
- Automatic probable opposing pitchers from MLB Stats.
- Pitcher season ERA, WHIP, HR/9, innings, and home runs allowed.
- Optional Statcast hitter and pitcher contact-quality data through `pybaseball` (barrel rate, hard-hit rate, average/max exit velocity).
- Statcast and pitcher-matchup components are included in the Dinger Score when available.
- Main board cache is set to two hours; the manual refresh button still forces an immediate update.

After extracting, run `python -m pip install -r requirements.txt` once so the optional Statcast dependency is installed.
