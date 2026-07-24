# DuggansDingers V21

## Dashboard
- Fixed the projected-starter footer overlap on featured cards.
- Replaced Last 15 with Last 10.
- Last 7 and Last 10 now render actual game-by-game home-run results.
- A full-height bar means one HR; a bright magenta bar with a number means a multi-HR game; a short blue bar means zero HR.

## Player Rankings
- Increased full-board font sizes and row height.
- Replaced Last 15 with actual Last 10 game-by-game home-run form.
- Kept actual Last 7 game form and player-profile links.

## Team Sheets
- Brightened the six individual Dinger Scores.
- Enlarged matchup selector cards and text.
- Rebuilt Last 7 and Last 15 form layouts so the 15-game strip no longer compresses together.
- Replaced the large explanation block with a compact asterisk footnote.

## Ballpark Weather
- Added a unique, high-resolution illustrated stadium scene for every MLB park/team.
- Removed repeated generic Guaranteed Rate Field artwork.
- Brightened all images and reduced the dark overlay.
- Removed the unwanted descriptive caption under the page title.
- Enlarged weather cards, temperatures, wind details, grades, and zone impacts.

## Game Sims
- Removed unreliable sportsbook total/over-under displays.
- Replaced average total runs with average projected hits.
- AI Game Read now changes by matchup using projected runs, hits, home runs, strikeouts, stolen bases, win probability, and game closeness.
- Enlarged simulation-board and narrative text.
- Cached simulation results for faster repeat visits.

## Loading Speed
- Added disk snapshots for the base model, weather, and odds.
- Reuses successful Statcast snapshots instead of downloading pybaseball leaderboards for each new slate date.
- Increased weather-request concurrency.
- Cached game simulations for one hour.
