# Update the existing Streamlit site

Do **not** delete the Streamlit app and do **not** change its URL.

1. Extract the V18 ZIP.
2. Open the extracted V18 folder.
3. Open the GitHub folder your current Streamlit deployment already uses.
4. Delete the old contents of that live folder except any local `.env` file you keep only on your computer.
5. Copy everything **inside** the extracted V18 folder into that existing live folder.
6. Commit the replacement directly to `main`.
7. Streamlit will rebuild automatically while keeping the same URL and stored Secrets.

Do not place the V18 parent folder inside the existing live folder. `app.py` must remain at the exact GitHub path already configured in Streamlit.

## Required Streamlit Secrets

```toml
BALLPARKPAL_API_KEY = "..."

ODDS_API_IO_KEY = "..."
ODDS_API_IO_BASE_URL = "https://api.odds-api.io/v3"
ODDS_API_IO_BOOKMAKERS = "DraftKings,FanDuel"
ODDS_TIMEZONE = "America/New_York"

WEATHERAPI_KEY = "..."
VISUAL_CROSSING_API_KEY = "" # optional fallback
```

The weather code accepts either `WEATHERAPI_KEY` or the legacy `WEATHER_API_KEY`, but `WEATHERAPI_KEY` is preferred.
