"""ESP32 serial hardware effector interface."""

from typing import Optional

try:
    import serial
except ImportError:
    serial = None


class HardwareTrigger:
    def __init__(self, port: Optional[str]):
        self.port = port
        self._conn = None

    @property
    def connected(self) -> bool:
        return self._conn is not None

    def connect(self) -> bool:
        if not self.port or serial is None:
            return False
        try:
            self._conn = serial.Serial(self.port, 115200, timeout=1)
            print(f"[*] Hardware Triggering ENABLED on {self.port}")
            return True
        except Exception as exc:
            print(f"[-] Hardware Error: {exc}")
            self._conn = None
            return False

    def trigger(self, duration_sec: int = 10):
        if self._conn:
            self._conn.write(b"1")

    def release(self):
        if self._conn:
            self._conn.write(b"0")

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
