import requests
from langchain_core.tools import tool
from langsmith import traceable

from app.core.config import get_settings

settings = get_settings()


@tool
@traceable(name="weather_tool")
def weather_tool(destination: str) -> dict:
    """
    Fetch current weather information for a travel destination.

    Args:
        destination: City or destination name.

    Returns:
        Weather details including temperature, condition, humidity, wind speed,
        and travel recommendation.
    """

    params = {
        "q": destination,
        "appid": settings.WEATHER_API_KEY,
        "units": "metric",
    }

    try:
        response = requests.get(
            settings.WEATHER_BASE_URL,
            params=params,
            timeout=10,
        )

        response.raise_for_status()
        data = response.json()

        temperature = data.get("main", {}).get("temp")
        feels_like = data.get("main", {}).get("feels_like")
        humidity = data.get("main", {}).get("humidity")
        condition = data.get("weather", [{}])[0].get("description", "Unknown")
        wind_speed = data.get("wind", {}).get("speed")

        recommendation = generate_weather_recommendation(
            temperature=temperature,
            condition=condition,
        )

        return {
            "city": destination,
            "temperature": temperature,
            "feels_like": feels_like,
            "condition": condition,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "recommendation": recommendation,
        }

    except Exception as e:
        return {
            "city": destination,
            "temperature": None,
            "feels_like": None,
            "condition": "Weather data unavailable",
            "humidity": None,
            "wind_speed": None,
            "recommendation": "Weather data could not be fetched. Plan with general precautions.",
            "error": str(e),
        }


@traceable(name="generate_weather_recommendation")
def generate_weather_recommendation(temperature: float | None, condition: str) -> str:
    if temperature is None:
        return "Carry water, check weather manually before travel, and avoid risky outdoor planning."

    condition_lower = condition.lower()

    if "rain" in condition_lower or "storm" in condition_lower:
        return "Carry an umbrella or raincoat. Avoid outdoor activities during heavy rain."

    if temperature >= 35:
        return "Weather may be very hot. Prefer morning and evening sightseeing."

    if temperature <= 15:
        return "Weather may be cold. Carry warm clothes."

    return "Weather looks manageable. Normal travel planning is suitable."