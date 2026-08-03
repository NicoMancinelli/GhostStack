"""MAVLink v1/v2 frame parsing for telemetry extraction."""

import struct
from dataclasses import dataclass
from typing import Optional

MAVLINK_V1_STX = 0xFE
MAVLINK_V2_STX = 0xFD

MSG_HEARTBEAT = 0
MSG_GPS_RAW_INT = 24
MSG_GLOBAL_POSITION_INT = 33


@dataclass
class MavlinkFrame:
    version: int
    msg_id: int
    sys_id: int
    comp_id: int
    payload: bytes


@dataclass
class GpsFix:
    lat: float
    lon: float
    alt_m: Optional[float] = None
    source: str = "unknown"


def parse_frame(raw: bytes) -> Optional[MavlinkFrame]:
    if len(raw) < 8:
        return None
    if raw[0] == MAVLINK_V2_STX:
        if len(raw) < 12:
            return None
        payload_len = raw[1]
        if len(raw) < 10 + payload_len + 2:
            return None
        msg_id = struct.unpack("<I", raw[7:10] + b"\x00")[0]
        return MavlinkFrame(
            version=2,
            msg_id=msg_id,
            sys_id=raw[5],
            comp_id=raw[6],
            payload=raw[10 : 10 + payload_len],
        )
    if raw[0] == MAVLINK_V1_STX:
        payload_len = raw[1]
        if len(raw) < 6 + payload_len + 2:
            return None
        return MavlinkFrame(
            version=1,
            msg_id=raw[5],
            sys_id=raw[3],
            comp_id=raw[4],
            payload=raw[6 : 6 + payload_len],
        )
    return None


def _deg_e7_to_float(value: int) -> float:
    return value / 1e7


def extract_gps(frame: MavlinkFrame) -> Optional[GpsFix]:
    payload = frame.payload
    if frame.msg_id == MSG_GLOBAL_POSITION_INT and len(payload) >= 12:
        lat = struct.unpack("<i", payload[4:8])[0]
        lon = struct.unpack("<i", payload[8:12])[0]
        alt_mm = struct.unpack("<i", payload[12:16])[0] if len(payload) >= 16 else None
        return GpsFix(
            lat=_deg_e7_to_float(lat),
            lon=_deg_e7_to_float(lon),
            alt_m=alt_mm / 1000.0 if alt_mm is not None else None,
            source="GLOBAL_POSITION_INT",
        )
    if frame.msg_id == MSG_GPS_RAW_INT and len(payload) >= 12:
        lat = struct.unpack("<i", payload[4:8])[0]
        lon = struct.unpack("<i", payload[8:12])[0]
        alt_mm = struct.unpack("<i", payload[12:16])[0] if len(payload) >= 16 else None
        return GpsFix(
            lat=_deg_e7_to_float(lat),
            lon=_deg_e7_to_float(lon),
            alt_m=alt_mm / 1000.0 if alt_mm is not None else None,
            source="GPS_RAW_INT",
        )
    return None


def parse_udp_mavlink_payload(raw: bytes) -> Optional[GpsFix]:
    frame = parse_frame(raw)
    if not frame:
        return None
    return extract_gps(frame)
