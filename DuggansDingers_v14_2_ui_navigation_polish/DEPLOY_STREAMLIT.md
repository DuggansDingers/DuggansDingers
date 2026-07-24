# Deploy / Update Streamlit

You do not need to delete the existing Streamlit app.

1. Extract this ZIP.
2. Copy the files **inside** the extracted folder into the existing GitHub folder that Streamlit already uses.
3. Replace the old files and commit directly to `main`.
4. Streamlit will rebuild automatically while keeping the same URL and Secrets.

Required Secrets:

```toml
BALLPARKPAL_API_KEY = "YOUR_KEY"
ODDS_API_IO_KEY = "YOUR_KEY"
ODDS_API_IO_BASE_URL = "https://api.odds-api.io/v3"
ODDS_API_IO_BOOKMAKERS = "DraftKings,FanDuel"
ODDS_TIMEZONE = "America/New_York"
WEATHERAPI_KEY = "YOUR_KEY"
VISUAL_CROSSING_API_KEY = ""
```

The weather code also accepts the alternate secret name `WEATHER_API_KEY`.
