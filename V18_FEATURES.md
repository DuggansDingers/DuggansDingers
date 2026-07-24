# V18 Mockup-Spec Rebuild

## Visual system
- Fixed left navigation rail matching the approved mockups
- Neon hover and active states for every navigation icon and label
- Large centered Duggan's Dingers wordmark with slate-date control
- Brighter navy/black background, high-contrast white text, and multi-color neon accents
- Native white Streamlit surfaces overridden with dark custom styling
- Custom responsive rules for desktop, tablet, and mobile

## Dashboard
- Six premium featured-player cards with real player headshots
- Distinct Top Pick, Power Matchup, Hottest Bat, Highest HR Probability, Best Ballpark, and Best Value treatments
- Matchup reasons and probable-pitcher information inside every card
- Compact Top 25 intelligence table modeled after the approved homepage mockup
- Bottom summary strip for slate size, ranked hitters, probable pitchers, value edges, and recent power

## Ballpark Weather
- MLB schedule is the authoritative game, venue, and home-team source
- Ballpark Pal `teamHomeId`, `teamAwayId`, `venueId`, and `gameTimeUTC` fields are supported
- Team-ID and player-level fallback matching when schedule metadata is incomplete
- Three ballparks per row
- Real stadium aerial imagery centered on each matched venue
- Clickable ballpark cards opening a detailed game-time weather panel and weather-adjusted hitter board

## Rankings
- Five compact featured players per row
- Probable pitcher, handedness, HR/9, reasons, probability, and score shown in the featured layer
- Custom dark rankings table and high-contrast controls

## Team Sheets
- Both clubs shown side by side
- Matchup selector opens the highest-projected HR game by default
- Probable pitcher cards, top hitters, recent form, live price, and matchup notes
- Improved Last 7 and Last 15 form guide

## Game Sims
- Full-slate clickable simulation board instead of a dropdown
- Selected matchup opens in the main simulation panel
- Projected score, runs, hits, HR, strikeouts, stolen bases, win probability, game total, and sportsbook O/U pricing
- Two-sentence AI-style simulation summary

## Reliability and performance
- Faster page-specific loading flags so heavy APIs are skipped when a page does not need them
- Cached MLB schedule and weather data
- Concurrent external data fetching where supported
- Navigation renders before cold data loading begins
