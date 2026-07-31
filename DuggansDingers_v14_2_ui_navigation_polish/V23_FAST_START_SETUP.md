# V23 Fast Start

## What changed

The app now checks `data/snapshots/current_full.json` before making any API
requests. That snapshot already contains:

- Ballpark Pal projections
- MLB player history
- Statcast
- probable pitchers
- weather
- DraftKings and FanDuel prices

The snapshot is built by GitHub Actions and committed to the repository. It
survives Streamlit sleep and container restarts.

## One-time setup

1. Replace the files in your existing live Streamlit folder with the V23 app files.
2. Copy `.github/workflows/duggans-fast-start.yml` to the repository root.
3. Add GitHub Actions repository secrets:
   - `BALLPARKPAL_API_KEY` — required
   - `WEATHERAPI_KEY` — recommended
   - `ODDS_API_IO_KEY` — recommended
   - `VISUAL_CROSSING_API_KEY` — optional
4. Open GitHub **Actions**.
5. Select **Build Duggans Fast-Start Snapshot**.
6. Click **Run workflow**.

After that, the workflow refreshes the prepared board three times daily.

## Manual live refresh

The sidebar now includes **Refresh live data**. It bypasses the prepared
snapshot for one run. Normal visitors continue to receive the fast snapshot.
