from mcp.server.fastmcp import FastMCP
import requests, re, os

mcp = FastMCP("tools")

@mcp.tool()
def get_transcript(url: str) -> str:
    """Get YouTube video transcript via Supadata API (cloud-friendly)."""
    # Supadata fetches YouTube transcripts server-side — no IP ban issues.
    # Get a free API key at supadata.ai and add SUPADATA_API_KEY to Railway Variables.
    key = os.environ.get("SUPADATA_API_KEY", "")
    resp = requests.get(
        "https://api.supadata.ai/v1/youtube/transcript",
        params={"url": url, "text": True},
        headers={"x-api-key": key},
        timeout=15,
    )
    data = resp.json()
    if not resp.ok or "content" not in data:
        return f"Transcript error: {data}"
    raw = data["content"]
    # Supadata returns either a plain string or a list of {text, offset, duration} dicts
    if isinstance(raw, list):
        text = " ".join(item["text"].replace("
", " ") for item in raw)
    else:
        text = raw
    return text[:6000]

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
