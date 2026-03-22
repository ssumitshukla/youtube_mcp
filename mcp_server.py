from mcp.server.fastmcp import FastMCP
from youtube_transcript_api import YouTubeTranscriptApi
import requests, re, os

mcp = FastMCP("tools")

@mcp.tool()
def get_transcript(url: str) -> str:
    """Get YouTube video transcript."""
    vid = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url).group(1)

    # proxy config — required when running on cloud servers (Railway, Render, etc.)
    # YouTube blocks all cloud IPs; a residential proxy bypasses this.
    # Sign up at webshare.io (free tier) and add PROXY_URL to Railway Variables.
    # Format: http://username:password@proxy.webshare.io:80
    proxy_url = os.environ.get("PROXY_URL")
    proxies   = {"http": proxy_url, "https": proxy_url} if proxy_url else None

    api = YouTubeTranscriptApi(proxies=proxies)
    return " ".join(s.text for s in api.fetch(vid))

@mcp.tool()
def calculate(expression: str) -> str:
    """Evaluate a math expression."""
    return f"{expression} = {eval(expression)}"

@mcp.tool()
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    geo = requests.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": city, "count": 1}).json()
    if not geo.get("results"):
        return f"City '{city}' not found. Try a different name or spelling."
    loc = geo["results"][0]
    w = requests.get("https://api.open-meteo.com/v1/forecast", params={"latitude": loc["latitude"], "longitude": loc["longitude"], "current_weather": True}).json()["current_weather"]
    return f"{loc['name']}: {w['temperature']}°C, wind {w['windspeed']} km/h"

if __name__ == "__main__":
    mcp.run(transport="stdio")
