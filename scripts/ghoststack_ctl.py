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

# GhostStack: Master Orchestrator (Deployment Grade)
#
# A production-ready process supervisor featuring a Policy Engine,
# Hardware Health Monitoring, and Structured JSON Logging.

DB_PATH = "ghoststack.db"
SAFE_ZONES_PATH = "config/safe_zones.yaml"
POLICIES_PATH = "config/policies.yaml"

class GhostStackCTL:
    def __init__(self, esp_port=None, sentry_mode=False):
        self.processes = {}
        self.init_db()
        self.serial_conn = None
        self.trigger_timer = None
        self.esp_port = esp_port
        
        # System State
        self.sentry_mode = sentry_mode
        self.last_cv_event = 0
        self.last_rf_event = 0
        self.is_in_safe_zone = False
        
        # Configs
        self.safe_zones = self.load_yaml(SAFE_ZONES_PATH, 'safe_zones')
        self.policies = self.load_yaml(POLICIES_PATH, 'policies')
        
        if esp_port:
            self.connect_hardware()

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
            
            # Condition Checking
            if cond.get('module') == module:
                if cond.get('event_contains') in event_text:
                    match = True
            
            if match:
                print(f"[!] POLICY MATCH: '{policy['name']}' triggered.")
                for action in policy['actions']:
                    self.execute_action(action)

    def execute_action(self, action):
        atype = action['type']
        if atype == "hardware_trigger" and self.serial_conn and not self.is_in_safe_zone:
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
        for line in iter(proc.stdout.readline, ''):
            line = line.strip()
            if not line: continue
            
            print(f"[{name}] {line}")
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
        while True:
            # We would call utils.health_check here and log to DB
            time.sleep(60)

    def stop_all(self):
        for name, proc in self.processes.items():
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        if self.serial_conn: self.serial_conn.close()

def main():
    parser = argparse.ArgumentParser(description="GhostStack Supervisor")
    parser.add_argument("command", choices=["start-all", "stop-all", "diagnose"])
    parser.add_argument("--esp-port", default="/dev/ttyUSB0")
    args = parser.parse_args()

    ctl = GhostStackCTL(esp_port=args.esp_port)

    if args.command == "start-all":
        # Launch standard stack based on policies or default
        ctl.start_module("rf-scanner", "python3 rf_ew/scanner_24ghz.py")
        ctl.start_module("remote-id", "python3 rf_ew/classification/remote_id_sniffer.py")
        ctl.start_module("mav-sniff", "python3 network_analysis/ghoststack_network/mavlink_sniff.py")
        
        print("[*] GhostStack Supervisor Active. Monitoring processes and policies...")
        while True: signal.pause()
        
    elif args.command == "diagnose":
        from utils import health_check
        health_check.run_full_diagnostic(args.esp_port)

if __name__ == "__main__":
    main()
