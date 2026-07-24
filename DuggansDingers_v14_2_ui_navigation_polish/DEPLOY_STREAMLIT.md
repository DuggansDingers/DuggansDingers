# Updating the existing Streamlit site

Do not delete the Streamlit app and do not change its URL.

1. Extract the V17 ZIP.
2. Open the extracted folder.
3. Copy everything **inside** the folder into the GitHub folder your current Streamlit deployment already uses.
4. Replace the old files and folders.
5. Commit directly to `main`.
6. Streamlit will rebuild automatically and keep the same URL and secrets.

Do not place the V17 parent folder inside the existing live folder. `app.py` must remain at the same GitHub path Streamlit already uses.

## Required secrets

```toml
BALLPARKPAL_API_KEY = "..."
ODDS_API_IO_KEY = "..."
ODDS_API_IO_BASE_URL = "https://api.odds-api.io/v3"
ODDS_API_IO_BOOKMAKERS = "DraftKings,FanDuel"
ODDS_TIMEZONE = "America/New_York"
WEATHERAPI_KEY = "..."
VISUAL_CROSSING_API_KEY = "" # optional fallback
```
