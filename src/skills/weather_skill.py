"""Weather skill — fetches historical conditions and assesses performance impact."""
from typing import Optional
from src.weather import get_weather
from src.llm import chat
from prompts.prompts import WEATHER_PROMPT
from src.logging_config import logger


def weather_skill(activity: dict) -> dict:
    """Fetch historical weather and assess its impact on the ride.

    Args:
        activity: Activity dict with start_latlng and date.

    Returns:
        Dict with: conditions (str), likely_impact (str), raw_data (dict|None).
    """
    logger.info(f"[weather_skill] Fetching weather for: {activity.get('name')}")

    latlng = activity.get("start_latlng")
    date = activity.get("date")
    raw_data: Optional[dict] = None
    embedded = activity.get("weather")

    if embedded:
        raw_data = {
            "avg_temp_c": embedded["temperature_c"],
            "max_temp_c": embedded["temperature_c"],
            "avg_humidity": embedded["humidity_pct"],
            "avg_wind_kmh": embedded["wind_speed_kmh"],
        }
    elif latlng and len(latlng) == 2 and date:
        logger.info(
            f"[weather_skill] Open-Meteo API → lat={latlng[0]}, lon={latlng[1]}, date={date}"
        )
        raw_data = get_weather(latlng[0], latlng[1], date)

    if raw_data:
        feels = embedded.get("feels_like_c", raw_data["avg_temp_c"]) if embedded else raw_data.get("avg_temp_c")
        conditions_text = (
            f"Temperature: {raw_data.get('avg_temp_c')}°C (feels like {feels}°C)\n"
            f"Humidity: {raw_data.get('avg_humidity')}%\n"
            f"Wind: {raw_data.get('avg_wind_kmh')} km/h"
        )
    else:
        conditions_text = "Weather data unavailable for this activity location/date."

    user_msg = (
        f"Activity: {activity.get('name')} on {activity.get('date')}\n"
        f"Type: {activity.get('type')}, "
        f"Duration: {activity.get('moving_time_min')} min\n\n"
        f"Weather:\n{conditions_text}\n\nAssess likely impact on cycling performance."
    )

    response = chat(WEATHER_PROMPT, user_msg, skill="weather")
    return {"conditions": conditions_text, "likely_impact": response, "raw_data": raw_data}
