"""Process supervisor orchestrating modules, geo-fencing, and policies."""

import datetime
import os
import signal
import subprocess
import threading
import time
from typing import Dict, List, Optional

from ghoststack.config_loader import load_policies, load_safe_zones, load_targets
from ghoststack.database import EventStore
from ghoststack.geo import SafeZoneChecker, extract_coordinates
from ghoststack.hardware import HardwareTrigger
from ghoststack.health import run_full_diagnostic
from ghoststack.mission import init_mission_archive
from ghoststack.pidfile import remove_pid, write_pid
from ghoststack.policies import PolicyEngine


class GhostStackSupervisor:
    def __init__(
        self,
        modules: List[tuple],
        *,
        esp_port: Optional[str] = None,
        sentry_mode: bool = False,
        store: Optional[EventStore] = None,
    ):
        self.modules = modules
        self.esp_port = esp_port
        self.sentry_mode = sentry_mode
        self.processes: Dict[str, subprocess.Popen] = {}
        self.mission_dir = init_mission_archive()
        self.store = store or EventStore()
        self.hardware = HardwareTrigger(esp_port)
        if esp_port:
            self.hardware.connect()

        self.safe_zones = load_safe_zones()
        self.zone_checker = SafeZoneChecker(self.safe_zones)
        self.targets = load_targets()

        self.is_in_safe_zone = False
        self.active_safe_zone: Optional[str] = None
        self.triggers_inhibited = False
        self.last_cv_event = 0
        self.last_rf_event = 0

        self.policy_engine = PolicyEngine(
            policies=load_policies(),
            targets=self.targets,
            get_state=self._state_snapshot,
            on_hardware_trigger=self._hardware_trigger,
            on_start_module=self.start_module,
            on_log_event=self._log_system_event,
            on_inhibit=self._inhibit_triggers,
        )

    def _state_snapshot(self) -> dict:
        return {
            "is_in_safe_zone": self.is_in_safe_zone,
            "triggers_inhibited": self.triggers_inhibited,
            "hardware_connected": self.hardware.connected,
            "sentry_mode": self.sentry_mode,
        }

    def _inhibit_triggers(self, message: str):
        self.triggers_inhibited = True
        print(message or "[*] All hardware triggers inhibited.")
        self.store.log_event("SYSTEM", message or "Triggers inhibited")

    def _log_system_event(self, message: str):
        print(message)
        self.store.log_event("SYSTEM", message)

    def _hardware_trigger(self, action: dict):
        duration = int(action.get("duration_sec", 10))
        label = action.get("value", "strobe_on")
        print(f"[!] ACTION: {label} for {duration}s")
        self.hardware.trigger(duration)
        threading.Timer(duration, self.hardware.release).start()

    def _update_geo_from_line(self, line: str):
        coords = extract_coordinates(line)
        if not coords:
            return
        inside, name = self.zone_checker.is_inside(coords["lat"], coords["lon"])
        prev = self.is_in_safe_zone
        self.is_in_safe_zone = inside
        self.active_safe_zone = name if inside else None
        if inside and not prev:
            print(f"[*] GEO: Target entered safe zone '{name}'.")
            self.policy_engine.evaluate_state()
        elif not inside and prev:
            print("[*] GEO: Target left safe zone. Effectors may engage.")
            self.triggers_inhibited = False

    def log_output(self, proc: subprocess.Popen, name: str):
        mission_log = os.path.join(self.mission_dir, f"{name}_raw.log")
        with open(mission_log, "a", encoding="utf-8") as f_log:
            for line in iter(proc.stdout.readline, ""):
                line = line.strip()
                if not line:
                    continue
                print(f"[{name}] {line}")
                f_log.write(f"{datetime.datetime.now().isoformat()} - {line}\n")
                f_log.flush()
                self._update_geo_from_line(line)
                if "[!]" in line:
                    self.store.log_event(name, line)
                    self.policy_engine.evaluate_module_event(name, line)

    def start_module(self, name: str, command: str):
        if name in self.processes:
            return
        print(f"[*] Starting {name}...")
        from ghoststack.paths import REPO_ROOT

        env = os.environ.copy()
        env["PYTHONPATH"] = REPO_ROOT + os.pathsep + env.get("PYTHONPATH", "")
        if self.sentry_mode:
            env["GHOSTSTACK_SENTRY"] = "1"
        proc = subprocess.Popen(
            command,
            shell=True,
            preexec_fn=os.setsid,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
            cwd=REPO_ROOT,
        )
        self.processes[name] = proc
        threading.Thread(target=self.log_output, args=(proc, name), daemon=True).start()

    def health_loop(self):
        while True:
            for component, status in run_full_diagnostic(self.esp_port).items():
                self.store.log_health(component, status)
            time.sleep(60)

    def run(self):
        write_pid()
        threading.Thread(target=self.health_loop, daemon=True).start()
        for name, command in self.modules:
            self.start_module(name, command)
        mode = "SENTRY" if self.sentry_mode else "STANDARD"
        print(f"[*] GhostStack Supervisor Active ({mode}). Ctrl+C to stop.")
        try:
            while True:
                signal.pause()
        except KeyboardInterrupt:
            print("\n[*] Shutting down GhostStack...")
            self.stop_all()

    def stop_all(self):
        for proc in self.processes.values():
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
        self.hardware.close()
        remove_pid()
