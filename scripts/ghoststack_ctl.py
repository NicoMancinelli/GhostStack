#!/usr/bin/env python3
import argparse
import subprocess
import os
import signal
import sys
import threading
import sqlite3
import serial
import time

# GhostStack: Master Orchestrator (GhostStack-CTL)
#
# Now includes 'Active Sentry' mode and 'Geo-Fencing' logic.

import yaml
import math

DB_PATH = "ghoststack.db"
SAFE_ZONES_PATH = "config/safe_zones.yaml"

class GhostStackCTL:
    def __init__(self, esp_port=None, sentry_mode=False):
        self.processes = {}
        self.init_db()
        self.serial_conn = None
        self.trigger_timer = None
        
        # Sentry Mode State
        self.sentry_mode = sentry_mode
        self.last_cv_event = 0
        self.last_rf_event = 0
        
        # Geo-Fencing State
        self.safe_zones = self.load_safe_zones()
        self.is_in_safe_zone = False
        
        if esp_port:
            try:
                self.serial_conn = serial.Serial(esp_port, 115200, timeout=1)
                print(f"[*] Hardware Triggering ENABLED on {esp_port}")
                if self.sentry_mode:
                    print("[*] SENTRY MODE ACTIVE: Multi-factor trigger required (CV + RF/Network)")
            except Exception as e:
                print(f"[-] Failed to connect to ESP32: {e}")

    def load_safe_zones(self):
        if os.path.exists(SAFE_ZONES_PATH):
            try:
                with open(SAFE_ZONES_PATH, 'r') as f:
                    config = yaml.safe_load(f)
                    print(f"[*] Loaded {len(config.get('safe_zones', []))} safe zones.")
                    return config.get('safe_zones', [])
            except Exception as e:
                print(f"[-] Error loading safe zones: {e}")
        return []

    def check_geo_fence(self, lat, lon):
        """Calculates distance to safe zones and updates state."""
        for zone in self.safe_zones:
            # Haversine formula for distance in meters
            R = 6371000
            phi1, phi2 = math.radians(lat), math.radians(zone['lat'])
            dphi = math.radians(zone['lat'] - lat)
            dlambda = math.radians(zone['lon'] - lon)
            a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            dist = R * c
            
            if dist <= zone['radius_meters']:
                if not self.is_in_safe_zone:
                    print(f"[!] GEO-FENCE: Target entered Safe Zone '{zone['name']}'. Disabling triggers.")
                self.is_in_safe_zone = True
                return True
        
        if self.is_in_safe_zone:
            print("[*] GEO-FENCE: Target left Safe Zone. Re-enabling triggers.")
        self.is_in_safe_zone = False
        return False

    def init_db(self):
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                module TEXT,
                event TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def disengage_strobe(self):
        if self.serial_conn:
            self.serial_conn.write(b'0')
            print("[*] Threat timeout reached. Disengaging Optical Blinder.")

    def log_output(self, proc, name):
        """Reads stdout of a subprocess and logs 'threats' to SQLite."""
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        c = conn.cursor()
        
        # Regex for Lat/Lon extraction from log lines
        coord_pattern = re.compile(r'([-+]?\d{1,2}\.\d+),\s*([-+]?\d{1,3}\.\d+)')

        for line in iter(proc.stdout.readline, ''):
            line = line.strip()
            if line:
                print(f"[{name}] {line}")
                if "[!]" in line:
                    c.execute('INSERT INTO events (module, event) VALUES (?, ?)', (name, line))
                    conn.commit()
                    
                    # Update Geo-Fence state if coordinates found
                    match = coord_pattern.search(line)
                    if match:
                        self.check_geo_fence(float(match.group(1)), float(match.group(2)))

                    # Update Sentry State
                    current_time = time.time()
                    if "yolo" in name:
                        self.last_cv_event = current_time
                    else:
                        self.last_rf_event = current_time

                    # Trigger Logic
                    should_trigger = False
                    if self.serial_conn and not self.is_in_safe_zone:
                        if self.sentry_mode:
                            if abs(self.last_cv_event - self.last_rf_event) < 30:
                                should_trigger = True
                                print("[!] SENTRY CONDITION MET: CV + RF Correlation.")
                        else:
                            should_trigger = True

                        if should_trigger:
                            self.serial_conn.write(b'1')
                            print(f"[!] TRIGGER SENT by {name}.")
                            
                            if self.trigger_timer:
                                self.trigger_timer.cancel()
                            self.trigger_timer = threading.Timer(10.0, self.disengage_strobe)
                            self.trigger_timer.start()
        conn.close()

    def start_module(self, name, command):
        if name in self.processes:
            print(f"[-] Module '{name}' is already running.")
            return

        print(f"[*] Starting module: {name}...")
        try:
            # Run in a new process group, capture stdout
            proc = subprocess.Popen(
                command, 
                shell=True, 
                preexec_fn=os.setsid, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True,
                bufsize=1
            )
            self.processes[name] = proc
            print(f"[+] {name} started with PID {proc.pid}")
            
            # Start background thread to parse output
            threading.Thread(target=self.log_output, args=(proc, name), daemon=True).start()
            
        except Exception as e:
            print(f"[-] Failed to start {name}: {e}")

    def stop_module(self, name):
        if name not in self.processes:
            print(f"[-] Module '{name}' is not running.")
            return

        print(f"[*] Stopping module: {name}...")
        try:
            os.killpg(os.getpgid(self.processes[name].pid), signal.SIGTERM)
            del self.processes[name]
            print(f"[+] {name} stopped.")
        except Exception as e:
            print(f"[-] Error stopping {name}: {e}")

    def stop_all(self):
        names = list(self.processes.keys())
        for name in names:
            self.stop_module(name)
        if self.serial_conn:
            self.serial_conn.write(b'0')
            self.serial_conn.close()

def main():
    parser = argparse.ArgumentParser(description="GhostStack Master Controller")
    parser.add_argument("command", choices=["start-rf", "start-network", "start-cv", "stop-all", "help"], help="Command to execute")
    parser.add_argument("--esp-port", default=None, help="Serial port of ESP32 (e.g., /dev/ttyUSB0) for hardware triggers.")
    
    args = parser.parse_args()

    if args.command == "help":
        parser.print_help()
        sys.exit(0)

    ctl = GhostStackCTL(esp_port=args.esp_port)

    try:
        if args.command == "start-rf":
            ctl.start_module("rf-scanner", "python3 rf_ew/scanner_24ghz.py")
            ctl.start_module("remote-id", "python3 rf_ew/classification/remote_id_sniffer.py")
            ctl.start_module("gamutrf", "python3 rf_ew/classification/gamutrf_connector.py")
        
        elif args.command == "start-network":
            ctl.start_module("mav-sniff", "python3 network_analysis/ghoststack_network/mavlink_sniff.py")
            ctl.start_module("flock-detect", "python3 network_analysis/alpr_research/flock_detector.py")
        
        elif args.command == "start-cv":
            ctl.start_module("yolo-detect", "python3 cv_adversarial/patches/yolo_detector.py")
        
        elif args.command == "stop-all":
            ctl.stop_all()
            sys.exit(0)

        print("[*] GhostStack running. Press Ctrl+C to stop all.")
        while True:
            signal.pause()

    except KeyboardInterrupt:
        print("\n[*] Interrupted. Shutting down all modules...")
        ctl.stop_all()

if __name__ == "__main__":
    main()
