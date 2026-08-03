"""Mission archive lifecycle."""

import datetime
import os
import shutil

from ghoststack.paths import DB_PATH, MISSIONS_DIR


def init_mission_archive() -> str:
    os.makedirs(MISSIONS_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    mission_path = os.path.join(MISSIONS_DIR, f"MISSION_{timestamp}")
    os.makedirs(mission_path, exist_ok=True)

    if os.path.exists(DB_PATH):
        shutil.copy(DB_PATH, os.path.join(mission_path, "previous_ghoststack.db"))
        print(f"[*] Previous mission database archived to {mission_path}")

    print(f"[*] Mission Archive initialized: {mission_path}")
    return mission_path
