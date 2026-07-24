from __future__ import annotations

import csv
import json
import os
import re
import unicodedata
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any, Iterable

import requests
from dotenv import load_dotenv

from config import BASE_DIR

load_dotenv(BASE_DIR / ".env", override=False)

ODDS_FILE = BASE_DIR / "data" / "odds.csv"
LIVE_CACHE_FILE = BASE_DIR / "data" / "cache" / "odds_api_io.json"
API_BASE = os.getenv("ODDS_API_IO_BASE_URL", "https://api.odds-api.io/v3").rstrip("/")
API_BOOKMAKERS = os.getenv("ODDS_API_IO_BOOKMAKERS", "DraftKings,FanDuel").strip() or "DraftKings,FanDuel"
ODDS_TIMEZONE = os.getenv("ODDS_TIMEZONE", "America/New_York").strip() or "America/New_York"


@dataclass(frozen=True)
class OddsRecord:
    slate_date: str
    player_name: str
    team: str
    book: str
    american_odds: float
    player_id: int | None = None
    game_id: str = ""


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if isinstance(value, str):
            value = value.strip().replace("+", "")
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any) -> int | None:
    try:
        text = str(value).strip()
        if not text:
            return None
        return int(float(text))
    except (TypeError, ValueError):
        return None


def normalize_name(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.lower().replace("’", "'")
    text = re.sub(r"\b(jr|sr|ii|iii|iv)\.?\b", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def american_to_decimal(value: Any) -> float:
    odds = safe_float(value)
    if odds > 0:
        return 1 + odds / 100
    if odds < 0:
        return 1 + 100 / abs(odds)
    return 1.0


def decimal_to_american(value: Any) -> float:
    decimal = safe_float(value)
    if decimal <= 1:
        return 0.0
    if decimal >= 2:
        return round((decimal - 1) * 100)
    return round(-100 / (decimal - 1))


def normalize_odds(value: Any) -> float:
    number = safe_float(value)
    if number == 0:
        return 0.0
    # Decimal prices normally sit between 1.01 and 100. American prices are
    # generally outside that range. This lets the adapter support either.
    if 1.001 < number < 100:
        return decimal_to_american(number)
    return number


def implied_probability(value: Any) -> float:
    decimal = american_to_decimal(value)
    return 1 / decimal if decimal > 1 else 0.0


def fair_american_from_probability(probability: float) -> float:
    probability = max(0.000001, min(0.999999, probability))
    if probability < 0.5:
        return ((1 - probability) / probability) * 100
    return -(probability / (1 - probability)) * 100


def expected_value(stake: float, model_probability: float, american_odds: Any) -> float:
    decimal = american_to_decimal(american_odds)
    profit_if_win = stake * (decimal - 1)
    return model_probability * profit_if_win - (1 - model_probability) * stake


def _record_from_row(row: dict[str, Any]) -> OddsRecord | None:
    player_name = str(row.get("player_name") or row.get("player") or row.get("name") or "").strip()
    book = str(row.get("book") or row.get("sportsbook") or "").strip() or "Unknown"
    american = safe_float(row.get("american_odds") or row.get("odds") or row.get("price"))
    if not player_name or not american:
        return None
    return OddsRecord(
        slate_date=str(row.get("date") or row.get("slate_date") or "").strip(),
        player_name=player_name,
        team=str(row.get("team") or row.get("team_abbr") or "").strip().upper(),
        book=book,
        american_odds=american,
        player_id=safe_int(row.get("player_id") or row.get("mlb_player_id")),
        game_id=str(row.get("game_id") or "").strip(),
    )


def load_odds(path: Path = ODDS_FILE, target_date: str | None = None) -> list[OddsRecord]:
    if not path.exists():
        return []
    records: list[OddsRecord] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            record = _record_from_row(row)
            if record is None:
                continue
            if target_date and record.slate_date and record.slate_date != target_date:
                continue
            records.append(record)
    return records


def _api_get(path: str, params: dict[str, Any], timeout: int = 25) -> Any:
    response = requests.get(f"{API_BASE}/{path.lstrip('/')}", params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _event_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("events", "data", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _event_date(event: dict[str, Any]) -> str:
    raw = str(event.get("date") or event.get("startTime") or event.get("commence_time") or "")
    return raw[:10]


def _is_mlb_event(event: dict[str, Any]) -> bool:
    league = event.get("league") or {}
    slug = str(league.get("slug") if isinstance(league, dict) else league).lower()
    name = str(league.get("name") if isinstance(league, dict) else league).lower()
    return slug == "usa-mlb" or name == "usa - mlb" or " major league baseball" in f" {name}"


def _parse_event_datetime(event: dict[str, Any]) -> datetime | None:
    raw = str(event.get("date") or event.get("startTime") or event.get("commence_time") or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def fetch_mlb_events(api_key: str, target_date: str) -> list[dict[str, Any]]:
    """Return future, pending MLB events whose local slate date matches target_date.

    Odds-API.io timestamps are UTC. Comparing the first ten characters of the
    timestamp to a U.S. slate date incorrectly includes prior-night settled games
    and excludes some evening games. Convert to the configured local timezone first.
    """
    payload = _api_get("events", {"apiKey": api_key, "sport": "baseball"})
    try:
        slate = date.fromisoformat(target_date)
    except ValueError:
        slate = date.today()
    try:
        local_tz = ZoneInfo(ODDS_TIMEZONE)
    except Exception:
        local_tz = ZoneInfo("America/New_York")

    now_utc = datetime.now(timezone.utc)
    selected: list[dict[str, Any]] = []
    for event in _event_list(payload):
        if not _is_mlb_event(event):
            continue
        if str(event.get("status") or "").lower() != "pending":
            continue
        starts_at = _parse_event_datetime(event)
        if starts_at is None or starts_at <= now_utc:
            continue
        if starts_at.astimezone(local_tz).date() != slate:
            continue
        selected.append(event)

    selected.sort(key=lambda event: _parse_event_datetime(event) or datetime.max.replace(tzinfo=timezone.utc))
    return selected


def _text_from(node: dict[str, Any], keys: Iterable[str]) -> str:
    for key in keys:
        value = node.get(key)
        if value is not None and not isinstance(value, (dict, list)):
            text = str(value).strip()
            if text:
                return text
    return ""


def _market_is_home_run(value: str) -> bool:
    text = normalize_name(value)
    return (
        "home run" in text
        or "home runs" in text
        or "homerun" in text
        or text in {"batter hr", "player hr", "to hit a home run"}
    )


def _selection_is_yes_or_over(node: dict[str, Any], inherited_market: str) -> bool:
    label = _text_from(node, ("selection", "side", "outcome", "label", "type", "name"))
    line = safe_float(node.get("line") or node.get("point") or node.get("handicap"), default=-999)
    normalized = normalize_name(label)
    if _market_is_home_run(inherited_market):
        if normalized in {"no", "under"}:
            return False
        if line != -999 and line > 0.5:
            return False
        return True
    return normalized in {"yes", "over", "to hit a home run"} and (line in {-999, 0, 0.5})


def _extract_player_name(node: dict[str, Any]) -> str:
    direct = _text_from(node, ("player_name", "playerName", "participant", "participantName", "description"))
    if direct:
        return direct
    player = node.get("player")
    if isinstance(player, str):
        return player.strip()
    if isinstance(player, dict):
        return _text_from(player, ("name", "fullName", "playerName"))
    # Some feeds put the player in `name` and the side in `label`/`selection`.
    name = _text_from(node, ("name",))
    side = _text_from(node, ("selection", "side", "outcome", "label", "type"))
    if name and normalize_name(name) not in {"yes", "no", "over", "under"} and name != side:
        return name
    return ""


def _extract_price(node: dict[str, Any]) -> float:
    for key in ("american_odds", "americanOdds", "price", "odds", "value"):
        if key in node:
            value = node.get(key)
            if isinstance(value, dict):
                value = value.get("american") or value.get("decimal") or value.get("value")
            result = normalize_odds(value)
            if result:
                return result
    return 0.0


def _walk_offers(
    node: Any,
    *,
    target_date: str,
    event_id: str,
    book: str = "",
    market: str = "",
) -> list[OddsRecord]:
    records: list[OddsRecord] = []
    if isinstance(node, list):
        for item in node:
            records.extend(_walk_offers(item, target_date=target_date, event_id=event_id, book=book, market=market))
        return records
    if not isinstance(node, dict):
        return records

    local_book = book
    local_market = market
    book_candidate = _text_from(node, ("bookmaker", "sportsbook", "book", "bookmakerName", "key"))
    market_candidate = _text_from(node, ("market", "marketName", "market_name", "group", "betType", "key", "name"))
    if book_candidate and not _market_is_home_run(book_candidate):
        local_book = book_candidate
    if market_candidate and _market_is_home_run(market_candidate):
        local_market = market_candidate

    price = _extract_price(node)
    player_name = _extract_player_name(node)
    if price and player_name and _market_is_home_run(local_market) and _selection_is_yes_or_over(node, local_market):
        records.append(
            OddsRecord(
                slate_date=target_date,
                player_name=player_name,
                team="",
                book=local_book or "Odds-API.io",
                american_odds=price,
                game_id=event_id,
            )
        )

    for key, value in node.items():
        next_book = local_book
        next_market = local_market
        if isinstance(value, (dict, list)):
            # Dictionary keys frequently carry bookmaker or market names.
            if _market_is_home_run(str(key)):
                next_market = str(key)
            elif not next_book and str(key).lower() not in {"bookmakers", "markets", "odds", "outcomes", "selections", "data"}:
                if isinstance(value, dict) and any(k in value for k in ("markets", "odds", "outcomes")):
                    next_book = str(key)
            records.extend(
                _walk_offers(
                    value,
                    target_date=target_date,
                    event_id=event_id,
                    book=next_book,
                    market=next_market,
                )
            )
    return records



def _parse_odds_api_io_player_props(payload: Any, target_date: str, event_id: str) -> list[OddsRecord]:
    """Parse the documented Odds-API.io MLB Player Props response.

    Shape observed from the live API:
      bookmakers -> DraftKings/FanDuel -> [{name: "Player Props", odds: [...]}]
    A one-home-run offer is identified by a label ending in ``(Home Runs)`` and
    handicap 0.5. The ``over`` value is decimal odds.
    """
    if not isinstance(payload, dict):
        return []
    bookmakers = payload.get("bookmakers")
    if not isinstance(bookmakers, dict):
        return []

    records: list[OddsRecord] = []
    label_pattern = re.compile(r"^\s*(.+?)\s*\(Home Runs\)\s*$", re.IGNORECASE)
    for book, markets in bookmakers.items():
        if not isinstance(markets, list):
            continue
        for market in markets:
            if not isinstance(market, dict) or normalize_name(market.get("name")) != "player props":
                continue
            offers = market.get("odds")
            if not isinstance(offers, list):
                continue
            for offer in offers:
                if not isinstance(offer, dict):
                    continue
                match = label_pattern.match(str(offer.get("label") or ""))
                if not match:
                    continue
                if abs(safe_float(offer.get("hdp"), default=-999) - 0.5) > 1e-9:
                    continue
                decimal_price = safe_float(offer.get("over"))
                if decimal_price <= 1:
                    continue
                records.append(
                    OddsRecord(
                        slate_date=target_date,
                        player_name=match.group(1).strip(),
                        team="",
                        book=str(book),
                        american_odds=decimal_to_american(decimal_price),
                        game_id=event_id,
                    )
                )
    return records

def _dedupe_records(records: list[OddsRecord]) -> list[OddsRecord]:
    best: dict[tuple[str, str, str], OddsRecord] = {}
    for record in records:
        key = (normalize_name(record.player_name), record.book.lower(), record.game_id)
        existing = best.get(key)
        if existing is None or american_to_decimal(record.american_odds) > american_to_decimal(existing.american_odds):
            best[key] = record
    return list(best.values())




def _cached_live_result(target_date: str) -> tuple[list[OddsRecord], dict[str, Any]] | None:
    """Return a recent cached odds result.

    Successful pulls are reused for one hour. Empty or failed pulls are reused
    for only five minutes so the app retries automatically without a button.
    """
    if not LIVE_CACHE_FILE.exists():
        return None
    try:
        cached = json.loads(LIVE_CACHE_FILE.read_text(encoding="utf-8"))
        if str(cached.get("target_date") or "") != target_date:
            return None
        updated_at = datetime.fromisoformat(str(cached.get("updated_at") or "").replace("Z", "+00:00"))
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - updated_at.astimezone(timezone.utc)).total_seconds()
        raw_records = cached.get("records") or []
        max_age = 3600 if raw_records else 300
        if age < 0 or age > max_age:
            return None
        records = [OddsRecord(**item) for item in raw_records if isinstance(item, dict)]
        status = cached.get("status") or {}
        if not isinstance(status, dict):
            status = {}
        status = dict(status)
        status["from_cache"] = True
        status["raw_cache"] = str(LIVE_CACHE_FILE)
        return records, status
    except Exception:
        return None


def clear_live_odds_cache() -> None:
    try:
        LIVE_CACHE_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def fetch_live_odds(target_date: str) -> tuple[list[OddsRecord], dict[str, Any]]:
    api_key = os.getenv("ODDS_API_IO_KEY", "").strip()
    if not api_key:
        return [], {"connected": False, "status": "API key not configured", "events": 0, "offers": 0}

    cached = _cached_live_result(target_date)
    if cached is not None:
        return cached

    try:
        events = fetch_mlb_events(api_key, target_date)
        all_records: list[OddsRecord] = []
        raw_events: list[dict[str, Any]] = []
        skipped_events: list[dict[str, Any]] = []
        for event in events:
            event_id = str(event.get("id") or "")
            if not event_id:
                continue
            try:
                params: dict[str, Any] = {"apiKey": api_key, "eventId": event_id}
                if API_BOOKMAKERS:
                    params["bookmakers"] = API_BOOKMAKERS
                payload = _api_get("odds", params)
            except requests.HTTPError as exc:
                # Odds-API.io can return HTTP 400 for an otherwise valid MLB
                # event when no sportsbook odds are available yet. Do not let
                # one unavailable game cancel the entire slate refresh.
                response = exc.response
                skipped_events.append({
                    "event_id": event_id,
                    "status_code": response.status_code if response is not None else None,
                    "message": (response.text[:300] if response is not None else str(exc)),
                })
                continue
            raw_events.append({"event": event, "odds": payload})
            parsed = _parse_odds_api_io_player_props(payload, target_date=target_date, event_id=event_id)
            # Keep the generic walker as a compatibility fallback for any future
            # alternate response shape, but prefer the exact documented parser.
            if not parsed:
                parsed = _walk_offers(payload, target_date=target_date, event_id=event_id)
            all_records.extend(parsed)

        records = _dedupe_records(all_records)
        if records:
            status_text = "Live HR props loaded automatically"
        elif events and skipped_events:
            status_text = f"Checked {len(events)} upcoming MLB game(s); {len(skipped_events)} odds request(s) failed and no 0.5 HR offers were returned"
        elif events:
            status_text = "Upcoming MLB games found, but no 0.5 home-run offers were returned by the selected books"
        else:
            status_text = "No MLB events found for this slate"
        status_payload = {
            "connected": True,
            "status": status_text,
            "events": len(events),
            "offers": len(records),
            "skipped_events": len(skipped_events),
            "raw_cache": str(LIVE_CACHE_FILE),
            "from_cache": False,
        }
        LIVE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        LIVE_CACHE_FILE.write_text(
            json.dumps({
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "target_date": target_date,
                "records": [asdict(record) for record in records],
                "status": status_payload,
                "events": raw_events,
                "skipped_events": skipped_events,
            }, indent=2),
            encoding="utf-8",
        )
        return records, status_payload
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else ""
        return [], {"connected": False, "status": f"Odds API HTTP error {status_code}", "events": 0, "offers": 0}
    except Exception as exc:
        return [], {"connected": False, "status": f"Odds API error: {exc}", "events": 0, "offers": 0}


def _match_score(player: dict[str, Any], record: OddsRecord) -> int:
    player_id = safe_int(player.get("player_id"))
    if player_id is not None and record.player_id is not None:
        if player_id != record.player_id:
            return -1
        return 100

    if normalize_name(player.get("player_name")) != normalize_name(record.player_name):
        return -1

    score = 60
    player_team = str(player.get("team_name") or "").upper()
    if record.team:
        if record.team != player_team:
            return -1
        score += 25
    if record.game_id:
        player_game_id = str(player.get("odds_event_id") or player.get("game_id") or "")
        # Ballpark Pal and Odds-API.io use different game IDs. Only enforce this
        # comparison when the player row has an Odds-API event ID.
        if player.get("odds_event_id") and record.game_id != player_game_id:
            return -1
        score += 5
    return score


def enrich_board_odds(board: dict[str, Any], path: Path = ODDS_FILE) -> dict[str, Any]:
    rankings = board.get("rankings", []) or []
    target_date = str(board.get("date") or date.today().isoformat())

    live_records, live_status = fetch_live_odds(target_date)
    manual_records = load_odds(path, target_date)
    # Manual rows stay useful as a fallback and can override/add books that the
    # live provider does not return.
    records = _dedupe_records(live_records + manual_records)

    matched_players = 0
    unmatched_records = set(range(len(records)))
    books: set[str] = set()

    for player in rankings:
        matches: list[tuple[int, OddsRecord]] = []
        for index, record in enumerate(records):
            score = _match_score(player, record)
            if score >= 0:
                matches.append((index, record))
        matches.sort(key=lambda item: (item[1].book.lower(), -american_to_decimal(item[1].american_odds)))

        offers = [
            {
                "book": record.book,
                "american_odds": record.american_odds,
                "decimal_odds": american_to_decimal(record.american_odds),
                "implied_probability": implied_probability(record.american_odds),
                "source": "live" if record in live_records else "manual",
            }
            for _, record in matches
        ]
        player["sportsbook_offers"] = offers
        player["sportsbook_connected"] = bool(offers)
        if not offers:
            player["best_book"] = ""
            player["best_odds"] = None
            player["book_implied_probability"] = None
            player["edge_pct"] = None
            player["ev_10"] = None
            player["roi_pct"] = None
            continue

        matched_players += 1
        for index, record in matches:
            unmatched_records.discard(index)
            books.add(record.book)

        best = max(offers, key=lambda offer: offer["decimal_odds"])
        model_probability = player.get("probability") or 0
        try:
            model_probability = float(model_probability)
        except (TypeError, ValueError):
            model_probability = 0.0
        if model_probability > 1:
            model_probability /= 100
        model_probability = max(0.0, min(1.0, model_probability))

        player["best_book"] = best["book"]
        player["best_odds"] = best["american_odds"]
        player["book_implied_probability"] = best["implied_probability"]
        player["edge_pct"] = (model_probability - best["implied_probability"]) * 100
        player["ev_10"] = expected_value(10.0, model_probability, best["american_odds"])
        player["roi_pct"] = player["ev_10"] * 10
        player["model_fair_odds"] = fair_american_from_probability(model_probability) if model_probability else player.get("fair_odds")

    positive_edges = [player for player in rankings if player.get("edge_pct") is not None and float(player["edge_pct"]) > 0]
    source = "Odds-API.io Live" if live_records else ("Manual CSV" if manual_records else "Not connected")
    board["odds_summary"] = {
        "source": source,
        "file": str(path),
        "records": len(records),
        "live_records": len(live_records),
        "manual_records": len(manual_records),
        "matched_players": matched_players,
        "unmatched_records": len(unmatched_records),
        "books": sorted(books),
        "positive_edges": len(positive_edges),
        "connected": bool(records) or bool(live_status.get("connected")),
        "api_status": live_status.get("status", ""),
        "api_events": live_status.get("events", 0),
        "raw_cache": live_status.get("raw_cache", ""),
    }
    board.setdefault("data_sources", {})["Sportsbook Odds"] = "live" if live_records else ("manual" if manual_records else "unavailable")
    return board


def write_uploaded_odds(payload: bytes, path: Path = ODDS_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def template_csv() -> bytes:
    content = (
        "date,player_id,player_name,team,book,american_odds,game_id\n"
        "2026-07-22,592450,Aaron Judge,NYY,DraftKings,+240,\n"
        "2026-07-22,656941,Kyle Tucker,CHC,FanDuel,+390,\n"
    )
    return content.encode("utf-8")
