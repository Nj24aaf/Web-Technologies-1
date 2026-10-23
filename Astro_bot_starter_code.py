#Contains partially completed code with sections for you to complete
#IT IS MANDATORY TO USE THE RESOURCE PROVIDED
#The starter code is structured into functions and modules. You are required to complete the missing sections while maintaining this modular design.  Further step by step instructions can be found in the appendix A of this assignment brief. 
#For extended features implement it within the existing modular structure. The new feature must be triggered using a new command (e.g., /stars, /moon, /sky) and follow the same approach 
#Use Git for version control. Maintain a repository on GitHub to track your project’s progress and changes. Ensure regular commits for each step with meaningful messages that document your step by stepdevelopment process. 

# =========================
# REQUIRED LIBRARIES
# =========================

import requests  # Sends HTTP requests to the APIs.
import json  # Converts Python dictionaries to/from JSON.
import time  # Used to poll Webex every 5 seconds and convert timestamps.
from datetime import datetime  # Kept from the supplied template for date/time work.
import os  # Reads credentials from environment variables when configured.
import re
from html import unescape  # Converts HTML entities to normal text for APOD descriptions.

# =========================
# CONFIGURATION FUNCTIONS
# =========================
def get_webex_token():
    # Prefer an environment variable so the secret does not need to be written into this file.
    token = os.getenv("WEBEX_ACCESS_TOKEN")
    if not token:
        choice = input("Use hard-coded Webex token? (y/n): ").strip().lower()
        if choice == "n":
            token = input("Enter your Webex Access Token: ").strip()
        else:
            # Paste a token here only for local testing; never commit a real token to GitHub.
            token = "YOUR_WEBEX_TOKEN"

    if not token or token == "YOUR_WEBEX_TOKEN":
        print("Set WEBEX_ACCESS_TOKEN or enter your real Webex token when prompted.")
        return ""
    # Webex expects the Authorization header value to start with 'Bearer '.
    return token if token.lower().startswith("bearer ") else f"Bearer {token}"


def get_api_key(prompt, hardcoded_key):
    # Map each prompt to its environment variable. This is safer than storing keys in source code.
    env_name = "OPENWEATHER_API_KEY" if "Weather" in prompt else "NASA_API_KEY"
    api_key = os.getenv(env_name)
    if api_key:
        return api_key

    # Preserve the starter template's option to use a configured default for local testing.
    choice = input(f"Use hard-coded {prompt}? (y/n): ").strip().lower()
    if choice == "y" and hardcoded_key not in ("YOUR_OPENWEATHER_API_KEY", "YOUR_NASA_API_KEY"):
        return hardcoded_key

    entered_key = input(f"Enter {prompt}: ").strip()
    # NASA allows a DEMO_KEY for limited testing; OpenWeather requires your own key.
    if not entered_key and "NASA" in prompt:
        return "DEMO_KEY"
    return entered_key

# =========================
# WEBEX FUNCTIONS
# =========================
def get_rooms(token):
    url = "https://webexapis.com/v1/rooms"  # Webex endpoint that lists rooms.
    headers = {"Authorization": token, "Accept": "application/json"}
    response = requests.get(url, headers=headers, params={"max": 100}, timeout=15)

    if response.status_code != 200:  # HTTP 200 means the request succeeded.
        print("Error fetching rooms:", response.status_code)
        return []

    return response.json().get("items", [])


def print_rooms(rooms):
    # Display both the room title and ID so the user can identify the correct room.
    for room in rooms:
        print(f"Room: {room.get('title', 'Untitled')} | ID: {room.get('id', 'Unknown')} | Type: {room.get('type', 'Unknown')}")


def select_room(rooms):
    while True:
        name = input("Enter the Webex room name (or part of the name): ").strip()
        for room in rooms:
            if name and name.lower() in room.get("title", "").lower():
                print(f"Selected room: {room.get('title', 'Untitled')}")
                return room["id"]
        print("Room not found. Check the name and try again.")


def get_latest_message(token, room_id):
    url = "https://webexapis.com/v1/messages"  # Webex endpoint for room messages.
    # max=1 requests only the newest message; the loop below tracks its ID to avoid repeats.
    params = {"roomId": room_id, "max": 1}
    headers = {"Authorization": token, "Accept": "application/json"}

    response = requests.get(url, headers=headers, params=params, timeout=15)

    if response.status_code != 200:
        return None, None

    data = response.json().get("items", [])

    if not data:
        return None, None

    latest = data[0]
    return latest.get("id"), latest.get("text", "")


def send_message(token, room_id, message):
    url = "https://webexapis.com/v1/messages"  # POST creates a message in the selected room.
    headers = {
        "Authorization": token,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    data = {
        "roomId": room_id,
        "text": message
    }
    # Convert the payload dictionary into JSON text as required by this template.
    response = requests.post(url, headers=headers, data=json.dumps(data), timeout=15)
    if response.status_code not in (200, 201):
        print("Error sending Webex message:", response.status_code)

# =========================
# WEATHER FUNCTIONS
# =========================
def get_city_coordinates(city, api_key):
    # Forward geocoding converts a city name into latitude and longitude.
    url = "https://api.openweathermap.org/geo/1.0/direct"
    params = {"q": city, "limit": 1, "appid": api_key}
    response = requests.get(url, params=params, timeout=15)

    if response.status_code != 200:
        return None

    data = response.json()
    return data[0] if data else None


def get_weather(city, api_key):
    location = get_city_coordinates(city, api_key)

    if not location:
        return f"City '{city}' was not found. Check the spelling and try again."

    # Use the coordinates from geocoding for the current weather request.
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": location["lat"],
        "lon": location["lon"],
        "units": "metric",  # Metric units report temperature in Celsius.
        "appid": api_key
    }

    response = requests.get(url, params=params, timeout=15)

    if response.status_code != 200:
        return f"Weather could not be retrieved (HTTP {response.status_code}). Check the API key."

    weather = response.json()
    main = weather.get("main", {})
    wind = weather.get("wind", {})
    weather_items = weather.get("weather", [])
    description = weather_items[0].get("description", "N/A") if weather_items else "N/A"
    city_name = weather.get("name", city)
    country = weather.get("sys", {}).get("country", "N/A")
    condition = weather_items[0].get("main", "").lower() if weather_items else ""

    # This is a simple guide only; cloud cover and local light pollution also matter.
    if condition == "clear":
        stargazing = "Potentially good for stargazing, based on the reported weather."
    elif condition == "clouds":
        stargazing = "Clouds may obstruct the night sky."
    elif condition in ("rain", "drizzle", "thunderstorm", "snow", "mist", "fog", "haze"):
        stargazing = "Current weather may make stargazing difficult."
    else:
        stargazing = "Stargazing outlook is uncertain from the available weather data."

    return (
        f"Weather for {city_name}, {country}\n"
        f"Conditions: {description}\n"
        f"Temperature: {main.get('temp', 'N/A')} °C\n"
        f"Feels like: {main.get('feels_like', 'N/A')} °C\n"
        f"Humidity: {main.get('humidity', 'N/A')}%\n"
        f"Wind speed: {wind.get('speed', 'N/A')} m/s\n"
        f"{stargazing}"
    )

# =========================
# ISS FUNCTIONS
# =========================
def reverse_geocode(lat, lon, api_key):
    # Reverse geocoding converts coordinates into the nearest named place when available.
    url = "https://api.openweathermap.org/geo/1.0/reverse"
    params = {"lat": lat, "lon": lon, "limit": 1, "appid": api_key}

    response = requests.get(url, params=params, timeout=15)

    if response.status_code != 200:
        return None

    data = response.json()
    return data[0] if data else None


def get_iss_location(api_key):
    # Open Notify provides the ISS latitude, longitude and Unix timestamp as JSON.
    url = "http://api.open-notify.org/iss-now.json"

    response = requests.get(url, timeout=15)

    if response.status_code != 200:
        return f"ISS location could not be retrieved (HTTP {response.status_code})."

    data = response.json()

    lat = data["iss_position"]["latitude"]
    lon = data["iss_position"]["longitude"]

    location = reverse_geocode(lat, lon, api_key)

    place = "Over Ocean / No Nearby City"

    if location:
        # A reverse-geocoded place may contain a name and country; either may be absent.
        place = location.get("name", place)
        if location.get("country"):
            place += f", {location['country']}"

    # The ISS API timestamp is Unix time in seconds. localtime() uses this computer's timezone.
    timestamp = data.get("timestamp")
    try:
        local_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
    except (TypeError, ValueError, OverflowError, OSError):
        local_time = "Unknown"

    # The assignment asks for weather at the ISS coordinates too. This is ground weather,
    # not weather experienced by astronauts aboard the ISS.
    weather_url = "https://api.openweathermap.org/data/2.5/weather"
    weather_params = {"lat": lat, "lon": lon, "units": "metric", "appid": api_key}
    weather_response = requests.get(weather_url, params=weather_params, timeout=15)
    if weather_response.status_code == 200:
        weather = weather_response.json()
        weather_items = weather.get("weather", [])
        description = weather_items[0].get("description", "N/A") if weather_items else "N/A"
        temperature = weather.get("main", {}).get("temp", "N/A")
        weather_text = f"Weather near these coordinates: {description}, {temperature} °C"
    else:
        weather_text = "Weather near the ISS coordinates is currently unavailable."

    return (
        f"ISS current position\n"
        f"Latitude: {lat}\n"
        f"Longitude: {lon}\n"
        f"Nearby location: {place}\n"
        f"Observed at: {local_time} (local time)\n"
        f"{weather_text}"
    )

# =========================
# MAIN BOT LOGIC
# =========================
def main():

    token = get_webex_token()
    if not token:
        return

    weather_key = get_api_key(
        "Weather API key",
        "YOUR_OPENWEATHER_API_KEY"
    )
    if not weather_key:
        print("An OpenWeather API key is required for weather and geocoding.")
        return

    # NASA APOD is the added extension command. DEMO_KEY is available for limited testing.
    nasa_key = get_api_key("NASA API key", "YOUR_NASA_API_KEY")

    rooms = get_rooms(token)

    if not rooms:
        print("No Webex rooms found. Check your token and room permissions.")
        return

    print_rooms(rooms)
    room_id = select_room(rooms)

    # Remember the newest message at startup so old chat messages are not answered again.
    last_message_id, _ = get_latest_message(token, room_id)
    print("AstroBot is monitoring this room. It checks for new messages every 5 seconds.")

    while True:

        message_id, message_text = get_latest_message(token, room_id)

        if message_id and message_id != last_message_id:

            last_message_id = message_id

            print(f"Received message: {message_text}")

            # Ignore normal conversation; only commands beginning with '/' are processed.
            if not message_text or not message_text.startswith("/"):
                time.sleep(5)
                continue

            if message_text.lower() == "/help":
                send_message(
                    token,
                    room_id,
                    "/weather <city> \n /iss \n /apod \n /help \n /quit"
                )

            elif message_text.lower().startswith("/weather"):

                parts = message_text.split(maxsplit=1)

                if len(parts) < 2:
                    send_message(token, room_id, "Usage: /weather <city>")
                else:
                    city = parts[1]
                    send_message(token, room_id, get_weather(city, weather_key))

            elif message_text.lower() == "/iss":
                send_message(token, room_id, get_iss_location(weather_key))

            elif message_text.lower() == "/apod":
                send_message(token, room_id, get_apod(nasa_key))

            elif message_text.lower() == "/quit":
                send_message(token, room_id, "AstroBot shutting down.")
                break

            else:
                send_message(token, room_id, "Unknown command. Use /help")

        # The assignment specifies polling every five seconds.
        time.sleep(5)



def get_apod(api_key):
    """Extended feature: retrieve NASA's Astronomy Picture of the Day."""
    url = "https://science.nasa.gov/wp-json/wp/v2/apod-basic"
    params = {"api_key": api_key}

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        # NASA may return a list containing the APOD entry.
        if isinstance(data, list):
            if not data:
                return "NASA APOD returned no results."
            data = data[0]

        if not isinstance(data, dict):
            return "NASA APOD returned an unexpected response format."
    except requests.RequestException as error:
        return f"NASA APOD request failed: {error}"
    except ValueError:
        return "NASA APOD returned an invalid response."

    
    title = data.get("title", "Astronomy Picture of the Day")
    date = data.get("date", "Unknown date")
    explanation = data.get("explanation", "No explanation available.")

    # Convert NASA's HTML description into readable text.
    explanation = re.sub(r"<br\s*/?>", "\n", explanation, flags=re.I)
    explanation = re.sub(r"</p\s*>", "\n", explanation, flags=re.I)
    explanation = re.sub(r"<[^>]+>", "", explanation)
    explanation = unescape(explanation)
    explanation = re.sub(r"\n\s*\n+", "\n", explanation)
    explanation = explanation.strip()

    # Remove NASA's redundant heading and keep the reply concise.
    explanation = re.sub(
        r"^Explanation:\s*", "", explanation, flags=re.I
    )
    if len(explanation) > 450:
        explanation = explanation[:447].rsplit(" ", 1)[0] + "..."

    media_url = data.get("hdurl")
    article_url = data.get("permalink") or data.get("url")

    return (
        f"NASA Astronomy Picture of the Day\n"
        f"Title: {title}\n"
        f"Date: {date}\n\n"
        f"{explanation}\n\n"
        f"Image: {media_url or 'Not available'}\n"
        f"Article: {article_url or 'Not available'}"
    )




if __name__ == '__main__':
    # Standard Python entry point: only start polling when this file is run directly.
    main()
