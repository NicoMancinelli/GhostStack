from ghoststack.events import format_threat, parse_confidence


def test_format_threat_includes_confidence():
    line = format_threat("Detection", confidence=0.91, lat=1.0, lon=2.0)
    assert "confidence: 0.91" in line
    assert "lat=1.000000" in line


def test_parse_confidence():
    assert parse_confidence("[!] x | confidence: 0.95") == 0.95
