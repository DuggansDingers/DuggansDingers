from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from typing import Any
from zoneinfo import ZoneInfo

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

SNAPSHOT_DIR = APP_DIR / "data" / "snapshots"
SNAPSHOT_FILE = SNAPSHOT_DIR / "current_full.json"
METADATA_FILE = SNAPSHOT_DIR / "metadata.json"


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    temporary.replace(path)


def _today_new_york() -> str:
    return datetime.now(ZoneInfo("America/New_York")).date().isoformat()


def _mark_failure(board: dict[str, Any], source: str, error: Exception) -> None:
    board.setdefault("snapshot_warnings", []).append(f"{source}: {error}")
    board.setdefault("data_sources", {})[source] = "snapshot refresh failed"


def build_snapshot(target_date: str) -> dict[str, Any]:
    if not os.getenv("BALLPARKPAL_API_KEY", "").strip():
        raise RuntimeError(
            "BALLPARKPAL_API_KEY is missing. Add it under "
            "GitHub repository Settings → Secrets and variables → Actions."
        )

    from model import get_home_run_rankings

    print(f"Building base model for {target_date}...", flush=True)
    board = get_home_run_rankings(target_date=target_date)
    if not board.get("rankings"):
        raise RuntimeError("The base model returned no ranked hitters; existing snapshot was preserved.")

    try:
        from services.weather import enrich_board_weather

        print("Adding weather...", flush=True)
        board = enrich_board_weather(deepcopy(board))
    except Exception as exc:
        print(f"Weather refresh failed: {exc}", flush=True)
        _mark_failure(board, "Weather", exc)

    try:
        from services.odds import enrich_board_odds

        print("Adding sportsbook odds...", flush=True)
        board = enrich_board_odds(deepcopy(board))
    except Exception as exc:
        print(f"Odds refresh failed: {exc}", flush=True)
        _mark_failure(board, "Sportsbook Odds", exc)

    generated_at = datetime.now(timezone.utc).isoformat()
    board["date"] = target_date
    board["updated_at"] = generated_at
    board["snapshot_generated_at"] = generated_at
    board["snapshot_status"] = "prepared by GitHub Actions"
    board["fast_start"] = True
    board.setdefault("data_sources", {})["Fast Start"] = "prepared"

    if not board.get("rankings"):
        raise RuntimeError("Snapshot validation failed: rankings are empty.")
    return board


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the persistent daily fast-start board.")
    parser.add_argument("--date", default="", help="Slate date in YYYY-MM-DD format.")
    args = parser.parse_args()

    target_date = args.date.strip() or _today_new_york()
    board = build_snapshot(target_date)

    _atomic_json(SNAPSHOT_FILE, board)
    _atomic_json(
        METADATA_FILE,
        {
            "date": target_date,
            "generated_at": board.get("snapshot_generated_at"),
            "games": board.get("games", 0),
            "ranked_hitters": len(board.get("rankings", [])),
            "weather_games": (board.get("weather_summary") or {}).get("games_available", 0),
            "odds_offers": (board.get("odds_summary") or {}).get("live_records", 0),
            "warnings": board.get("snapshot_warnings", []),
        },
    )

    print(
        f"Snapshot ready: {len(board.get('rankings', []))} hitters, "
        f"{board.get('games', 0)} games → {SNAPSHOT_FILE}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
