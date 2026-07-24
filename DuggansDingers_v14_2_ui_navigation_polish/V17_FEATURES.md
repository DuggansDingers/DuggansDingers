# DuggansDingers V17 — Finished Template Rebuild

## Visual rebuild
- Template-style permanent sidebar with glowing SVG navigation.
- Duplicate Streamlit page list removed by moving renderers out of the reserved `pages/` directory.
- Homepage rebuilt around the approved template: centered wordmark, six player-photo feature cards, Top 25 board, probable pitchers, and neon slate summary.
- All dropdowns, menus, popovers, text inputs, and filters use a dark neon skin with bold white text.
- Brighter navy site background and higher-contrast typography.

## Weather
- MLB Stats schedule is now the authoritative source for home club, venue, game time, and team IDs.
- Empty Ballpark Pal venue fields are repaired before stadium lookup.
- All 30 MLB home parks are mapped in `data/stadiums.json`.
- Three ballpark cards per row.
- Cards use real aerial imagery centered on the matched stadium location.
- Every game opens a dedicated weather detail screen with LF/CF/RF carry, forecast metrics, and a weather-adjusted hitter board.
- WeatherAPI, Visual Crossing, and National Weather Service fallback remain supported.

## Probable pitchers
- Player-to-game matching no longer depends only on the Ballpark Pal game ID.
- MLB team IDs and team pairs are used to match the schedule and opposing starter.
- Pitcher hand, ERA, and HR/9 appear on the homepage, rankings, profiles, and team sheets when announced.

## Rankings and profiles
- Five compact ranking cards per row on desktop.
- Full probable-pitcher board below the cards.
- Player profile dropdown replaced with searchable, clickable player tiles.

## Team sheets
- Both teams remain side by side.
- Recent form uses distinct symbols/colors for no HR, one HR, multi-HR, and no-data/DNP.
- Player rows are clickable and open Player Intelligence.

## Game Sims
- Removed the white game dropdown.
- Full-slate rows are clickable and open the selected simulation above.
- Added two-sentence AI-style simulation read.
- DraftKings total and over/under prices are parsed when the connected Odds-API response includes game-total markets.

## Loading speed
- Ballpark Pal game calls increased to 12 concurrent workers.
- MLB player enrichment increased to 20 concurrent workers.
- Probable-pitcher stat calls increased to 12 concurrent workers.
- Sportsbook event requests are fetched concurrently instead of sequentially.
