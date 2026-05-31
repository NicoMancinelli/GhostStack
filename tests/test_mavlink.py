import struct

from ghoststack.mavlink import MSG_GLOBAL_POSITION_INT, extract_gps, parse_frame


def _frame(lat: float, lon: float) -> bytes:
    lat_e7 = int(lat * 1e7)
    lon_e7 = int(lon * 1e7)
    payload = struct.pack("<IiiiihhhH", 0, lat_e7, lon_e7, 50000, 50000, 0, 0, 0, 0)
    header = bytes([0xFD, len(payload), 0, 0, 0, 2, 1]) + struct.pack("<I", MSG_GLOBAL_POSITION_INT)[:3]
    return header + payload + b"\x00\x00"


def test_global_position_int_decode():
    gps = extract_gps(parse_frame(_frame(34.0522, -118.2437)))
    assert gps is not None
    assert abs(gps.lat - 34.0522) < 0.0001
    assert abs(gps.lon - (-118.2437)) < 0.0001
    assert gps.source == "GLOBAL_POSITION_INT"


def test_invalid_frame_returns_none():
    assert parse_frame(b"\x00\x01") is None
