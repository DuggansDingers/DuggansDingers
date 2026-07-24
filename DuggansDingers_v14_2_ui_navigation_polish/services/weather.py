from __future__ import annotations

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

from services.schedule import fetch_schedule, match_meta_to_schedule, match_player_to_schedule, repair_board_games

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env", override=False)

STADIUMS_FILE = BASE_DIR / "data" / "stadiums.json"
CACHE_FILE = BASE_DIR / "data" / "cache" / "weather_multi_provider.json"
WEATHERAPI_URL = "https://api.weatherapi.com/v1/forecast.json"
VISUAL_CROSSING_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
NWS_POINTS_URL = "https://api.weather.gov/points"
SUCCESS_TTL_MINUTES = 45
STALE_TTL_HOURS = 12
FAILURE_BACKOFF_MINUTES = 10
USER_AGENT = "DuggansDingers/15.0 (MLB analytics dashboard)"

def _secret_value(*names: str) -> str:
    """Read provider keys at request time and accept common secret names."""
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    try:
        import streamlit as st
        for name in names:
            value = str(st.secrets.get(name, "") or "").strip()
            if value:
                return value
    except Exception:
        pass
    return ""


def weatherapi_key() -> str:
    return _secret_value("WEATHERAPI_KEY", "WEATHER_API_KEY", "WEATHERAPI_API_KEY")


def visual_crossing_key() -> str:
    return _secret_value("VISUAL_CROSSING_API_KEY", "VISUALCROSSING_API_KEY")

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
    "ATHLETICS": "ATH", "OAKLAND ATHLETICS": "ATH", "SACRAMENTO ATHLETICS": "ATH", "OAK": "ATH",
    "PHILADELPHIA PHILLIES": "PHI", "PHILLIES": "PHI",
    "PITTSBURGH PIRATES": "PIT", "PIRATES": "PIT",
    "SAN DIEGO PADRES": "SD", "PADRES": "SD", "SDP": "SD",
    "SAN FRANCISCO GIANTS": "SF", "GIANTS": "SF", "SFG": "SF",
    "SEATTLE MARINERS": "SEA", "MARINERS": "SEA",
    "ST LOUIS CARDINALS": "STL", "CARDINALS": "STL",
    "TAMPA BAY RAYS": "TB", "RAYS": "TB", "TBR": "TB",
    "TEXAS RANGERS": "TEX", "RANGERS": "TEX",
    "TORONTO BLUE JAYS": "TOR", "BLUE JAYS": "TOR",
    "WASHINGTON NATIONALS": "WSH", "NATIONALS": "WSH", "WSN": "WSH",
}

MLB_TEAM_ID_TO_ABBR = {
    109: "ARI", 144: "ATL", 110: "BAL", 111: "BOS", 112: "CHC", 145: "CWS",
    113: "CIN", 114: "CLE", 115: "COL", 116: "DET", 117: "HOU", 118: "KC",
    108: "LAA", 119: "LAD", 146: "MIA", 158: "MIL", 142: "MIN", 121: "NYM",
    147: "NYY", 133: "ATH", 143: "PHI", 134: "PIT", 135: "SD", 137: "SF",
    136: "SEA", 138: "STL", 139: "TB", 140: "TEX", 141: "TOR", 120: "WSH",
}


CARDINAL_DEGREES = {
    "N": 0, "NNE": 22.5, "NE": 45, "ENE": 67.5, "E": 90, "ESE": 112.5,
    "SE": 135, "SSE": 157.5, "S": 180, "SSW": 202.5, "SW": 225,
    "WSW": 247.5, "W": 270, "WNW": 292.5, "NW": 315, "NNW": 337.5,
}


def _load_json(path: Path, default: Any) -> Any:
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
                normalized_venue in name or name in normalized_venue for name in normalized_names if name
            ):
                return {"team": abbreviation, **stadium}
    key = normalize_team_key(team)
    stadium = stadiums.get(key)
    return {"team": key, **stadium} if stadium else None


def stadium_satellite_url(stadium: dict[str, Any]) -> str:
    """Return an aerial image centered on the real ballpark without another API key."""
    try:
        lat = float(stadium.get("latitude"))
        lon = float(stadium.get("longitude"))
    except (TypeError, ValueError):
        return ""
    lat_pad = 0.0042
    lon_pad = 0.0062
    bbox = f"{lon-lon_pad:.6f},{lat-lat_pad:.6f},{lon+lon_pad:.6f},{lat+lat_pad:.6f}"
    return (
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
        f"?bbox={bbox}&bboxSR=4326&size=1100,520&imageSR=4326&format=jpg&f=image"
    )


def _stadium_identity(stadium: dict[str, Any]) -> dict[str, Any]:
    return {
        "stadium_team": stadium.get("team"),
        "stadium_name": stadium.get("name"),
        "stadium_timezone": stadium.get("timezone"),
        "stadium_latitude": stadium.get("latitude"),
        "stadium_longitude": stadium.get("longitude"),
        "stadium_image_url": stadium_satellite_url(stadium),
    }


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
    return datetime.fromisoformat(f"{slate_date}T19:00:00").replace(tzinfo=tz)


def _angle_difference(a: float, b: float) -> float:
    return abs((a - b + 180) % 360 - 180)


def wind_field_effect(wind_from_degrees: Any, center_field_bearing: Any) -> tuple[str, float]:
    try:
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
        score += 4.5; reasons.append(f"Hot air at {temp:.0f}°F")
    elif temp >= 80:
        score += 3.0; reasons.append(f"Warm air at {temp:.0f}°F")
    elif temp >= 70:
        score += 1.5; reasons.append(f"Mild air at {temp:.0f}°F")
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
        reasons.append("Low rain risk")
    if humidity >= 85:
        score -= 0.7
    score = round(max(-10.0, min(10.0, score)), 1)
    grade = "A+" if score >= 7 else "A" if score >= 5 else "B+" if score >= 3 else "B" if score >= 1 else "C" if score > -1 else "D" if score > -3 else "F"
    return score, grade, reasons[:4]


def _cache_key(provider: str, stadium: dict[str, Any], game_time: datetime) -> str:
    return f"{provider}|{stadium.get('team')}|{game_time.strftime('%Y-%m-%dT%H')}"


def _cache_read(key: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    cache = _load_json(CACHE_FILE, {})
    entry = cache.get(key) if isinstance(cache, dict) else None
    if not isinstance(entry, dict):
        return None, None
    now = datetime.now(timezone.utc)
    fetched = _parse_timestamp(entry.get("fetched_at"))
    failed = _parse_timestamp(entry.get("failed_at"))
    payload = entry.get("payload") if isinstance(entry.get("payload"), dict) else None
    if payload and fetched and now - fetched <= timedelta(minutes=SUCCESS_TTL_MINUTES):
        return payload, None
    if failed and now - failed <= timedelta(minutes=FAILURE_BACKOFF_MINUTES):
        return None, payload
    return None, payload if payload and fetched and now - fetched <= timedelta(hours=STALE_TTL_HOURS) else None


def _cache_success(key: str, payload: dict[str, Any]) -> None:
    cache = _load_json(CACHE_FILE, {})
    if not isinstance(cache, dict):
        cache = {}
    cache[key] = {"fetched_at": datetime.now(timezone.utc).isoformat(), "payload": payload}
    if len(cache) > 250:
        cache = dict(list(cache.items())[-180:])
    _save_json(CACHE_FILE, cache)


def _cache_failure(key: str, error: str) -> None:
    cache = _load_json(CACHE_FILE, {})
    if not isinstance(cache, dict):
        cache = {}
    entry = cache.get(key) if isinstance(cache.get(key), dict) else {}
    entry.update({"failed_at": datetime.now(timezone.utc).isoformat(), "error": error})
    cache[key] = entry
    _save_json(CACHE_FILE, cache)


def _nearest(items: list[dict[str, Any]], game_time: datetime, time_key: str) -> dict[str, Any]:
    candidates: list[tuple[float, dict[str, Any]]] = []
    for item in items:
        raw = str(item.get(time_key) or "")
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=game_time.tzinfo)
            parsed = parsed.astimezone(game_time.tzinfo)
            candidates.append((abs((parsed - game_time).total_seconds()), item))
        except ValueError:
            continue
    if not candidates:
        raise RuntimeError("The provider returned no hourly forecast near first pitch.")
    return min(candidates, key=lambda pair: pair[0])[1]


def _weatherapi(stadium: dict[str, Any], game_time: datetime) -> dict[str, Any]:
    key = weatherapi_key()
    if not key:
        raise RuntimeError("WEATHERAPI_KEY is not configured")
    response = requests.get(
        WEATHERAPI_URL,
        params={
            "key": key,
            "q": f"{stadium['latitude']},{stadium['longitude']}",
            "dt": game_time.date().isoformat(),
            "aqi": "no",
            "alerts": "no",
        },
        headers={"User-Agent": USER_AGENT},
        timeout=25,
    )
    if response.status_code == 429:
        raise RuntimeError("WeatherAPI rate limit reached")
    response.raise_for_status()
    payload = response.json()
    days = ((payload.get("forecast") or {}).get("forecastday") or [])
    hours = (days[0].get("hour") or []) if days else []
    hour = _nearest(hours, game_time, "time")
    condition = hour.get("condition") or {}
    return {
        "provider": "WeatherAPI.com",
        "forecast_time": hour.get("time"),
        "temperature_f": hour.get("temp_f"),
        "apparent_temperature_f": hour.get("feelslike_f"),
        "humidity_pct": hour.get("humidity"),
        "dew_point_f": hour.get("dewpoint_f"),
        "precip_probability": hour.get("chance_of_rain", 0),
        "precipitation_in": hour.get("precip_in", 0),
        "cloud_cover_pct": hour.get("cloud", 0),
        "visibility_miles": hour.get("vis_miles"),
        "surface_pressure_hpa": hour.get("pressure_mb"),
        "wind_speed_mph": hour.get("wind_mph"),
        "wind_gust_mph": hour.get("gust_mph"),
        "wind_direction_deg": hour.get("wind_degree"),
        "weather_description": condition.get("text") or "Forecast",
    }


def _visual_crossing(stadium: dict[str, Any], game_time: datetime) -> dict[str, Any]:
    key = visual_crossing_key()
    if not key:
        raise RuntimeError("VISUAL_CROSSING_API_KEY is not configured")
    day = game_time.date().isoformat()
    url = f"{VISUAL_CROSSING_URL}/{stadium['latitude']},{stadium['longitude']}/{day}/{day}"
    response = requests.get(
        url,
        params={"unitGroup": "us", "include": "hours", "key": key, "contentType": "json"},
        headers={"User-Agent": USER_AGENT},
        timeout=25,
    )
    if response.status_code == 429:
        raise RuntimeError("Visual Crossing rate limit reached")
    response.raise_for_status()
    payload = response.json()
    days = payload.get("days") or []
    hours = (days[0].get("hours") or []) if days else []
    # Visual Crossing's hourly datetime is local HH:MM:SS; add the game date.
    normalized = []
    for hour in hours:
        item = dict(hour)
        item["local_time"] = f"{day}T{hour.get('datetime','00:00:00')}"
        normalized.append(item)
    hour = _nearest(normalized, game_time, "local_time")
    return {
        "provider": "Visual Crossing",
        "forecast_time": hour.get("local_time"),
        "temperature_f": hour.get("temp"),
        "apparent_temperature_f": hour.get("feelslike"),
        "humidity_pct": hour.get("humidity"),
        "dew_point_f": hour.get("dew"),
        "precip_probability": hour.get("precipprob", 0),
        "precipitation_in": hour.get("precip", 0),
        "cloud_cover_pct": hour.get("cloudcover", 0),
        "visibility_miles": hour.get("visibility"),
        "surface_pressure_hpa": hour.get("pressure"),
        "wind_speed_mph": hour.get("windspeed"),
        "wind_gust_mph": hour.get("windgust"),
        "wind_direction_deg": hour.get("winddir"),
        "weather_description": hour.get("conditions") or "Forecast",
    }


def _wind_speed_number(value: Any) -> float:
    match = re.search(r"\d+(?:\.\d+)?", str(value or ""))
    return float(match.group()) if match else 0.0


def _nws(stadium: dict[str, Any], game_time: datetime) -> dict[str, Any]:
    # api.weather.gov covers the United States. Toronto requires one of the keyed providers.
    if str(stadium.get("team")) == "TOR":
        raise RuntimeError("NWS does not cover Toronto; add WEATHERAPI_KEY for Canadian weather")
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    points = requests.get(
        f"{NWS_POINTS_URL}/{stadium['latitude']:.4f},{stadium['longitude']:.4f}",
        headers=headers,
        timeout=25,
    )
    points.raise_for_status()
    properties = points.json().get("properties") or {}
    hourly_url = properties.get("forecastHourly")
    if not hourly_url:
        raise RuntimeError("NWS returned no hourly forecast endpoint")
    forecast = requests.get(hourly_url, headers=headers, timeout=25)
    if forecast.status_code == 429:
        raise RuntimeError("NWS rate limit reached")
    forecast.raise_for_status()
    periods = ((forecast.json().get("properties") or {}).get("periods") or [])
    hour = _nearest(periods, game_time, "startTime")
    humidity = (hour.get("relativeHumidity") or {}).get("value")
    rain = (hour.get("probabilityOfPrecipitation") or {}).get("value")
    direction = str(hour.get("windDirection") or "N").upper()
    return {
        "provider": "National Weather Service",
        "forecast_time": hour.get("startTime"),
        "temperature_f": hour.get("temperature"),
        "apparent_temperature_f": hour.get("temperature"),
        "humidity_pct": humidity or 0,
        "dew_point_f": None,
        "precip_probability": rain or 0,
        "precipitation_in": None,
        "cloud_cover_pct": None,
        "visibility_miles": None,
        "surface_pressure_hpa": None,
        "wind_speed_mph": _wind_speed_number(hour.get("windSpeed")),
        "wind_gust_mph": None,
        "wind_direction_deg": CARDINAL_DEGREES.get(direction, 0),
        "weather_description": hour.get("shortForecast") or "Forecast",
    }


def _indoor_payload(stadium: dict[str, Any], game_time: datetime) -> dict[str, Any]:
    return {
        "weather_available": True,
        "weather_source": "Indoor park",
        "weather_stale": False,
        "weather_time_local": game_time.isoformat(),
        "temperature_f": 72,
        "apparent_temperature_f": 72,
        "humidity_pct": 45,
        "dew_point_f": None,
        "precip_probability": 0,
        "precipitation_in": 0,
        "cloud_cover_pct": 0,
        "visibility_miles": None,
        "surface_pressure_hpa": None,
        "wind_speed_mph": 0,
        "wind_gust_mph": 0,
        "wind_direction_deg": 0,
        "wind_field_effect": "neutral",
        "wind_alignment_difference": 0,
        "weather_description": "Climate controlled",
        "weather_impact": 0,
        "weather_grade": "DOME",
        "weather_reasons": ["Fixed-roof climate-controlled environment"],
        "roof_type": stadium.get("roof", "indoor"),
        "roof_status": "closed",
        **_stadium_identity(stadium),
    }


def _provider_order() -> list[tuple[str, Any]]:
    providers: list[tuple[str, Any]] = []
    if weatherapi_key():
        providers.append(("weatherapi", _weatherapi))
    if visual_crossing_key():
        providers.append(("visualcrossing", _visual_crossing))
    providers.append(("nws", _nws))
    return providers


def provider_configuration() -> dict[str, bool]:
    return {
        "weatherapi": bool(weatherapi_key()),
        "visual_crossing": bool(visual_crossing_key()),
        "nws": True,
    }


def _fetch_stadium_weather(stadium: dict[str, Any], game_time: datetime) -> dict[str, Any]:
    if str(stadium.get("roof") or "").lower() in {"fixed", "dome", "indoor"}:
        return _indoor_payload(stadium, game_time)

    errors: list[str] = []
    for provider_name, provider in _provider_order():
        key = _cache_key(provider_name, stadium, game_time)
        fresh, stale = _cache_read(key)
        if fresh:
            raw = fresh
            stale_used = False
        else:
            try:
                raw = provider(stadium, game_time)
                _cache_success(key, raw)
                stale_used = False
            except (requests.RequestException, RuntimeError, ValueError) as exc:
                error = f"{provider_name}: {exc}"
                errors.append(error)
                _cache_failure(key, error)
                if stale:
                    raw = stale
                    stale_used = True
                else:
                    continue

        direction = raw.get("wind_direction_deg")
        field_effect, angle = wind_field_effect(direction, stadium.get("center_field_bearing"))
        impact, grade, reasons = weather_impact(
            raw.get("temperature_f"),
            raw.get("wind_speed_mph"),
            field_effect,
            raw.get("precip_probability"),
            raw.get("humidity_pct"),
        )
        return {
            "weather_available": True,
            "weather_source": f"{raw.get('provider')}{' cached' if stale_used else ''}",
            "weather_stale": stale_used,
            "weather_warning": " • ".join(errors),
            "weather_time_local": raw.get("forecast_time") or game_time.isoformat(),
            **{key: raw.get(key) for key in (
                "temperature_f", "apparent_temperature_f", "humidity_pct", "dew_point_f",
                "precip_probability", "precipitation_in", "cloud_cover_pct", "visibility_miles",
                "surface_pressure_hpa", "wind_speed_mph", "wind_gust_mph", "wind_direction_deg",
                "weather_description",
            )},
            "wind_field_effect": field_effect,
            "wind_alignment_difference": round(angle, 1),
            "weather_impact": impact,
            "weather_grade": grade,
            "weather_reasons": reasons,
            "roof_type": stadium.get("roof", "outdoor"),
            "roof_status": "unconfirmed" if stadium.get("roof") == "retractable" else "open-air",
            **_stadium_identity(stadium),
        }

    return {
        "weather_available": False,
        "weather_error": " • ".join(errors) or "No weather provider returned a forecast",
        "roof_type": stadium.get("roof", "outdoor"),
        **_stadium_identity(stadium),
    }


def get_game_weather(team: str | None, venue_name: str | None, game_time: Any, slate_date: str) -> dict[str, Any]:
    stadium = find_stadium(team, venue_name)
    if not stadium:
        return {"weather_available": False, "weather_error": "Stadium location not found"}
    local_time = _parse_game_time(game_time, stadium["timezone"], slate_date)
    return _fetch_stadium_weather(stadium, local_time)


def enrich_board_weather(board: dict[str, Any]) -> dict[str, Any]:
    rankings = board.get("rankings", []) or []
    slate_date = str(board.get("date") or date.today().isoformat())

    try:
        schedule = fetch_schedule(slate_date)
    except requests.RequestException as exc:
        schedule = []
        schedule_error = str(exc)
    else:
        schedule_error = ""

    if schedule:
        board = repair_board_games(board, schedule)
    games_meta = board.get("games_meta", []) or []

    contexts: dict[str, tuple[dict[str, Any], datetime]] = {}
    context_game: dict[str, dict[str, Any]] = {}
    results: dict[str, dict[str, Any]] = {}

    # Use the MLB schedule as the authority. This prevents empty Ballpark Pal
    # venue fields from producing the home=None / venue=None failure.
    source_games = schedule or games_meta
    for game in source_games:
        key = str(game.get("schedule_game_key") or game.get("mlb_game_pk") or game.get("game_id") or "")
        home_team = normalize_team_key(game.get("home_team_name"))
        stadium = find_stadium(home_team, game.get("venue_name"))
        if not key:
            continue
        if not stadium:
            results[key] = {
                "weather_available": False,
                "weather_error": f"Stadium location not found for home team={home_team!r}, venue={game.get('venue_name')!r}",
            }
            continue
        local_time = _parse_game_time(game.get("game_time"), stadium["timezone"], slate_date)
        contexts[key] = (stadium, local_time)
        context_game[key] = game

    with ThreadPoolExecutor(max_workers=min(5, max(1, len(contexts)))) as executor:
        future_map = {
            executor.submit(_fetch_stadium_weather, stadium, game_time): key
            for key, (stadium, game_time) in contexts.items()
        }
        for future in as_completed(future_map):
            key = future_map[future]
            try:
                results[key] = future.result()
            except Exception as exc:
                results[key] = {"weather_available": False, "weather_error": str(exc)}

    # Attach weather to every board game, matching by MLB schedule when needed.
    for meta in games_meta:
        schedule_game = match_meta_to_schedule(meta, schedule) if schedule else None
        key = str(
            (schedule_game or {}).get("schedule_game_key")
            or meta.get("schedule_game_key")
            or meta.get("mlb_game_pk")
            or meta.get("game_id")
            or ""
        )
        if schedule_game:
            for field, value in schedule_game.items():
                if value not in (None, ""):
                    meta[field] = value
        if key in results:
            meta.update(results[key])
            meta["weather_game_key"] = key

    # Attach the matching weather and authoritative game metadata to each hitter.
    for player in rankings:
        schedule_game = match_player_to_schedule(player, schedule) if schedule else None
        key = str(
            (schedule_game or {}).get("schedule_game_key")
            or player.get("schedule_game_key")
            or player.get("mlb_game_pk")
            or player.get("game_id")
            or ""
        )
        if schedule_game:
            player.update({
                "schedule_game_key": schedule_game.get("schedule_game_key"),
                "mlb_game_pk": schedule_game.get("mlb_game_pk"),
                "game_time": schedule_game.get("game_time") or player.get("game_time"),
                "venue_name": schedule_game.get("venue_name") or player.get("venue_name"),
                "home_team_name": schedule_game.get("home_team_name"),
                "away_team_name": schedule_game.get("away_team_name"),
                "home_team_id": schedule_game.get("home_team_id"),
                "away_team_id": schedule_game.get("away_team_id"),
            })
        if key in results:
            player.update(results[key])
            player["weather_game_key"] = key

    # Ensure schedule-only games are represented for the all-ballparks page.
    represented = {str(meta.get("weather_game_key") or meta.get("schedule_game_key") or "") for meta in games_meta}
    for game in schedule:
        key = str(game.get("schedule_game_key") or "")
        if key and key not in represented:
            games_meta.append({**game, "game_id": key, "weather_game_key": key, **results.get(key, {})})

    available = sum(1 for item in results.values() if item.get("weather_available"))
    favorable = sum(1 for item in results.values() if item.get("weather_available") and float(item.get("weather_impact") or 0) >= 3)
    providers = sorted({str(item.get("weather_source")) for item in results.values() if item.get("weather_source")})
    errors = sorted({str(item.get("weather_error")) for item in results.values() if item.get("weather_error")})
    if schedule_error:
        errors.append(f"MLB schedule: {schedule_error}")
    board["games_meta"] = games_meta
    board["weather_summary"] = {
        "games_available": available,
        "games_total": len(results),
        "favorable_games": favorable,
        "unavailable_games": max(0, len(results) - available),
        "providers": providers,
        "errors": sorted(set(errors)),
        "configuration": provider_configuration(),
        "schedule_games": len(schedule),
    }
    board.setdefault("data_sources", {})["Weather"] = "live" if available else "unavailable"
    return board

