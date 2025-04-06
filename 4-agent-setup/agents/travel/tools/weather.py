import os
import requests
from langchain.tools import tool

from utils.logger import logger

@tool
def get_city_weather(city: str) -> str:
    """Get the current weather for a specific city.

    Args:
        city: The name of the city to get weather for.

    Returns:
        A string with current weather information for the city.
    """
    logger.info(f"🌡️ Getting weather for {city}")

    try:
        # Use OpenWeatherMap API - you'd need to set OPENWEATHER_API_KEY in your .env file
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            logger.warning("No OpenWeather API key found in environment variables")
            return f"I couldn't retrieve current weather for {city} due to missing API key."

        # Call weather API
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            weather_desc = data['weather'][0]['description']
            temp = data['main']['temp']
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']

            weather_info = f"Current weather in {city}:\n"
            weather_info += f"- Conditions: {weather_desc}\n"
            weather_info += f"- Temperature: {temp}°C\n"
            weather_info += f"- Humidity: {humidity}%\n"
            weather_info += f"- Wind Speed: {wind_speed} m/s"

            logger.info(f"✅ Weather retrieved successfully for {city}")
            return weather_info
        else:
            logger.warning(f"Weather API error: {response.status_code} - {response.text}")
            return f"I couldn't retrieve current weather for {city}. The city might not be found or there's an API issue."

    except Exception as e:
        logger.error(f"Error getting weather: {str(e)}")
        return f"I encountered an error while getting weather for {city}."
