# Duggan's Dingers v14 — Template Mirror Redesign

This build redesigns the Streamlit app to closely mirror the approved dark sports-dashboard template.

## Included

- Branded top header with six icon navigation items
- Compact six-player daily picks row
- Transparent/cutout MLB player photography
- Large live weather and ballpark panel
- Directional LF/CF/RF home-run effectiveness field
- Game-time forecast panel
- Team cheat-sheet matchup cards
- Today's games panel
- Quick-tool navigation
- Responsive desktop, tablet, and iPhone layouts
- No login screen and no username/password secrets
- More robust Open-Meteo weather retrieval and fallback handling

## Streamlit secrets

Only the data-source secrets are needed:

```toml
BALLPARKPAL_API_KEY = "your-key"
ODDS_API_IO_KEY = "your-key"
ODDS_API_IO_BASE_URL = "https://api.odds-api.io/v3"
ODDS_API_IO_BOOKMAKERS = "DraftKings,FanDuel"
ODDS_TIMEZONE = "America/New_York"
```

## Main file path

If the entire folder is uploaded to GitHub:

```text
DuggansDingers_v14_template_mirror/app.py
```

If the contents are uploaded directly to the repository root:

```text
app.py
```
