#!/usr/bin/env python3
"""Headless smoke test for CI and docker-compose.smoke.yml."""

import os
import struct
import sys
import tempfile

# Ensure repo root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ghoststack.auth import credentials_valid, token_valid
from ghoststack.database import EventStore
from ghoststack.mavlink import MSG_GLOBAL_POSITION_INT, extract_gps, parse_frame
from ghoststack.policies import PolicyEngine


def _build_global_position_frame(lat: float, lon: float) -> bytes:
    lat_e7 = int(lat * 1e7)
    lon_e7 = int(lon * 1e7)
    payload = struct.pack("<IiiiihhhH", 0, lat_e7, lon_e7, 100000, 100000, 0, 0, 0, 0)
    msg_id = MSG_GLOBAL_POSITION_INT
    header = bytes([0xFD, len(payload), 0, 0, 0, 1, 1]) + struct.pack("<I", msg_id)[:3]
    return header + payload + b"\x00\x00"


def main() -> int:
    print("[smoke] MAVLink GPS parse...")
    raw = _build_global_position_frame(37.775, -122.419)
    frame = parse_frame(raw)
    gps = extract_gps(frame)
    assert gps and abs(gps.lat - 37.775) < 0.001
    print("[smoke] OK")

    print("[smoke] Database roundtrip...")
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "smoke.db")
        store = EventStore(db)
        store.log_event("smoke", "[!] test")
        assert len(store.get_recent_events(5)) == 1
    print("[smoke] OK")

    print("[smoke] Policy engine...")
    hits = []

    engine = PolicyEngine(
        policies=[
            {
                "name": "smoke",
                "condition": {"module": "gamutrf", "event_contains": "dji", "min_confidence": 0.8},
                "actions": [{"type": "log_event", "message": "fired"}],
            }
        ],
        targets={},
        get_state=lambda: {"is_in_safe_zone": False, "triggers_inhibited": False, "hardware_connected": False},
        on_hardware_trigger=lambda a: None,
        on_start_module=lambda n, c: None,
        on_log_event=lambda m: hits.append(m),
        on_inhibit=lambda m: None,
    )
    engine.evaluate_module_event("gamutrf", "[!] dji | confidence: 0.95")
    assert hits == ["fired"]
    print("[smoke] OK")

    os.environ["GHOSTSTACK_DASHBOARD_AUTH"] = "false"
    print("[smoke] Auth disabled mode...")
    assert credentials_valid("any", "any")
    assert token_valid(None)
    print("[smoke] OK")

    print("[smoke] All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
