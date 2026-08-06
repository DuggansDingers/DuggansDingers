from __future__ import annotations

import csv
import json
import os
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any, Iterable

import requests
from dotenv import load_dotenv

from config import BASE_DIR
from services.schedule import normalize_team

load_dotenv(BASE_DIR / ".env", override=False)

ODDS_FILE = BASE_DIR / "data" / "odds.csv"
LIVE_CACHE_FILE = BASE_DIR / "data" / "cache" / "odds_api_io.json"
API_BASE = os.getenv("ODDS_API_IO_BASE_URL", "https://api.odds-api.io/v3").rstrip("/")
API_BOOKMAKERS = os.getenv("ODDS_API_IO_BOOKMAKERS", "DraftKings,FanDuel").strip() or "DraftKings,FanDuel"
ODDS_TIMEZONE = os.getenv("ODDS_TIMEZONE", "America/New_York").strip() or "America/New_York"
ODDS_CACHE_SCHEMA = 2


@dataclass(frozen=True)
class OddsRecord:
    slate_date: str
    player_name: str
    team: str
    book: str
    american_odds: float
    player_id: int | None = None
    game_id: str = ""


@dataclass(frozen=True)
class PlayerPropRecord:
    slate_date: str
    player_name: str
    market: str
    line: float | None
    side: str
    book: str
    american_odds: float
    player_id: int | None = None
    team: str = ""
    game_id: str = ""
    source: str = "live"


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


# Canonical market names consumed by the Next.js Prop Command and Kitchen pages.
# Keep this list intentionally narrow so team totals and game totals cannot be
# mistaken for player props.
def canonical_player_market(value: Any) -> str:
    text = normalize_name(value)
    if not text or text == "player props":
        return ""

    if any(token in text for token in ("hits runs rbis", "hits runs rbi", "singles", "doubles", "triples")):
        return ""
    if "earned runs" in text:
        return "Pitcher Earned Runs"
    if "outs recorded" in text or "pitching outs" in text or "pitcher outs" in text:
        return "Pitcher Outs Recorded"
    if "strikeout" in text or text in {"ks", "k s", "pitcher ks"}:
        return "Pitcher Strikeouts"
    if "stolen base" in text:
        return "Stolen Bases"
    if "total base" in text:
        return "Total Bases"
    if "home run" in text or "homerun" in text or text in {"batter hr", "player hr"}:
        return "Home Run"
    if "runs batted in" in text or re.search(r"\brbis?\b", text):
        return "RBIs"
    if "walk" in text and "allowed" not in text:
        return "Walks"
    if "hit" in text and "allowed" not in text:
        return "Hits"
    if "run" in text and not any(token in text for token in ("allowed", "earned", "home run")):
        return "Runs Scored"
    return ""


def _extract_line(node: dict[str, Any], market: str) -> float | None:
    for key in ("hdp", "line", "point", "handicap", "threshold", "total"):
        if key not in node or node.get(key) in (None, ""):
            continue
        value = safe_float(node.get(key), default=float("nan"))
        if value == value:
            return value
    # Home-run props are commonly yes/no offers without an explicit line.
    return 0.5 if market == "Home Run" else None


def _split_player_market_label(label: Any, fallback_market: Any = "") -> tuple[str, str]:
    raw = " ".join(str(label or "").split())
    if not raw:
        return "", ""

    # Odds-API.io's documented baseball shape uses labels like
    # "Shohei Ohtani (Home Runs)".
    match = re.match(r"^(.+?)\s*\(([^()]*)\)\s*$", raw)
    if match:
        market = canonical_player_market(match.group(2))
        if market:
            return match.group(1).strip(), market

    for separator in (" - ", " | ", ": "):
        if separator not in raw:
            continue
        left, right = [part.strip() for part in raw.rsplit(separator, 1)]
        market = canonical_player_market(right)
        if market:
            return left, market
        market = canonical_player_market(left)
        if market:
            return right, market

    fallback = canonical_player_market(fallback_market)
    if fallback and normalize_name(raw) not in {"over", "under", "yes", "no"}:
        return raw, fallback
    return "", ""


def _offer_side_prices(offer: dict[str, Any]) -> list[tuple[str, float]]:
    prices: list[tuple[str, float]] = []
    side_fields = (
        ("Over", ("over", "overOdds", "over_odds")),
        ("Under", ("under", "underOdds", "under_odds")),
        ("Yes", ("yes", "yesOdds", "yes_odds")),
        ("No", ("no", "noOdds", "no_odds")),
    )
    for side, keys in side_fields:
        for key in keys:
            if key not in offer or offer.get(key) in (None, ""):
                continue
            price = normalize_odds(offer.get(key))
            if price:
                prices.append((side, price))
            break

    if prices:
        return prices

    side = _text_from(offer, ("side", "selection", "outcome", "type"))
    price = _extract_price(offer)
    normalized_side = normalize_name(side)
    if price and normalized_side in {"over", "under", "yes", "no"}:
        return [(normalized_side.title(), price)]
    return []


def _parse_odds_api_io_all_player_props(payload: Any, target_date: str, event_id: str) -> list[PlayerPropRecord]:
    if not isinstance(payload, dict):
        return []
    bookmakers = payload.get("bookmakers")
    if not isinstance(bookmakers, dict):
        return []

    records: list[PlayerPropRecord] = []
    for book, markets in bookmakers.items():
        if not isinstance(markets, list):
            continue
        for market_node in markets:
            if not isinstance(market_node, dict):
                continue
            container_name = _text_from(market_node, ("name", "label", "market", "marketName"))
            normalized_container = normalize_name(container_name)
            if "player prop" not in normalized_container and not canonical_player_market(container_name):
                continue
            offers = market_node.get("odds") or market_node.get("outcomes") or market_node.get("selections") or []
            if isinstance(offers, dict):
                offers = [offers]
            if not isinstance(offers, list):
                continue
            for offer in offers:
                if not isinstance(offer, dict):
                    continue
                label = _text_from(offer, ("label", "description", "name", "participant", "participantName"))
                player_name, market = _split_player_market_label(label, container_name)
                if not player_name or not market:
                    # Some feeds separate the participant and stat fields.
                    player_name = _extract_player_name(offer)
                    market = canonical_player_market(
                        _text_from(offer, ("market", "marketName", "market_name", "statType", "stat_type", "betType", "bet_type"))
                        or container_name
                    )
                if not player_name or not market:
                    continue
                line = _extract_line(offer, market)
                for side, american_odds in _offer_side_prices(offer):
                    records.append(
                        PlayerPropRecord(
                            slate_date=target_date,
                            player_name=player_name,
                            market=market,
                            line=line,
                            side=side,
                            book=str(book),
                            american_odds=american_odds,
                            game_id=event_id,
                        )
                    )
    return records


def _walk_player_prop_offers(
    node: Any,
    *,
    target_date: str,
    event_id: str,
    book: str = "",
    market: str = "",
) -> list[PlayerPropRecord]:
    records: list[PlayerPropRecord] = []
    if isinstance(node, list):
        for item in node:
            records.extend(
                _walk_player_prop_offers(
                    item,
                    target_date=target_date,
                    event_id=event_id,
                    book=book,
                    market=market,
                )
            )
        return records
    if not isinstance(node, dict):
        return records

    local_book = book
    local_market = market
    book_candidate = _text_from(node, ("bookmaker", "sportsbook", "book", "bookmakerName"))
    if book_candidate:
        local_book = book_candidate
    market_candidate = _text_from(node, ("market", "marketName", "market_name", "group", "betType", "statType"))
    canonical = canonical_player_market(market_candidate)
    if canonical:
        local_market = canonical

    label = _text_from(node, ("label", "description", "name", "participant", "participantName"))
    player_name, label_market = _split_player_market_label(label, local_market)
    if label_market:
        local_market = label_market
    if not player_name:
        player_name = _extract_player_name(node)
    if player_name and local_market:
        line = _extract_line(node, local_market)
        for side, price in _offer_side_prices(node):
            records.append(
                PlayerPropRecord(
                    slate_date=target_date,
                    player_name=player_name,
                    market=local_market,
                    line=line,
                    side=side,
                    book=local_book or "Odds-API.io",
                    american_odds=price,
                    game_id=event_id,
                )
            )

    for key, value in node.items():
        if not isinstance(value, (dict, list)):
            continue
        next_book = local_book
        next_market = local_market
        key_market = canonical_player_market(key)
        if key_market:
            next_market = key_market
        elif not next_book and isinstance(value, dict) and any(k in value for k in ("markets", "odds", "outcomes")):
            next_book = str(key)
        records.extend(
            _walk_player_prop_offers(
                value,
                target_date=target_date,
                event_id=event_id,
                book=next_book,
                market=next_market,
            )
        )
    return records


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


def _event_team_name(event: dict[str, Any], side: str) -> str:
    candidates = (
        event.get(side), event.get(f"{side}Team"), event.get(f"{side}_team"),
        (event.get("teams") or {}).get(side) if isinstance(event.get("teams"), dict) else None,
    )
    for value in candidates:
        if isinstance(value, dict):
            value = value.get("abbreviation") or value.get("shortName") or value.get("name") or value.get("teamName")
        if value:
            normalized = normalize_team(value)
            if normalized:
                return normalized
    return ""


def _parse_total_market(payload: Any, event: dict[str, Any], event_id: str) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    bookmakers = payload.get("bookmakers")
    if not isinstance(bookmakers, dict):
        return []
    away = _event_team_name(event, "away")
    home = _event_team_name(event, "home")
    totals: list[dict[str, Any]] = []
    for book, markets in bookmakers.items():
        if not isinstance(markets, list):
            continue
        for market in markets:
            if not isinstance(market, dict):
                continue
            market_name = normalize_name(market.get("name") or market.get("label") or market.get("market"))
            if "total" not in market_name or "player" in market_name:
                continue
            offers = market.get("odds") or market.get("outcomes") or market.get("selections") or []
            if isinstance(offers, dict):
                offers = [offers]
            for offer in offers if isinstance(offers, list) else []:
                if not isinstance(offer, dict):
                    continue
                line = safe_float(offer.get("hdp") or offer.get("line") or offer.get("handicap") or offer.get("point"))
                over_raw = offer.get("over") or offer.get("overOdds") or offer.get("over_odds")
                under_raw = offer.get("under") or offer.get("underOdds") or offer.get("under_odds")
                over = normalize_odds(over_raw)
                under = normalize_odds(under_raw)
                if line > 0 and (over or under):
                    totals.append({
                        "event_id": event_id,
                        "away": away,
                        "home": home,
                        "book": str(book),
                        "line": line,
                        "over_odds": over or None,
                        "under_odds": under or None,
                    })
    return totals


def _best_game_totals(raw_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    offers: list[dict[str, Any]] = []
    for item in raw_events:
        event = item.get("event") if isinstance(item, dict) else None
        payload = item.get("odds") if isinstance(item, dict) else None
        if isinstance(event, dict):
            offers.extend(_parse_total_market(payload, event, str(event.get("id") or "")))
    best: dict[tuple[str, str, str], dict[str, Any]] = {}
    for offer in offers:
        key = (str(offer.get("away")), str(offer.get("home")), str(offer.get("book")))
        existing = best.get(key)
        if existing is None or str(offer.get("book")).lower() == "draftkings":
            best[key] = offer
    return list(best.values())


def _attach_game_totals(board: dict[str, Any], totals: list[dict[str, Any]]) -> None:
    board["game_totals"] = totals
    for meta in board.get("games_meta", []) or []:
        away = normalize_team(meta.get("away_team_name"))
        home = normalize_team(meta.get("home_team_name"))
        matches = [offer for offer in totals if {offer.get("away"), offer.get("home")} == {away, home}]
        if not matches:
            continue
        draftkings = next((offer for offer in matches if str(offer.get("book")).lower() == "draftkings"), matches[0])
        meta["sportsbook_total"] = draftkings.get("line")
        meta["over_odds"] = draftkings.get("over_odds")
        meta["under_odds"] = draftkings.get("under_odds")
        meta["total_book"] = draftkings.get("book")


def _dedupe_records(records: list[OddsRecord]) -> list[OddsRecord]:
    best: dict[tuple[str, str, str], OddsRecord] = {}
    for record in records:
        key = (normalize_name(record.player_name), record.book.lower(), record.game_id)
        existing = best.get(key)
        if existing is None or american_to_decimal(record.american_odds) > american_to_decimal(existing.american_odds):
            best[key] = record
    return list(best.values())


def _dedupe_prop_records(records: list[PlayerPropRecord]) -> list[PlayerPropRecord]:
    best: dict[tuple[str, str, str, str, str, str], PlayerPropRecord] = {}
    for record in records:
        line_key = "" if record.line is None else f"{record.line:g}"
        key = (
            normalize_name(record.player_name),
            normalize_name(record.market),
            line_key,
            normalize_name(record.side),
            record.book.lower(),
            record.game_id,
        )
        existing = best.get(key)
        if existing is None or american_to_decimal(record.american_odds) > american_to_decimal(existing.american_odds):
            best[key] = record
    return list(best.values())


def _hr_records_from_props(records: list[PlayerPropRecord]) -> list[OddsRecord]:
    return _dedupe_records(
        [
            OddsRecord(
                slate_date=record.slate_date,
                player_name=record.player_name,
                team=record.team,
                book=record.book,
                american_odds=record.american_odds,
                player_id=record.player_id,
                game_id=record.game_id,
            )
            for record in records
            if record.market == "Home Run"
            and normalize_name(record.side) in {"over", "yes"}
            and (record.line is None or record.line <= 0.5)
        ]
    )


def _manual_hr_props(records: list[OddsRecord]) -> list[PlayerPropRecord]:
    return [
        PlayerPropRecord(
            slate_date=record.slate_date,
            player_name=record.player_name,
            market="Home Run",
            line=0.5,
            side="Over",
            book=record.book,
            american_odds=record.american_odds,
            player_id=record.player_id,
            team=record.team,
            game_id=record.game_id,
            source="manual",
        )
        for record in records
    ]


def _best_prop_board_records(records: list[PlayerPropRecord]) -> list[PlayerPropRecord]:
    """Keep the best available sportsbook price for each player/market/side."""
    best: dict[tuple[str, str, str, str, str], PlayerPropRecord] = {}
    for record in records:
        line_key = "" if record.line is None else f"{record.line:g}"
        key = (
            normalize_name(record.player_name),
            normalize_name(record.market),
            line_key,
            normalize_name(record.side),
            record.game_id,
        )
        existing = best.get(key)
        if existing is None or american_to_decimal(record.american_odds) > american_to_decimal(existing.american_odds):
            best[key] = record
    return list(best.values())


def _cached_live_result(target_date: str) -> tuple[list[OddsRecord], list[PlayerPropRecord], dict[str, Any]] | None:
    """Return a recent cached odds result.

    Successful pulls are reused for one hour. Empty or failed pulls are reused
    for only five minutes so the scheduled snapshot retries quickly.
    """
    if not LIVE_CACHE_FILE.exists():
        return None
    try:
        cached = json.loads(LIVE_CACHE_FILE.read_text(encoding="utf-8"))
        if int(cached.get("schema_version") or 0) != ODDS_CACHE_SCHEMA:
            return None
        if str(cached.get("target_date") or "") != target_date:
            return None
        updated_at = datetime.fromisoformat(str(cached.get("updated_at") or "").replace("Z", "+00:00"))
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - updated_at.astimezone(timezone.utc)).total_seconds()
        raw_records = cached.get("records") or []
        raw_props = cached.get("prop_records") or []
        max_age = 3600 if raw_records or raw_props else 300
        if age < 0 or age > max_age:
            return None
        records = [OddsRecord(**item) for item in raw_records if isinstance(item, dict)]
        prop_records = [PlayerPropRecord(**item) for item in raw_props if isinstance(item, dict)]
        # Upgrade old HR-only caches without forcing a failed first load.
        if not prop_records and records:
            prop_records = _manual_hr_props(records)
        status = cached.get("status") or {}
        if not isinstance(status, dict):
            status = {}
        status = dict(status)
        status["from_cache"] = True
        status["raw_cache"] = str(LIVE_CACHE_FILE)
        status.setdefault("prop_offers", len(prop_records))
        return records, prop_records, status
    except Exception:
        return None


def clear_live_odds_cache() -> None:
    try:
        LIVE_CACHE_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def fetch_live_odds(target_date: str) -> tuple[list[OddsRecord], list[PlayerPropRecord], dict[str, Any]]:
    api_key = os.getenv("ODDS_API_IO_KEY", "").strip()
    if not api_key:
        return [], [], {
            "connected": False,
            "status": "API key not configured",
            "events": 0,
            "offers": 0,
            "prop_offers": 0,
        }

    cached = _cached_live_result(target_date)
    if cached is not None:
        return cached

    try:
        events = fetch_mlb_events(api_key, target_date)
        all_records: list[OddsRecord] = []
        all_props: list[PlayerPropRecord] = []
        raw_events: list[dict[str, Any]] = []
        skipped_events: list[dict[str, Any]] = []

        def fetch_event(event: dict[str, Any]) -> tuple[dict[str, Any], Any | None, dict[str, Any] | None]:
            event_id = str(event.get("id") or "")
            if not event_id:
                return event, None, {"event_id": "", "status_code": None, "message": "missing event id"}
            try:
                params: dict[str, Any] = {"apiKey": api_key, "eventId": event_id}
                if API_BOOKMAKERS:
                    params["bookmakers"] = API_BOOKMAKERS
                return event, _api_get("odds", params), None
            except requests.HTTPError as exc:
                response = exc.response
                return event, None, {
                    "event_id": event_id,
                    "status_code": response.status_code if response is not None else None,
                    "message": (response.text[:300] if response is not None else str(exc)),
                }

        with ThreadPoolExecutor(max_workers=min(8, max(1, len(events)))) as executor:
            futures = [executor.submit(fetch_event, event) for event in events]
            for future in as_completed(futures):
                event, payload, skipped = future.result()
                if skipped:
                    skipped_events.append(skipped)
                    continue
                event_id = str(event.get("id") or "")
                raw_events.append({"event": event, "odds": payload})

                parsed_props = _parse_odds_api_io_all_player_props(
                    payload,
                    target_date=target_date,
                    event_id=event_id,
                )
                parsed_props.extend(
                    _walk_player_prop_offers(
                        payload,
                        target_date=target_date,
                        event_id=event_id,
                    )
                )
                parsed_props = _dedupe_prop_records(parsed_props)
                all_props.extend(parsed_props)

                hr_records = _hr_records_from_props(parsed_props)
                if not hr_records:
                    # Backwards-compatible fallback for unusual HR-only payloads.
                    hr_records = _parse_odds_api_io_player_props(
                        payload,
                        target_date=target_date,
                        event_id=event_id,
                    )
                    if not hr_records:
                        hr_records = _walk_offers(
                            payload,
                            target_date=target_date,
                            event_id=event_id,
                        )
                all_records.extend(hr_records)

        records = _dedupe_records(all_records)
        prop_records = _dedupe_prop_records(all_props)
        game_totals = _best_game_totals(raw_events)
        markets = sorted({record.market for record in prop_records})

        if prop_records:
            status_text = f"Loaded {len(prop_records)} live player-prop offer(s) across {len(markets)} market(s)"
        elif events and skipped_events:
            status_text = (
                f"Checked {len(events)} upcoming MLB game(s); "
                f"{len(skipped_events)} odds request(s) failed and no player props were returned"
            )
        elif events:
            status_text = "Upcoming MLB games found, but the selected books returned no supported player props"
        else:
            status_text = "No MLB events found for this slate"

        status_payload = {
            "connected": True,
            "status": status_text,
            "events": len(events),
            "offers": len(records),
            "prop_offers": len(prop_records),
            "markets": markets,
            "skipped_events": len(skipped_events),
            "raw_cache": str(LIVE_CACHE_FILE),
            "from_cache": False,
            "game_totals": len(game_totals),
        }
        LIVE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        LIVE_CACHE_FILE.write_text(
            json.dumps(
                {
                    "schema_version": ODDS_CACHE_SCHEMA,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "target_date": target_date,
                    "records": [asdict(record) for record in records],
                    "prop_records": [asdict(record) for record in prop_records],
                    "status": status_payload,
                    "events": raw_events,
                    "game_totals": game_totals,
                    "skipped_events": skipped_events,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return records, prop_records, status_payload
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else ""
        return [], [], {
            "connected": False,
            "status": f"Odds API HTTP error {status_code}",
            "events": 0,
            "offers": 0,
            "prop_offers": 0,
        }
    except Exception as exc:
        return [], [], {
            "connected": False,
            "status": f"Odds API error: {exc}",
            "events": 0,
            "offers": 0,
            "prop_offers": 0,
        }


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


def _prop_subjects(board: dict[str, Any]) -> dict[str, dict[str, Any]]:
    subjects: dict[str, dict[str, Any]] = {}
    for player in board.get("rankings", []) or []:
        name = str(player.get("player_name") or "").strip()
        if not name:
            continue
        subjects[normalize_name(name)] = {
            "player_id": safe_int(player.get("player_id")),
            "team": str(player.get("team_name") or "").upper(),
            "game_id": str(player.get("game_id") or player.get("mlb_game_pk") or ""),
            "probability": player.get("probability"),
            "score": player.get("dinger_score"),
            "kind": "hitter",
        }

    for game in board.get("games_meta", []) or []:
        for side in ("home", "away"):
            name = str(game.get(f"{side}_probable_pitcher") or "").strip()
            if not name:
                continue
            subjects.setdefault(
                normalize_name(name),
                {
                    "player_id": safe_int(game.get(f"{side}_probable_pitcher_id")),
                    "team": str(game.get(f"{side}_team_name") or "").upper(),
                    "game_id": str(game.get("mlb_game_pk") or game.get("game_id") or ""),
                    "probability": None,
                    "score": None,
                    "kind": "pitcher",
                },
            )
    return subjects


def _build_board_props(board: dict[str, Any], records: list[PlayerPropRecord]) -> list[dict[str, Any]]:
    subjects = _prop_subjects(board)
    all_records = _dedupe_prop_records(records)
    best_records = _best_prop_board_records(all_records)
    offers_by_key: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = {}

    for record in all_records:
        line_key = "" if record.line is None else f"{record.line:g}"
        key = (
            normalize_name(record.player_name),
            normalize_name(record.market),
            line_key,
            normalize_name(record.side),
            record.game_id,
        )
        offers_by_key.setdefault(key, []).append(
            {
                "sportsbook": record.book,
                "odds": record.american_odds,
                "decimalOdds": american_to_decimal(record.american_odds),
                "impliedProbability": implied_probability(record.american_odds),
                "source": record.source,
            }
        )

    props: list[dict[str, Any]] = []
    for record in sorted(
        best_records,
        key=lambda row: (
            row.market,
            normalize_name(row.player_name),
            row.line if row.line is not None else -1,
            row.side,
        ),
    ):
        subject = subjects.get(normalize_name(record.player_name), {})
        line_key = "" if record.line is None else f"{record.line:g}"
        key = (
            normalize_name(record.player_name),
            normalize_name(record.market),
            line_key,
            normalize_name(record.side),
            record.game_id,
        )
        model_probability = None
        model_score = None
        if record.market == "Home Run" and normalize_name(record.side) in {"over", "yes"}:
            model_probability = subject.get("probability")
            model_score = subject.get("score")

        player_id = record.player_id or subject.get("player_id")
        team = record.team or subject.get("team") or ""
        identity = "|".join(
            [
                str(record.game_id),
                str(player_id or normalize_name(record.player_name)),
                normalize_name(record.market),
                line_key,
                normalize_name(record.side),
            ]
        )
        props.append(
            {
                "id": identity,
                "playerId": player_id,
                "playerName": record.player_name,
                "team": team,
                "market": record.market,
                "line": record.line,
                "side": record.side,
                "odds": record.american_odds,
                "americanOdds": record.american_odds,
                "sportsbook": record.book,
                "probability": model_probability,
                "score": model_score,
                "gameId": record.game_id or subject.get("game_id") or None,
                "bookImpliedProbability": implied_probability(record.american_odds),
                "offers": sorted(
                    offers_by_key.get(key, []),
                    key=lambda offer: american_to_decimal(offer.get("odds")),
                    reverse=True,
                ),
            }
        )
    return props


def enrich_board_odds(board: dict[str, Any], path: Path = ODDS_FILE) -> dict[str, Any]:
    rankings = board.get("rankings", []) or []
    target_date = str(board.get("date") or date.today().isoformat())

    live_records, live_props, live_status = fetch_live_odds(target_date)
    try:
        cached_payload = json.loads(LIVE_CACHE_FILE.read_text(encoding="utf-8")) if LIVE_CACHE_FILE.exists() else {}
        game_totals = cached_payload.get("game_totals") if isinstance(cached_payload.get("game_totals"), list) else []
    except (OSError, json.JSONDecodeError):
        game_totals = []
    _attach_game_totals(board, game_totals)

    manual_records = load_odds(path, target_date)
    # Manual CSV rows remain an HR fallback. Live provider rows can now carry all
    # supported player markets into the top-level snapshot props list.
    records = _dedupe_records(live_records + manual_records)
    prop_records = _dedupe_prop_records(live_props + _manual_hr_props(manual_records))

    matched_players = 0
    unmatched_records = set(range(len(records)))
    books: set[str] = {record.book for record in prop_records if record.book}

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

    board_props = _build_board_props(board, prop_records)
    board["props"] = board_props
    board["pricedProps"] = sum(1 for prop in board_props if prop.get("odds") is not None)
    board["priced_props"] = board["pricedProps"]

    positive_edges = [player for player in rankings if player.get("edge_pct") is not None and float(player["edge_pct"]) > 0]
    source = "Odds-API.io Live" if live_props or live_records else ("Manual CSV" if manual_records else "Not connected")
    board["odds_summary"] = {
        "source": source,
        "file": str(path),
        "records": len(records),
        "live_records": len(live_records),
        "live_prop_records": len(live_props),
        "prop_records": len(prop_records),
        "priced_props": len(board_props),
        "markets": sorted({prop.get("market") for prop in board_props if prop.get("market")}),
        "manual_records": len(manual_records),
        "matched_players": matched_players,
        "unmatched_records": len(unmatched_records),
        "books": sorted(books),
        "positive_edges": len(positive_edges),
        "connected": bool(records) or bool(prop_records) or bool(live_status.get("connected")),
        "api_status": live_status.get("status", ""),
        "api_events": live_status.get("events", 0),
        "raw_cache": live_status.get("raw_cache", ""),
    }
    board.setdefault("data_sources", {})["Sportsbook Odds"] = (
        "live" if live_props or live_records else ("manual" if manual_records else "unavailable")
    )
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
