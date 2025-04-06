import os
import requests
from langchain.tools import tool

from utils.logger import logger

@tool
def get_city_fallback_info(city: str) -> str:
    """Fallback function to provide basic information about a city when API fails."""
    logger.info(f"Using fallback info for {city}")
    return f"""
# {city.title()}

I don't have specific up-to-date information about {city} at the moment due to API limitations.
However, {city} is a known city that you can explore for its:

## General Information
- Local culture and history
- Architecture and city layout
- Local cuisine and traditional dishes

## Typical Attractions in Cities
1. **Historic Sites and Landmarks**
   - Main squares, monuments, historic buildings

2. **Museums and Cultural Institutions**
   - Art galleries, history museums, cultural centers

3. **Parks and Recreation Areas**
   - City parks, walking areas, viewpoints

4. **Shopping Districts**
   - Local markets, shopping streets, artisan shops

5. **Dining and Entertainment**
   - Local restaurants, entertainment venues

For more specific information, consider researching {city} through a travel guidebook or website.
    """

@tool
def get_city_info(city: str) -> str:
    """Get general information and top attractions about a specific city.

    Args:
        city: The name of the city to get information for.

    Returns:
        A string with information about the city and its top attractions.
    """
    logger.info(f"🏙️ Getting info for {city}")

    try:
        # Use OpenTripMap API to get city data
        # You'll need to get a free API key from https://opentripmap.io/
        api_key = os.getenv("OPENTRIPMAP_API_KEY")

        # First, get the city coordinates
        geoname_url = f"https://api.opentripmap.com/0.1/en/places/geoname?name={city}&apikey={api_key}"
        geo_response = requests.get(geoname_url)

        if geo_response.status_code != 200:
            logger.warning(f"OpenTripMap API error: {geo_response.status_code} - {geo_response.text}")
            return get_city_fallback_info(city)

        geo_data = geo_response.json()
        if not geo_data or "lat" not in geo_data or "lon" not in geo_data:
            logger.warning(f"Could not find coordinates for {city}")
            return get_city_fallback_info(city)

        # Get city information and attractions using the coordinates
        lat = geo_data["lat"]
        lon = geo_data["lon"]
        country = geo_data.get("country", "")

        # Get the top attractions
        radius = 5000  # 5km radius
        limit = 10     # Top 10 attractions
        attractions_url = f"https://api.opentripmap.com/0.1/en/places/radius?radius={radius}&lon={lon}&lat={lat}&rate=3&format=json&limit={limit}&apikey={api_key}"
        attractions_response = requests.get(attractions_url)

        if attractions_response.status_code != 200:
            logger.warning(f"OpenTripMap attractions API error: {attractions_response.status_code}")
            return get_city_fallback_info(city)

        attractions_data = attractions_response.json()

        # Format the response
        city_info = f"# {city.title()}, {country}\n\n"
        city_info += f"{city.title()} is located at coordinates {lat:.2f}, {lon:.2f}. "

        if geo_data.get("population"):
            city_info += f"It has a population of approximately {geo_data['population']:,}. "

        city_info += "\n\n## Top Attractions:\n\n"

        if not attractions_data:
            city_info += "No specific attractions found in the database for this city.\n"
        else:
            for i, attraction in enumerate(attractions_data[:6], 1):
                name = attraction.get("name", "Unnamed attraction")
                kinds = attraction.get("kinds", "").replace(",", ", ")

                # Skip attractions without names
                if not name or name == "":
                    continue

                city_info += f"{i}. **{name}**\n"
                if kinds:
                    city_info += f"   - Type: {kinds}\n"
                if attraction.get("rate"):
                    city_info += f"   - Rating: {attraction.get('rate', 0)}/7\n"
                city_info += "\n"

        logger.info(f"✅ Retrieved {len(attractions_data) if attractions_data else 0} attractions for {city}")
        return city_info

    except Exception as e:
        logger.error(f"Error getting city info: {str(e)}")
        return f"I encountered an error while getting information for {city}. Please try again later."
