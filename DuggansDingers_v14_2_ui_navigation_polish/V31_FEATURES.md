# DuggansDingers V31 — Visual Analytics

## Slugging Heat Map
Added to Player Intelligence directly below the Statcast and opposing-pitcher section.

The 3x3 zone map uses:
- season slugging percentage
- recent home-run rate versus season form
- barrel percentage
- hard-hit percentage
- batter side
- opposing-pitcher hand
- opposing-pitcher HR/9

Each zone displays its modeled slugging percentage and uses a blue-to-red heat scale.
The panel also identifies the hottest zone, modeled peak SLG, barrel rate, and hard-hit rate.

Because the current data sources do not include a complete pitch-location feed, this is
explicitly labeled as a modeled zone profile rather than raw pitch-by-pitch Statcast data.

## Matchup Edge Graph
Added to every individual Matchup Center game page.

The leading hitter from each team is compared with the opposing starter across:
- contact
- slugging/power
- hard-hit contact
- barrel profile
- strikeout control

The hitter side uses AVG, SLG, hard-hit%, barrel%, and strikeout rate. The pitcher side
uses WHIP, HR/9 suppression, hard-hit suppression, barrel suppression, and K/9.

Two neon comparison graphs appear side-by-side on desktop and stack on mobile.
