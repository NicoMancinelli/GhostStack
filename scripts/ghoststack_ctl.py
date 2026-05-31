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
import yaml
import re
import json
import math
import datetime
import shutil

# GhostStack: Master Orchestrator (Deployment Grade)
#
# A production-ready process supervisor featuring a Policy Engine,
# Hardware Health Monitoring, Structured JSON Logging, and Mission Archiving.

DB_PATH = "ghoststack.db"
SAFE_ZONES_PATH = "config/safe_zones.yaml"
POLICIES_PATH = "config/policies.yaml"
MISSIONS_DIR = "missions"

RF_MODULES = [
    ("rf-scanner", "python3 rf_ew/scanner_24ghz.py"),
    ("remote-id", "python3 rf_ew/classification/remote_id_sniffer.py"),
    ("gamutrf-connector", "python3 rf_ew/classification/gamutrf_connector.py"),
]

NETWORK_MODULES = [
    ("mav-sniff", "python3 network_analysis/ghoststack_network/mavlink_sniff.py"),
    ("unitree-detect", "python3 network_analysis/robot_research/unitree_detector.py"),
]

FULL_STACK_MODULES = RF_MODULES + NETWORK_MODULES


class GhostStackCTL:
    def __init__(self, esp_port=None, sentry_mode=False):
        self.processes = {}
        self.mission_dir = self.init_mission_archive()
        self.init_db()
        self.serial_conn = None
        self.trigger_timer = None
        self.esp_port = esp_port
        
        # System State
        self.sentry_mode = sentry_mode
        self.last_cv_event = 0
        self.last_rf_event = 0
        self.is_in_safe_zone = False
        self.triggers_inhibited = False
        
        # Configs
        self.safe_zones = self.load_yaml(SAFE_ZONES_PATH, 'safe_zones')
        self.policies = self.load_yaml(POLICIES_PATH, 'policies')
        
        if esp_port:
            self.connect_hardware()

    def init_mission_archive(self):
        """Creates a timestamped mission folder and backs up the previous database."""
        os.makedirs(MISSIONS_DIR, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        mission_path = os.path.join(MISSIONS_DIR, f"MISSION_{timestamp}")
        os.makedirs(mission_path, exist_ok=True)
        
        if os.path.exists(DB_PATH):
            shutil.copy(DB_PATH, os.path.join(mission_path, "previous_ghoststack.db"))
            print(f"[*] Previous mission database archived to {mission_path}")
            
        print(f"[*] Mission Archive initialized: {mission_path}")
        return mission_path

    def init_db(self):
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS events 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
                      module TEXT, event TEXT, raw_json TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS system_health 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
                      component TEXT, status TEXT)''')
        conn.commit()
        conn.close()

    def load_yaml(self, path, key):
        if os.path.exists(path):
            with open(path, 'r') as f:
                return yaml.safe_load(f).get(key, [])
        return []

    def connect_hardware(self):
        try:
            self.serial_conn = serial.Serial(self.esp_port, 115200, timeout=1)
            print(f"[*] Hardware Triggering ENABLED on {self.esp_port}")
        except Exception as e:
            print(f"[-] Hardware Error: {e}")

    def log_to_db(self, module, event, raw_data=None):
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('INSERT INTO events (module, event, raw_json) VALUES (?, ?, ?)', 
                  (module, event, json.dumps(raw_data) if raw_data else None))
        conn.commit()
        conn.close()

    def execute_policy_check(self, module, event_text):
        """Iterates through policies and executes actions if conditions are met."""
        for policy in self.policies:
            cond = policy['condition']
            match = False

            if 'state' in cond:
                state_val = getattr(self, cond['state'], None)
                match = state_val == cond.get('value')
            elif cond.get('module') == module and cond.get('event_contains') in event_text:
                min_conf = cond.get('min_confidence')
                if min_conf is not None:
                    conf_match = re.search(
                        r'confidence["\']?\s*[:=]\s*([\d.]+)', event_text, re.I
                    )
                    match = bool(
                        conf_match and float(conf_match.group(1)) >= min_conf
                    )
                else:
                    match = True

            if match:
                print(f"[!] POLICY MATCH: '{policy['name']}' triggered.")
                for action in policy['actions']:
                    self.execute_action(action)

    def execute_action(self, action):
        atype = action['type']
        if atype == "inhibit_all_triggers":
            self.triggers_inhibited = True
            print(action.get('message', '[*] All hardware triggers inhibited.'))
            self.log_to_db("SYSTEM", action.get('message', 'Triggers inhibited'))

        elif atype == "hardware_trigger" and self.serial_conn and not self.is_in_safe_zone and not self.triggers_inhibited:
            self.serial_conn.write(b'1')
            print(f"[!] ACTION: {action['value']} for {action.get('duration_sec', 10)}s")
            # Set timer to turn off
            threading.Timer(action.get('duration_sec', 10), lambda: self.serial_conn.write(b'0')).start()
        
        elif atype == "start_module":
            self.start_module(action['module_name'], action['command'])
            
        elif atype == "log_event":
            print(action['message'])
            self.log_to_db("SYSTEM", action['message'])

    def log_output(self, proc, name):
        """Supervisor loop for child process output."""
        mission_log = os.path.join(self.mission_dir, f"{name}_raw.log")
        
        with open(mission_log, "a") as f_log:
            for line in iter(proc.stdout.readline, ''):
                line = line.strip()
                if not line: continue
                
                print(f"[{name}] {line}")
                f_log.write(f"{datetime.datetime.now().isoformat()} - {line}\n")
                f_log.flush()
                
                if "[!]" in line:
                    self.log_to_db(name, line)
                    self.execute_policy_check(name, line)

    def start_module(self, name, command):
        if name in self.processes: return
        print(f"[*] Starting {name}...")
        proc = subprocess.Popen(command, shell=True, preexec_fn=os.setsid, 
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self.processes[name] = proc
        threading.Thread(target=self.log_output, args=(proc, name), daemon=True).start()

    def health_loop(self):
        """Background thread to monitor hardware health."""
        from utils import health_check
        while True:
            results = health_check.run_full_diagnostic(self.esp_port)
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            c = conn.cursor()
            for component, status in results.items():
                c.execute(
                    'INSERT INTO system_health (component, status) VALUES (?, ?)',
                    (component, status),
                )
            conn.commit()
            conn.close()
            time.sleep(60)

    def run_supervisor(self, modules):
        """Start modules, health monitoring, and block until interrupted."""
        threading.Thread(target=self.health_loop, daemon=True).start()
        for name, command in modules:
            self.start_module(name, command)
        print("[*] GhostStack Supervisor Active. Monitoring processes and policies...")
        try:
            while True:
                signal.pause()
        except KeyboardInterrupt:
            print("\n[*] Shutting down GhostStack...")
            self.stop_all()

    def stop_all(self):
        for name, proc in self.processes.items():
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        if self.serial_conn: self.serial_conn.close()

def main():
    parser = argparse.ArgumentParser(description="GhostStack Supervisor")
    parser.add_argument(
        "command",
        choices=["start-all", "start-rf", "start-network", "stop-all", "diagnose"],
    )
    parser.add_argument("--esp-port", default="/dev/ttyUSB0")
    parser.add_argument("--sentry", action="store_true", help="Enable active sentry mode")
    args = parser.parse_args()

    if args.command == "stop-all":
        print("[*] stop-all is a no-op without a running supervisor process.")
        sys.exit(0)

    ctl = GhostStackCTL(esp_port=args.esp_port, sentry_mode=args.sentry)

    if args.command == "start-all":
        ctl.run_supervisor(FULL_STACK_MODULES)
    elif args.command == "start-rf":
        ctl.run_supervisor(RF_MODULES)
    elif args.command == "start-network":
        ctl.run_supervisor(NETWORK_MODULES)
    elif args.command == "diagnose":
        from utils import health_check
        health_check.run_full_diagnostic(args.esp_port)

if __name__ == "__main__":
    main()
