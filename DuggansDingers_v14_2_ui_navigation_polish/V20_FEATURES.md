# DuggansDingers V20

## Player Rankings
- Replaced repeated `BEST BALLPARK` labels with data-driven labels:
  Top Pick, Highest HR Probability, Hottest Bat, Power Matchup, Best Weather,
  Best Value, Matchup Edge, Hot Form, Park Boost, and Value Upside.
- Rebuilt compact cards so the projected starter no longer overlaps HR probability.
- Added weather grade and HR impact to each player card.
- Player cards and table headshots open the complete player profile.
- Removed Player Profiles from the visible sidebar while preserving direct profile links.

## Probable Pitchers
- Corrected MLB schedule-field mapping for `home_probable_pitcher` and
  `away_probable_pitcher`.
- Corrected home/away team-name mapping.
- Added a one-request Ballpark Pal matchup fallback when MLB has not yet
  published a probable starter.
- Added projected-starter status text and pitcher ERA/HR9 when available.

## Team Sheets
- Increased type sizes throughout.
- Added a clear explanation of the recent-form graphs.
- Every form column now shows a number:
  0 = no HR, 1 = one HR, 2+ = multiple combined HR, — = no data.
- Added game-date labels and a full legend.
- Added weather impact and projected opposing starter to each team panel.

## Weather
- Replaced aerial-map imagery with local AI-illustrated stadium scene assets
  based on the approved mockup style.
- Added a consistent team-specific stadium scene for each MLB club.
- Kept three matchup cards per row and a clickable detailed weather view.
- Weather is now loaded and shared with Dashboard, Rankings, Team Sheets,
  Game Sims, Parlay Lab, and player detail pages.
- Added weather-adjusted probability and score fields to enriched player records.

## Game Sims and Parlay Lab
- Increased font sizes and contrast.
- Added weather impact to each generated parlay leg.
