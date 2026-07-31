# V24 Weather Asset Mapping Fix

This package focuses on the Ballpark Weather page.

## Included fixes
- Forces weather cards to use stable venue-specific local stadium art.
- Removes random generic scene rotation.
- Adds a dedicated `assets/stadium_renders/` folder for team-by-team stadium renders.
- Brightens team logos on weather cards and weather detail headers.
- Lightens image overlays so stadium scenes read more clearly.

## Notes
- The app now prefers files in `assets/stadium_renders/<TEAM>.jpg`.
- If you later create better AI ballpark renders, drop them into that folder using team abbreviations like `LAD.jpg`, `NYY.jpg`, `BOS.jpg`, etc.
- Included starter files are copied from the current packaged weather scenes so the page works immediately after upload.

## Changed files
- `components/stadium_art.py`
- `assets/v22.css`
- `assets/stadium_renders/*.jpg`
