from __future__ import annotations

import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests

BASE_DIR = Path(__file__).resolve().parents[1]
STADIUMS_FILE = BASE_DIR / "data" / "stadiums.json"
CACHE_FILE = BASE_DIR / "data" / "cache" / "weather_cache.json"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
CACHE_TTL_MINUTES = 35


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


def normalize_team_key(team: str | None) -> str:
    raw = " ".join(str(team or "").replace(".", " ").upper().split())
    return TEAM_ALIASES.get(raw, raw)

HOURLY_FIELDS = (
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
    # A neutral evening fallback keeps date matching predictable when the feed omits time.
    return datetime.fromisoformat(f"{slate_date}T19:00:00").replace(tzinfo=tz)


def _cache_key(stadium: dict[str, Any], local_game_time: datetime) -> str:
    return f"{stadium.get('team')}|{local_game_time.strftime('%Y-%m-%dT%H')}"


def _cached_weather(key: str) -> dict[str, Any] | None:
    cache = _load_json(CACHE_FILE, {})
    item = cache.get(key) if isinstance(cache, dict) else None
    if not isinstance(item, dict):
        return None
    try:
        fetched_at = datetime.fromisoformat(str(item.get("fetched_at", "")).replace("Z", "+00:00"))
    except ValueError:
        return None
    if datetime.now(timezone.utc) - fetched_at > timedelta(minutes=CACHE_TTL_MINUTES):
        return None
    payload = item.get("payload")
    return payload if isinstance(payload, dict) else None


def _put_cache(key: str, payload: dict[str, Any]) -> None:
    cache = _load_json(CACHE_FILE, {})
    if not isinstance(cache, dict):
        cache = {}
    cache[key] = {"fetched_at": datetime.now(timezone.utc).isoformat(), "payload": payload}
    # Prevent the local cache from growing forever.
    if len(cache) > 250:
        cache = dict(list(cache.items())[-200:])
    _save_json(CACHE_FILE, cache)


def _weather_description(code: Any) -> str:
    try:
        value = int(code)
    except (TypeError, ValueError):
        return "Conditions unavailable"
    if value == 0:
        return "Clear"
    if value in {1, 2, 3}:
        return "Partly cloudy"
    if value in {45, 48}:
        return "Fog"
    if value in {51, 53, 55, 56, 57}:
        return "Drizzle"
    if value in {61, 63, 65, 66, 67, 80, 81, 82}:
        return "Rain"
    if value in {71, 73, 75, 77, 85, 86}:
        return "Snow"
    if value in {95, 96, 99}:
        return "Thunderstorms"
    return "Mixed conditions"


def _angle_difference(a: float, b: float) -> float:
    return abs((a - b + 180) % 360 - 180)


def wind_field_effect(wind_from_degrees: Any, center_field_bearing: Any) -> tuple[str, float]:
    try:
        # Weather APIs report where wind comes FROM. Add 180 to get where it blows TO.
        wind_to = (float(wind_from_degrees) + 180.0) % 360.0
        center = float(center_field_bearing) % 360.0
    except (TypeError, ValueError):
        return "unknown", 90.0
    difference = _angle_difference(wind_to, center)
    if difference <= 55:
        return "out", difference
    if difference >= 125:
        return "in", difference
    return "cross", difference


def weather_impact(temperature_f: Any, wind_speed_mph: Any, field_effect: str, rain_probability: Any, humidity_pct: Any) -> tuple[float, str, list[str]]:
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
    if score >= 7:
        grade = "A+"
    elif score >= 5:
        grade = "A"
    elif score >= 3:
        grade = "B+"
    elif score >= 1:
        grade = "B"
    elif score > -1:
        grade = "C"
    elif score > -3:
        grade = "D"
    else:
        grade = "F"
    return score, grade, reasons[:4]


def _fetch_hourly(stadium: dict[str, Any], local_game_time: datetime) -> dict[str, Any]:
    game_date = local_game_time.date()
    today = date.today()
    endpoint = ARCHIVE_URL if game_date < today - timedelta(days=5) else FORECAST_URL
    params = {
        "latitude": stadium["latitude"],
        "longitude": stadium["longitude"],
        "hourly": ",".join(HOURLY_FIELDS),
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": stadium["timezone"],
        "start_date": game_date.isoformat(),
        "end_date": game_date.isoformat(),
    }
    headers = {"User-Agent": "DuggansDingers/14.0 (+Streamlit)"}
    response = requests.get(endpoint, params=params, headers=headers, timeout=20)
    if response.status_code >= 400:
        # Some Open-Meteo endpoints can reject one optional hourly field. Retry
        # with the core forecast set instead of dropping the whole game.
        core_fields = (
            "temperature_2m", "apparent_temperature", "relative_humidity_2m",
            "dew_point_2m", "precipitation", "cloud_cover", "visibility",
            "surface_pressure", "wind_speed_10m", "wind_direction_10m",
            "wind_gusts_10m", "weather_code",
        )
        retry_params = dict(params)
        retry_params["hourly"] = ",".join(core_fields)
        response = requests.get(endpoint, params=retry_params, headers=headers, timeout=20)
    response.raise_for_status()
    payload = response.json()
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    if not times:
        raise RuntimeError("Open-Meteo returned no hourly forecast for this game date.")

    parsed_times = [datetime.fromisoformat(str(item)).replace(tzinfo=ZoneInfo(stadium["timezone"])) for item in times]
    index = min(range(len(parsed_times)), key=lambda i: abs((parsed_times[i] - local_game_time).total_seconds()))

    def value(field: str, default: Any = None) -> Any:
        values = hourly.get(field) or []
        return values[index] if index < len(values) else default

    field_effect, angle = wind_field_effect(value("wind_direction_10m"), stadium.get("center_field_bearing"))
    impact, grade, reasons = weather_impact(
        value("temperature_2m"), value("wind_speed_10m"), field_effect,
        value("precipitation_probability"), value("relative_humidity_2m"),
    )
    return {
        "weather_available": True,
        "weather_source": "Open-Meteo",
        "weather_time_local": parsed_times[index].isoformat(),
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


def get_game_weather(team: str | None, venue_name: str | None, game_time: Any, slate_date: str) -> dict[str, Any]:
    stadium = find_stadium(team, venue_name)
    if not stadium:
        return {"weather_available": False, "weather_error": "Stadium location not found"}
    local_game_time = _parse_game_time(game_time, stadium["timezone"], slate_date)
    key = _cache_key(stadium, local_game_time)
    cached = _cached_weather(key)
    if cached:
        return cached
    try:
        payload = _fetch_hourly(stadium, local_game_time)
    except (requests.RequestException, RuntimeError, ValueError) as exc:
        return {
            "weather_available": False,
            "weather_error": str(exc),
            "stadium_name": stadium.get("name"),
            "roof_type": stadium.get("roof", "outdoor"),
            "stadium_timezone": stadium.get("timezone"),
        }
    _put_cache(key, payload)
    return payload


def enrich_board_weather(board: dict[str, Any]) -> dict[str, Any]:
    rankings = board.get("rankings", []) or []
    game_meta = board.get("games_meta", []) or []
    slate_date = str(board.get("date") or date.today().isoformat())
    game_weather: dict[str, dict[str, Any]] = {}
    meta_by_game = {
        str(meta.get("game_id")): meta
        for meta in game_meta
        if meta.get("game_id") is not None
    }

    # Always use the HOME team's stadium for each game. The previous version
    # could pick an away hitter first and therefore look up the wrong ballpark.
    for meta in game_meta:
        game_key = str(meta.get("game_id") or "")
        if not game_key:
            continue
        game_weather[game_key] = get_game_weather(
            str(meta.get("home_team_name") or ""),
            str(meta.get("venue_name") or ""),
            meta.get("game_time"),
            slate_date,
        )
        meta.update(game_weather[game_key])

    for player in rankings:
        game_key = str(player.get("game_id") or f"{player.get('team_name')}|{slate_date}")
        if game_key not in game_weather:
            meta = meta_by_game.get(game_key, {})
            home_team = meta.get("home_team_name") or player.get("home_team_name") or player.get("team_name")
            venue = meta.get("venue_name") or player.get("venue_name")
            game_time = meta.get("game_time") or player.get("game_time")
            game_weather[game_key] = get_game_weather(
                str(home_team or ""),
                str(venue or ""),
                game_time,
                slate_date,
            )
        player.update(game_weather[game_key])

    available = sum(1 for item in game_weather.values() if item.get("weather_available"))
    favorable = sum(
        1 for item in game_weather.values()
        if item.get("weather_available") and float(item.get("weather_impact") or 0) >= 3
    )
    errors = sorted({
        str(item.get("weather_error"))
        for item in game_weather.values()
        if item.get("weather_error")
    })
    board["weather_summary"] = {
        "games_available": available,
        "games_total": len(game_weather),
        "favorable_games": favorable,
        "unavailable_games": max(0, len(game_weather) - available),
        "errors": errors,
    }
    board.setdefault("data_sources", {})["Weather"] = "live" if available else "unavailable"
    return board
