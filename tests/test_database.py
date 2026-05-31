import os
import tempfile

from ghoststack.database import EventStore


def test_schema_and_health_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        store = EventStore(db_path)
        store.log_event("test-mod", "[!] alert")
        store.log_health("sdr", "RTL-SDR Detected")
        events = store.get_recent_events(10)
        health = store.get_latest_health()
        assert len(events) == 1
        assert events[0][2] == "test-mod"
        assert health.get("sdr") == "RTL-SDR Detected"
