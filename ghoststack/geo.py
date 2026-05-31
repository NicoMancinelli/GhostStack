"""Geospatial utilities: coordinate parsing and safe-zone checks."""

import math
import re
from typing import Dict, List, Optional, Tuple

COORD_PAIR_RE = re.compile(
    r"lat[=:\s]+([-+]?\d{1,2}\.\d+)[,\s]+lon[=:\s]+([-+]?\d{1,3}\.\d+)",
    re.I,
)
COORD_LEGACY_RE = re.compile(r"([-+]?\d{1,2}\.\d+),\s*([-+]?\d{1,3}\.\d+)")


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def extract_coordinates(event_text: str) -> Optional[Dict[str, float]]:
    if not event_text:
        return None
    match = COORD_PAIR_RE.search(event_text) or COORD_LEGACY_RE.search(event_text)
    if not match:
        return None
    return {"lat": float(match.group(1)), "lon": float(match.group(2))}


class SafeZoneChecker:
    def __init__(self, zones: List[dict]):
        self.zones = zones or []

    def is_inside(self, lat: float, lon: float) -> Tuple[bool, Optional[str]]:
        for zone in self.zones:
            zlat = zone.get("lat")
            zlon = zone.get("lon")
            radius = zone.get("radius_meters", 100)
            if zlat is None or zlon is None:
                continue
            dist = haversine_meters(lat, lon, float(zlat), float(zlon))
            if dist <= float(radius):
                return True, zone.get("name", "safe_zone")
        return False, None
