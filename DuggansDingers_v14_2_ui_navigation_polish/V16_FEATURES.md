# DuggansDingers V16 — Template Home + Sidebar Rebuild

## Homepage
- Mirrors the supplied high-energy template structure.
- Keeps player headshots in the six top-pick cards instead of placing the logo behind each pick.
- Adds two plain-English reasons and the probable-pitcher matchup to every top pick.
- Adds a professional Top 25 neon intelligence table with probable pitchers.

## Navigation and appearance
- Moves navigation into a permanent desktop sidebar.
- SVG icons, labels, and descriptions glow on hover.
- Brightens the global navy background and removes low-contrast gray copy.
- Restyles select boxes, date inputs, menus, sliders, and popovers with dark neon surfaces.

## Weather
- Reads WEATHERAPI_KEY dynamically and also accepts WEATHER_API_KEY.
- Repairs home-team and stadium matching from MLB team IDs and MLB schedule metadata.
- Displays three field diagrams per row.
- Each game opens a full weather detail screen with field-direction carry and affected hitters.

## Probable pitchers
- Matches games by MLB team IDs before abbreviations.
- Repairs missing home/away abbreviations and venue data from the MLB schedule.
- Shows the opposing probable pitcher, handedness, HR/9, and ERA on ranking cards and tables.

## Team sheets
- Away and home clubs display side by side.
- Larger, brighter hitter text.
- Compact neon bars for Dinger Score, HR probability, Last 7, and Last 15.
- Highest projected home-run game opens first.

## Speed
- Only loads weather on Weather and Player Intelligence pages.
- Only loads sportsbook prices on pages that display them.
- Ballpark Pal game projection calls run concurrently.
- Reuses a recent MLB stats snapshot for up to two days on a cold deployment.
- Sidebar renders before the data pipeline finishes.

## Game Sims
- Adds a two-sentence AI-style game read generated from the 5,000-simulation results.
