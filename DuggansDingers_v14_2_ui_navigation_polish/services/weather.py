from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests

BASE_DIR = Path(__file__).resolve().parents[1]
STADIUMS_FILE = BASE_DIR / "data" / "stadiums.json"
CACHE_FILE = BASE_DIR / "data" / "cache" / "weather_batch_cache.json"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
SUCCESS_TTL_MINUTES = 30
FAILURE_BACKOFF_MINUTES = 15

# One compact hourly request supplies everything shown in the dashboard.
FORECAST_FIELDS = (
    "temperature_2m",
    "apparent_temperature",
    "relative_humidity_2m",
    "dew_point_2m",
    "precipitation_probability",
    "precipitation",
    "cloud_cover",
    "visibility",
    "surface_pressure",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "weather_code",
)
ARCHIVE_FIELDS = tuple(field for field in FORECAST_FIELDS if field != "precipitation_probability")

TEAM_ALIASES = {
    "ARIZONA DIAMONDBACKS": "ARI", "DIAMONDBACKS": "ARI",
    "ATLANTA BRAVES": "ATL", "BRAVES": "ATL",
    "BALTIMORE ORIOLES": "BAL", "ORIOLES": "BAL",
    "BOSTON RED SOX": "BOS", "RED SOX": "BOS",
    "CHICAGO CUBS": "CHC", "CUBS": "CHC",
    "CHICAGO WHITE SOX": "CWS", "WHITE SOX": "CWS",
    "CINCINNATI REDS": "CIN", "REDS": "CIN",
    "CLEVELAND GUARDIANS": "CLE", "GUARDIANS": "CLE",
    "COLORADO ROCKIES": "COL", "ROCKIES": "COL",
    "DETROIT TIGERS": "DET", "TIGERS": "DET",
    "HOUSTON ASTROS": "HOU", "ASTROS": "HOU",
    "KANSAS CITY ROYALS": "KC", "ROYALS": "KC", "KCR": "KC",
    "LOS ANGELES ANGELS": "LAA", "ANGELS": "LAA",
    "LOS ANGELES DODGERS": "LAD", "DODGERS": "LAD",
    "MIAMI MARLINS": "MIA", "MARLINS": "MIA",
    "MILWAUKEE BREWERS": "MIL", "BREWERS": "MIL",
    "MINNESOTA TWINS": "MIN", "TWINS": "MIN",
    "NEW YORK METS": "NYM", "METS": "NYM",
    "NEW YORK YANKEES": "NYY", "YANKEES": "NYY",
    "ATHLETICS": "ATH", "OAKLAND ATHLETICS": "ATH", "SACRAMENTO ATHLETICS": "ATH",
    "PHILADELPHIA PHILLIES": "PHI", "PHILLIES": "PHI",
    "PITTSBURGH PIRATES": "PIT", "PIRATES": "PIT",
    "SAN DIEGO PADRES": "SD", "PADRES": "SD", "SDP": "SD",
    "SAN FRANCISCO GIANTS": "SF", "GIANTS": "SF", "SFG": "SF",
    "SEATTLE MARINERS": "SEA", "MARINERS": "SEA",
    "ST. LOUIS CARDINALS": "STL", "ST LOUIS CARDINALS": "STL", "CARDINALS": "STL",
    "TAMPA BAY RAYS": "TB", "RAYS": "TB", "TBR": "TB",
    "TEXAS RANGERS": "TEX", "RANGERS": "TEX",
    "TORONTO BLUE JAYS": "TOR", "BLUE JAYS": "TOR",
    "WASHINGTON NATIONALS": "WSH", "NATIONALS": "WSH", "WSN": "WSH",
}


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return default


def _save_json(path: Path, payload: Any) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass


def _parse_timestamp(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def normalize_team_key(team: str | None) -> str:
    raw = " ".join(str(team or "").replace(".", " ").upper().split())
    return TEAM_ALIASES.get(raw, raw)


def _stadiums() -> dict[str, dict[str, Any]]:
    payload = _load_json(STADIUMS_FILE, {})
    return payload if isinstance(payload, dict) else {}


def find_stadium(team: str | None, venue_name: str | None = None) -> dict[str, Any] | None:
    stadiums = _stadiums()
    normalized_venue = " ".join(str(venue_name or "").strip().lower().split())
    if normalized_venue:
        for abbreviation, stadium in stadiums.items():
            names = [stadium.get("name"), *(stadium.get("aliases") or [])]
            normalized_names = [" ".join(str(name or "").strip().lower().split()) for name in names]
            if normalized_venue in normalized_names or any(
                normalized_venue in name or name in normalized_venue
                for name in normalized_names if name
            ):
                return {"team": abbreviation, **stadium}
    key = normalize_team_key(team)
    stadium = stadiums.get(key)
    return {"team": key, **stadium} if stadium else None


def _parse_game_time(value: Any, stadium_timezone: str, slate_date: str) -> datetime:
    tz = ZoneInfo(stadium_timezone)
    raw = str(value or "").strip()
    if raw:
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=tz)
            return parsed.astimezone(tz)
        except ValueError:
            pass
        for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(raw, pattern).replace(tzinfo=tz)
            except ValueError:
                continue
    return datetime.fromisoformat(f"{slate_date}T19:00:00").replace(tzinfo=tz)


def _weather_description(code: Any) -> str:
    try:
        value = int(code)
    except (TypeError, ValueError):
        return "Conditions unavailable"
    if value == 0: return "Clear"
    if value in {1, 2, 3}: return "Partly cloudy"
    if value in {45, 48}: return "Fog"
    if value in {51, 53, 55, 56, 57}: return "Drizzle"
    if value in {61, 63, 65, 66, 67, 80, 81, 82}: return "Rain"
    if value in {71, 73, 75, 77, 85, 86}: return "Snow"
    if value in {95, 96, 99}: return "Thunderstorms"
    return "Mixed conditions"


def _angle_difference(a: float, b: float) -> float:
    return abs((a - b + 180) % 360 - 180)


def wind_field_effect(wind_from_degrees: Any, center_field_bearing: Any) -> tuple[str, float]:
    try:
        wind_to = (float(wind_from_degrees) + 180.0) % 360.0
        center = float(center_field_bearing) % 360.0
    except (TypeError, ValueError):
        return "unknown", 90.0
    difference = _angle_difference(wind_to, center)
    if difference <= 55: return "out", difference
    if difference >= 125: return "in", difference
    return "cross", difference


def weather_impact(
    temperature_f: Any,
    wind_speed_mph: Any,
    field_effect: str,
    rain_probability: Any,
    humidity_pct: Any,
) -> tuple[float, str, list[str]]:
    temp = float(temperature_f or 0)
    wind = max(0.0, float(wind_speed_mph or 0))
    rain = max(0.0, float(rain_probability or 0))
    humidity = max(0.0, float(humidity_pct or 0))
    score = 0.0
    reasons: list[str] = []

    if temp >= 90:
        score += 4.5; reasons.append(f"Hot hitting weather at {temp:.0f}°F")
    elif temp >= 80:
        score += 3.0; reasons.append(f"Warm game-time air at {temp:.0f}°F")
    elif temp >= 70:
        score += 1.5; reasons.append(f"Mild game-time temperature at {temp:.0f}°F")
    elif temp and temp < 55:
        score -= 3.0; reasons.append(f"Cold air at {temp:.0f}°F")

    wind_adjustment = min(wind * 0.36, 6.5)
    if field_effect == "out":
        score += wind_adjustment; reasons.append(f"{wind:.0f} mph wind blowing out")
    elif field_effect == "in":
        score -= wind_adjustment; reasons.append(f"{wind:.0f} mph wind blowing in")
    elif field_effect == "cross" and wind >= 10:
        reasons.append(f"{wind:.0f} mph crosswind")

    if rain >= 50:
        score -= 2.0; reasons.append(f"{rain:.0f}% precipitation risk")
    elif rain <= 20:
        reasons.append("Low precipitation risk")
    if humidity >= 85:
        score -= 0.7

    score = round(max(-10.0, min(10.0, score)), 1)
    if score >= 7: grade = "A+"
    elif score >= 5: grade = "A"
    elif score >= 3: grade = "B+"
    elif score >= 1: grade = "B"
    elif score > -1: grade = "C"
    elif score > -3: grade = "D"
    else: grade = "F"
    return score, grade, reasons[:4]


def _group_endpoint(target_utc: datetime) -> str:
    return ARCHIVE_URL if target_utc.date() < date.today() - timedelta(days=5) else FORECAST_URL


def _batch_cache_key(endpoint: str, start_date: str, end_date: str, stadiums: list[dict[str, Any]]) -> str:
    teams = ",".join(sorted(str(stadium.get("team")) for stadium in stadiums))
    endpoint_name = "archive" if endpoint == ARCHIVE_URL else "forecast"
    return f"{endpoint_name}|{start_date}|{end_date}|{teams}"


def _read_batch_cache(key: str) -> tuple[dict[str, Any] | None, bool, str | None]:
    cache = _load_json(CACHE_FILE, {})
    entry = cache.get(key) if isinstance(cache, dict) else None
    if not isinstance(entry, dict):
        return None, False, None

    now = datetime.now(timezone.utc)
    success_at = _parse_timestamp(entry.get("success_fetched_at"))
    failure_at = _parse_timestamp(entry.get("failure_fetched_at"))
    payload = entry.get("payload") if isinstance(entry.get("payload"), dict) else None

    if payload and success_at and now - success_at <= timedelta(minutes=SUCCESS_TTL_MINUTES):
        return payload, False, None

    failure_error = str(entry.get("failure_error") or "") or None
    if failure_at and now - failure_at <= timedelta(minutes=FAILURE_BACKOFF_MINUTES):
        # During a provider backoff, use the last successful response instead of
        # repeatedly hitting Open-Meteo and extending the rate limit.
        return payload, bool(payload), failure_error

    return None, False, None


def _write_batch_success(key: str, payload: dict[str, Any]) -> None:
    cache = _load_json(CACHE_FILE, {})
    if not isinstance(cache, dict):
        cache = {}
    cache[key] = {
        "success_fetched_at": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }
    if len(cache) > 80:
        cache = dict(list(cache.items())[-60:])
    _save_json(CACHE_FILE, cache)


def _write_batch_failure(key: str, error: str) -> dict[str, Any] | None:
    cache = _load_json(CACHE_FILE, {})
    if not isinstance(cache, dict):
        cache = {}
    entry = cache.get(key) if isinstance(cache.get(key), dict) else {}
    entry["failure_fetched_at"] = datetime.now(timezone.utc).isoformat()
    entry["failure_error"] = error
    cache[key] = entry
    _save_json(CACHE_FILE, cache)
    payload = entry.get("payload")
    return payload if isinstance(payload, dict) else None


def _request_batch_raw(
    endpoint: str,
    stadiums: list[dict[str, Any]],
    start_date: str,
    end_date: str,
) -> tuple[dict[str, dict[str, Any]], bool, str | None]:
    """Fetch every stadium in one Open-Meteo request.

    Returns team -> raw location forecast, whether stale cache was used, and an
    optional provider warning. A 429 is never retried immediately.
    """
    unique: dict[str, dict[str, Any]] = {}
    for stadium in stadiums:
        unique[str(stadium.get("team"))] = stadium
    ordered = list(unique.values())
    key = _batch_cache_key(endpoint, start_date, end_date, ordered)

    cached, stale, warning = _read_batch_cache(key)
    if cached is not None:
        return cached, stale, warning

    fields = ARCHIVE_FIELDS if endpoint == ARCHIVE_URL else FORECAST_FIELDS
    params = {
        "latitude": ",".join(str(stadium["latitude"]) for stadium in ordered),
        "longitude": ",".join(str(stadium["longitude"]) for stadium in ordered),
        "hourly": ",".join(fields),
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        # UTC makes one multi-location request possible while still allowing
        # game-time matching for every local stadium timezone.
        "timezone": "GMT",
        "start_date": start_date,
        "end_date": end_date,
    }
    headers = {"User-Agent": "DuggansDingers/14.1 (+Streamlit)"}

    try:
        response = requests.get(endpoint, params=params, headers=headers, timeout=25)
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            suffix = f" Retry after {retry_after} seconds." if retry_after else ""
            raise RuntimeError(f"Open-Meteo rate limit reached.{suffix}")
        response.raise_for_status()
        body = response.json()
        locations = body if isinstance(body, list) else [body]
        if len(locations) != len(ordered):
            raise RuntimeError(
                f"Open-Meteo returned {len(locations)} locations for {len(ordered)} requested stadiums."
            )
        mapped = {
            str(stadium.get("team")): location
            for stadium, location in zip(ordered, locations)
            if isinstance(location, dict)
        }
        if len(mapped) != len(ordered):
            raise RuntimeError("Open-Meteo returned an incomplete multi-stadium forecast.")
    except (requests.RequestException, RuntimeError, ValueError) as exc:
        error = str(exc)
        stale_payload = _write_batch_failure(key, error)
        if stale_payload:
            return stale_payload, True, error
        raise RuntimeError(error) from exc

    _write_batch_success(key, mapped)
    return mapped, False, None


def _extract_location_weather(
    raw: dict[str, Any],
    stadium: dict[str, Any],
    local_game_time: datetime,
    *,
    stale: bool = False,
    warning: str | None = None,
) -> dict[str, Any]:
    hourly = raw.get("hourly") or {}
    times = hourly.get("time") or []
    if not times:
        raise RuntimeError("Open-Meteo returned no hourly forecast for this game date.")

    parsed_times: list[datetime] = []
    for item in times:
        parsed = datetime.fromisoformat(str(item).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        parsed_times.append(parsed.astimezone(timezone.utc))

    target_utc = local_game_time.astimezone(timezone.utc)
    index = min(range(len(parsed_times)), key=lambda i: abs((parsed_times[i] - target_utc).total_seconds()))

    def value(field: str, default: Any = None) -> Any:
        values = hourly.get(field) or []
        return values[index] if index < len(values) else default

    field_effect, angle = wind_field_effect(value("wind_direction_10m"), stadium.get("center_field_bearing"))
    impact, grade, reasons = weather_impact(
        value("temperature_2m"),
        value("wind_speed_10m"),
        field_effect,
        value("precipitation_probability", 0),
        value("relative_humidity_2m"),
    )
    local_forecast_time = parsed_times[index].astimezone(ZoneInfo(stadium["timezone"]))
    payload = {
        "weather_available": True,
        "weather_source": "Open-Meteo cached" if stale else "Open-Meteo",
        "weather_stale": stale,
        "weather_warning": warning or "",
        "weather_time_local": local_forecast_time.isoformat(),
        "temperature_f": value("temperature_2m"),
        "apparent_temperature_f": value("apparent_temperature", value("temperature_2m")),
        "humidity_pct": value("relative_humidity_2m"),
        "dew_point_f": value("dew_point_2m"),
        "precip_probability": value("precipitation_probability", 0),
        "precipitation_in": value("precipitation"),
        "cloud_cover_pct": value("cloud_cover"),
        "visibility_miles": round(float(value("visibility", 0) or 0) / 1609.344, 1),
        "surface_pressure_hpa": value("surface_pressure"),
        "wind_speed_mph": value("wind_speed_10m"),
        "wind_gust_mph": value("wind_gusts_10m"),
        "wind_direction_deg": value("wind_direction_10m"),
        "wind_field_effect": field_effect,
        "wind_alignment_difference": round(angle, 1),
        "weather_code": value("weather_code"),
        "weather_description": _weather_description(value("weather_code")),
        "weather_impact": impact,
        "weather_grade": grade,
        "weather_reasons": reasons,
        "roof_type": stadium.get("roof", "outdoor"),
        "roof_status": "unconfirmed" if stadium.get("roof") == "retractable" else "open-air",
        "stadium_name": stadium.get("name"),
        "stadium_timezone": stadium.get("timezone"),
    }
    return payload


def _resolve_context_weather(contexts: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    valid: dict[str, dict[str, Any]] = {}

    for key, context in contexts.items():
        stadium = find_stadium(context.get("home_team"), context.get("venue_name"))
        if not stadium:
            results[key] = {
                "weather_available": False,
                "weather_error": "Stadium location not found",
            }
            continue
        local_game_time = _parse_game_time(context.get("game_time"), stadium["timezone"], context["slate_date"])
        valid[key] = {
            **context,
            "stadium": stadium,
            "local_game_time": local_game_time,
            "target_utc": local_game_time.astimezone(timezone.utc),
        }

    # Group current forecasts separately from archive requests. A normal live
    # slate therefore generates exactly one Open-Meteo HTTP request.
    groups: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for key, context in valid.items():
        endpoint = _group_endpoint(context["target_utc"])
        groups.setdefault(endpoint, []).append((key, context))

    for endpoint, items in groups.items():
        min_date = min(context["target_utc"].date() for _, context in items)
        max_date = max(context["target_utc"].date() for _, context in items)
        stadiums = [context["stadium"] for _, context in items]
        try:
            raw_by_team, stale, warning = _request_batch_raw(
                endpoint,
                stadiums,
                min_date.isoformat(),
                max_date.isoformat(),
            )
        except RuntimeError as exc:
            for key, context in items:
                stadium = context["stadium"]
                results[key] = {
                    "weather_available": False,
                    "weather_error": str(exc),
                    "stadium_name": stadium.get("name"),
                    "roof_type": stadium.get("roof", "outdoor"),
                    "stadium_timezone": stadium.get("timezone"),
                }
            continue

        for key, context in items:
            stadium = context["stadium"]
            raw = raw_by_team.get(str(stadium.get("team")))
            if not raw:
                results[key] = {
                    "weather_available": False,
                    "weather_error": "No forecast returned for this stadium",
                    "stadium_name": stadium.get("name"),
                }
                continue
            try:
                results[key] = _extract_location_weather(
                    raw,
                    stadium,
                    context["local_game_time"],
                    stale=stale,
                    warning=warning,
                )
            except (RuntimeError, ValueError) as exc:
                results[key] = {
                    "weather_available": False,
                    "weather_error": str(exc),
                    "stadium_name": stadium.get("name"),
                    "roof_type": stadium.get("roof", "outdoor"),
                    "stadium_timezone": stadium.get("timezone"),
                }

    return results


def get_game_weather(team: str | None, venue_name: str | None, game_time: Any, slate_date: str) -> dict[str, Any]:
    context = {
        "single": {
            "home_team": team,
            "venue_name": venue_name,
            "game_time": game_time,
            "slate_date": slate_date,
        }
    }
    return _resolve_context_weather(context)["single"]


def enrich_board_weather(board: dict[str, Any]) -> dict[str, Any]:
    rankings = board.get("rankings", []) or []
    game_meta = board.get("games_meta", []) or []
    slate_date = str(board.get("date") or date.today().isoformat())

    meta_by_game = {
        str(meta.get("game_id")): meta
        for meta in game_meta
        if meta.get("game_id") is not None
    }
    contexts: dict[str, dict[str, Any]] = {}

    for index, meta in enumerate(game_meta):
        game_key = str(meta.get("game_id") or f"meta-{index}")
        contexts[game_key] = {
            "home_team": meta.get("home_team_name"),
            "venue_name": meta.get("venue_name"),
            "game_time": meta.get("game_time"),
            "slate_date": slate_date,
        }

    # Fallback for feeds that omit games_meta. Still deduplicates by game ID.
    for player in rankings:
        game_key = str(player.get("game_id") or f"{player.get('home_team_name') or player.get('team_name')}|{slate_date}")
        if game_key in contexts:
            continue
        meta = meta_by_game.get(game_key, {})
        contexts[game_key] = {
            "home_team": meta.get("home_team_name") or player.get("home_team_name") or player.get("team_name"),
            "venue_name": meta.get("venue_name") or player.get("venue_name"),
            "game_time": meta.get("game_time") or player.get("game_time"),
            "slate_date": slate_date,
        }

    game_weather = _resolve_context_weather(contexts)

    for index, meta in enumerate(game_meta):
        game_key = str(meta.get("game_id") or f"meta-{index}")
        if game_key in game_weather:
            meta.update(game_weather[game_key])

    for player in rankings:
        game_key = str(player.get("game_id") or f"{player.get('home_team_name') or player.get('team_name')}|{slate_date}")
        if game_key in game_weather:
            player.update(game_weather[game_key])

    available = sum(1 for item in game_weather.values() if item.get("weather_available"))
    favorable = sum(
        1 for item in game_weather.values()
        if item.get("weather_available") and float(item.get("weather_impact") or 0) >= 3
    )
    stale_games = sum(1 for item in game_weather.values() if item.get("weather_stale"))
    errors = sorted({
        str(item.get("weather_error"))
        for item in game_weather.values()
        if item.get("weather_error")
    })
    warnings = sorted({
        str(item.get("weather_warning"))
        for item in game_weather.values()
        if item.get("weather_warning")
    })
    board["weather_summary"] = {
        "games_available": available,
        "games_total": len(game_weather),
        "favorable_games": favorable,
        "unavailable_games": max(0, len(game_weather) - available),
        "stale_games": stale_games,
        "errors": errors,
        "warnings": warnings,
        "request_mode": "single batched request",
    }
    board.setdefault("data_sources", {})["Weather"] = "cached" if stale_games else ("live" if available else "unavailable")
    return board
