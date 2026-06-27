"""Open-Meteo historical weather fetcher for the AI Endurance Coach."""

from typing import Optional

import requests


OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"


def get_weather(lat: float, lon: float, date_iso: str) -> Optional[dict]:
    """Fetch historical weather for a given location and date.

    Uses the Open-Meteo archive API (no API key required).

    Args:
        lat: Latitude of the activity start.
        lon: Longitude of the activity start.
        date_iso: Date string in 'YYYY-MM-DD' format.

    Returns:
        Dict with keys: avg_temp_c, max_temp_c, avg_humidity, avg_wind_kmh.
        Returns None if data is unavailable or the request fails.
    """
    try:
        resp = requests.get(
            OPEN_METEO_ARCHIVE,
            params={
                "latitude": lat,
                "longitude": lon,
                "start_date": date_iso,
                "end_date": date_iso,
                "daily": "temperature_2m_mean,temperature_2m_max,precipitation_sum,windspeed_10m_max",
                "hourly": "relativehumidity_2m",
                "timezone": "auto",
            },
            timeout=10,
        )

        if resp.status_code != 200:
            return None

        data = resp.json()

        daily = data.get("daily", {})
        hourly = data.get("hourly", {})

        avg_temp = _first(daily.get("temperature_2m_mean"))
        max_temp = _first(daily.get("temperature_2m_max"))
        max_wind = _first(daily.get("windspeed_10m_max"))

        humidity_vals = hourly.get("relativehumidity_2m", [])
        avg_humidity = (
            round(sum(humidity_vals) / len(humidity_vals), 1)
            if humidity_vals
            else None
        )

        return {
            "avg_temp_c": avg_temp,
            "max_temp_c": max_temp,
            "avg_humidity": avg_humidity,
            "avg_wind_kmh": max_wind,
        }

    except Exception:
        return None


def _first(lst: Optional[list]) -> Optional[float]:
    """Return the first element of a list, or None if empty."""
    if lst and len(lst) > 0:
        return lst[0]
    return None
