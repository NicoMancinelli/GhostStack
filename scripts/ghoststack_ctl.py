#!/usr/bin/env python3
import argparse
import subprocess
import os
import signal
import sys
import threading
import sqlite3

# GhostStack: Master Orchestrator (GhostStack-CTL)
#
# Centralized CLI to manage modules, intercept their outputs, 
# and log detected threats to a local SQLite database.

DB_PATH = "ghoststack.db"

class GhostStackCTL:
    def __init__(self):
        self.processes = {}
        self.init_db()

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

    def log_output(self, proc, name):
        """Reads stdout of a subprocess and logs 'threats' to SQLite."""
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        c = conn.cursor()
        
        for line in iter(proc.stdout.readline, ''):
            line = line.strip()
            if line:
                print(f"[{name}] {line}")
                # Simple heuristic: If the line contains "[!]", log it as a threat event
                if "[!]" in line:
                    c.execute('INSERT INTO events (module, event) VALUES (?, ?)', (name, line))
                    conn.commit()
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

def main():
    ctl = GhostStackCTL()
    parser = argparse.ArgumentParser(description="GhostStack Master Controller")
    parser.add_argument("command", choices=["start-rf", "start-network", "start-cv", "stop-all", "help"], help="Command to execute")
    
    args = parser.parse_args()

    if args.command == "help":
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "start-rf":
            ctl.start_module("rf-scanner", "python3 rf_ew/scanner_24ghz.py")
            ctl.start_module("remote-id", "python3 rf_ew/classification/remote_id_sniffer.py")
        
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
