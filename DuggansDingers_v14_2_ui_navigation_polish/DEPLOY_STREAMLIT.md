# Streamlit Community Cloud deployment

If this folder is uploaded to GitHub as `DuggansDingers_v15_neon_intelligence_rebuild`, use:

```text
Repository: DuggansDingers/DuggansDingers
Branch: main
Main file path: DuggansDingers_v15_neon_intelligence_rebuild/app.py
```

Under **Advanced settings → Secrets**, use:

```toml
BALLPARKPAL_API_KEY = "YOUR_REAL_KEY"
ODDS_API_IO_KEY = "YOUR_REAL_KEY"
ODDS_API_IO_BASE_URL = "https://api.odds-api.io/v3"
ODDS_API_IO_BOOKMAKERS = "DraftKings,FanDuel"
ODDS_TIMEZONE = "America/New_York"

# Recommended for reliable weather at every park, including Toronto.
WEATHERAPI_KEY = "YOUR_REAL_WEATHERAPI_KEY"

# Optional second weather provider.
VISUAL_CROSSING_API_KEY = ""
```

No login username, login password, or cookie secret is required.
