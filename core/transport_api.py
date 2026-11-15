"""
===============================================================================
FILE:     core/transport_api.py
OWNER:    Person C – Profiles, Listings & API
-------------------------------------------------------------------------------
PURPOSE
    Live data from an external API (graded requirement no. 2):
    public-transport travel time from a WG address to the HSG campus,
    using the free Swiss API  https://transport.opendata.ch  (no key needed).

WHEN IS IT CALLED?
    Once, when a provider saves / edits their WG listing. The result is stored
    in wgs.travel_time_min, so swiping never waits for the API.

WHAT BELONGS HERE
    - building the API request, reading the JSON answer, error handling
WHAT DOES NOT BELONG HERE
    - Streamlit code, database writes (the page calls database.update_wg)

EXAMPLE REQUEST (try it in your browser):
    https://transport.opendata.ch/v1/connections?from=Rotmonten,St.Gallen&to=St.Gallen,Universität&limit=3
    -> answer["connections"][0]["duration"] looks like "00d00:14:00"

STATUS:   Step 4 – parse_duration is DONE, get_travel_time_minutes is TODO.
AI NOTE:  Generated with Claude (Anthropic), 15.11.2026 – see docs/ai_usage.md
===============================================================================
"""

import requests  # noqa: F401  (used once get_travel_time_minutes is implemented)

from core.config import UNIVERSITY_ADDRESS

BASE_URL = "https://transport.opendata.ch/v1/connections"
TIMEOUT_SECONDS = 10


def parse_duration(duration: str) -> int:
    """DONE: convert the API format "00d00:14:00" into minutes (14)."""
    days, time_part = duration.split("d")
    hours, minutes, _seconds = (int(x) for x in time_part.split(":"))
    return int(days) * 24 * 60 + hours * 60 + minutes


def get_travel_time_minutes(from_address: str, to_address: str = UNIVERSITY_ADDRESS) -> int | None:
    """
    TODO: fastest public-transport time in minutes, or None if it fails.

    Steps:
      1. params = {"from": from_address, "to": to_address, "limit": 3}
      2. response = requests.get(BASE_URL, params=params, timeout=TIMEOUT_SECONDS)
      3. data = response.json();  connections = data.get("connections", [])
      4. if no connections -> return None
      5. return min(parse_duration(c["duration"]) for c in connections)
      6. wrap everything in try/except requests.RequestException -> return None
    """
    raise NotImplementedError("TODO (Person C): get_travel_time_minutes")
