"""Public transport times and coordinates from transport.opendata.ch."""
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: code everything missing.
import math
import re

import requests

from core.config import UNIVERSITY_ADDRESS

BASE_URL = "https://transport.opendata.ch/v1/connections"
TIMEOUT_SECONDS = 10


def parse_duration(duration: str) -> int:
    """Parse 00d00:14:00, rounding partial minutes up."""
    match = re.fullmatch(r"(\d+)d(\d{2}):(\d{2}):(\d{2})", duration)
    if not match:
        raise ValueError("Invalid transport duration")
    days, hours, minutes, seconds = map(int, match.groups())
    if hours >= 24 or minutes >= 60 or seconds >= 60:
        raise ValueError("Invalid transport duration")
    return days * 1440 + hours * 60 + minutes + math.ceil(seconds / 60)


def get_travel_time_minutes(from_address: str, to_address: str = UNIVERSITY_ADDRESS) -> int | None:
    """Return the fastest of three upcoming connections, or None on failure."""
    if not from_address.strip():
        return None
    try:
        response = requests.get(BASE_URL, params={"from": from_address, "to": to_address, "limit": 3}, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        durations = []
        for connection in response.json().get("connections", []):
            try:
                durations.append(parse_duration(connection["duration"]))
            except (KeyError, ValueError, TypeError):
                continue
        return min(durations) if durations else None
    except (requests.RequestException, ValueError, TypeError, AttributeError):
        return None


def get_location_coordinates(address: str) -> tuple[float, float] | None:
    """Resolve an address to latitude/longitude for the listing map."""
    try:
        response = requests.get(
            "https://transport.opendata.ch/v1/locations",
            params={"query": address, "type": "address"}, timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        for station in response.json().get("stations", []):
            coordinate = station.get("coordinate") or {}
            if coordinate.get("x") is not None and coordinate.get("y") is not None:
                lat, lon = float(coordinate["x"]), float(coordinate["y"])
                if math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon
    except (requests.RequestException, ValueError, TypeError, AttributeError):
        pass
    return None
