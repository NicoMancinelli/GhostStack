"""Structured event formatting for module log lines."""

import json
from typing import Any, Dict, Optional


def format_threat(
    message: str,
    *,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    confidence: Optional[float] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    """Build a supervisor-parseable threat line with optional geo/confidence."""
    parts = [f"[!] {message}"]
    if lat is not None and lon is not None:
        parts.append(f"lat={lat:.6f}, lon={lon:.6f}")
    if confidence is not None:
        parts.append(f"confidence: {confidence:.2f}")
    if extra:
        parts.append(json.dumps(extra))
    return " | ".join(parts)


def parse_confidence(event_text: str) -> Optional[float]:
    import re

    match = re.search(r"confidence\s*[:=]\s*([\d.]+)", event_text, re.I)
    return float(match.group(1)) if match else None
