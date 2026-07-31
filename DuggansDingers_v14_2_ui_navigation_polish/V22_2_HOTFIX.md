# V22.2 Game Sims Hotfix

- Fixed `UnboundLocalError: projected_runs` in Game Sims.
- `projected_runs` is now calculated before the hit-projection formula uses it.
- Kept hit projections as per-team estimates rather than combined game totals.
- Verified the simulator with a two-team sample game after patching.
