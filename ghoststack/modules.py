"""Supervisor module profiles (RF, network, sentry, full stack)."""

from typing import List, Tuple

ModuleSpec = Tuple[str, str]

RF_MODULES: List[ModuleSpec] = [
    ("rf-scanner", "python3 rf_ew/scanner_24ghz.py"),
    ("remote-id", "python3 rf_ew/classification/remote_id_sniffer.py"),
    ("gamutrf", "python3 rf_ew/classification/gamutrf_connector.py"),
]

NETWORK_MODULES: List[ModuleSpec] = [
    ("mav-sniff", "python3 network_analysis/ghoststack_network/mavlink_sniff.py"),
    ("unitree-detect", "python3 network_analysis/robot_research/unitree_detector.py"),
]

SENTRY_EXTRA: List[ModuleSpec] = [
    ("wifi-deauth", "python3 network_analysis/ghoststack_network/wifi_deauth.py"),
    ("hijack-orch", "python3 scripts/hijack_orchestrator.py"),
    ("target-linker", "python3 scripts/target_linker.py"),
]

FULL_STACK_MODULES: List[ModuleSpec] = RF_MODULES + NETWORK_MODULES
SENTRY_MODULES: List[ModuleSpec] = FULL_STACK_MODULES + SENTRY_EXTRA


def profile_for(command: str, sentry: bool = False) -> List[ModuleSpec]:
    if command == "start-rf":
        return list(RF_MODULES)
    if command == "start-network":
        return list(NETWORK_MODULES)
    if command == "start-all":
        return list(SENTRY_MODULES if sentry else FULL_STACK_MODULES)
    return []
