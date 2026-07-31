# Prepared Fast-Start Snapshot

`current_full.json` is created by the scheduled GitHub Action.

It contains the already-built hitter board, probable pitchers, weather, and
sportsbook data. Because the file is committed to GitHub, Streamlit can read it
immediately after waking instead of rebuilding every API feed for each visitor.
