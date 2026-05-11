#!/usr/bin/env python3
import argparse
import subprocess
import os
import signal
import sys

# GhostStack: Master Orchestrator (GhostStack-CTL)
#
# A centralized CLI tool to manage the various disruption and analysis modules.

class GhostStackCTL:
    def __init__(self):
        self.processes = {}

    def start_module(self, name, command):
        if name in self.processes:
            print(f"[-] Module '{name}' is already running.")
            return

        print(f"[*] Starting module: {name}...")
        try:
            # Run in a new process group to allow killing child processes
            proc = subprocess.Popen(command, shell=True, preexec_fn=os.setsid)
            self.processes[name] = proc
            print(f"[+] {name} started with PID {proc.pid}")
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
    parser.add_argument("command", choices=["start-rf", "start-network", "start-cv", "stop-all"], help="Command to execute")
    parser.add_argument("--interface", default="wlan0mon", help="WiFi interface for scanners")

    args = parser.parse_args()

    try:
        if args.command == "start-rf":
            ctl.start_module("rf-scanner", f"python3 rf_ew/scanner_24ghz.py")
            ctl.start_module("remote-id", f"python3 rf_ew/classification/remote_id_sniffer.py")
        
        elif args.command == "start-network":
            ctl.start_module("mav-sniff", f"python3 network_analysis/mavlink_sniff.py")
            ctl.start_module("flock-detect", f"python3 network_analysis/alpr_research/flock_detector.py")
        
        elif args.command == "start-cv":
            ctl.start_module("yolo-detect", f"python3 cv_adversarial/patches/yolo_detector.py")
        
        elif args.command == "stop-all":
            ctl.stop_all()
            sys.exit(0)

        # Keep main thread alive to monitor processes
        print("[*] GhostStack running. Press Ctrl+C to stop all.")
        while True:
            signal.pause()

    except KeyboardInterrupt:
        print("\n[*] Interrupted. Shutting down all modules...")
        ctl.stop_all()

if __name__ == "__main__":
    main()
