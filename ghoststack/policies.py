"""Policy engine: evaluates YAML rules and executes actions."""

import re
import threading
from typing import Any, Callable, Dict, List, Optional

from ghoststack.config_loader import load_policies, load_targets, resolve_template
from ghoststack.events import parse_confidence


class PolicyEngine:
    def __init__(
        self,
        policies: Optional[List[dict]] = None,
        targets: Optional[Dict[str, Any]] = None,
        *,
        get_state: Callable[[], Dict[str, Any]],
        on_hardware_trigger: Callable[[dict], None],
        on_start_module: Callable[[str, str], None],
        on_log_event: Callable[[str], None],
        on_inhibit: Callable[[str], None],
    ):
        self.policies = policies if policies is not None else load_policies()
        self.targets = targets if targets is not None else load_targets()
        self._get_state = get_state
        self._on_hardware_trigger = on_hardware_trigger
        self._on_start_module = on_start_module
        self._on_log_event = on_log_event
        self._on_inhibit = on_inhibit

    def evaluate_module_event(self, module: str, event_text: str):
        for policy in self.policies:
            cond = policy.get("condition", {})
            if not self._match_module_condition(cond, module, event_text):
                continue
            self._fire_policy(policy)

    def evaluate_state(self):
        """Re-run state-only policies (e.g. safe zone inhibit)."""
        state = self._get_state()
        for policy in self.policies:
            cond = policy.get("condition", {})
            if "state" not in cond:
                continue
            key = cond["state"]
            if state.get(key) == cond.get("value"):
                self._fire_policy(policy)

    def _match_module_condition(self, cond: dict, module: str, event_text: str) -> bool:
        if "state" in cond:
            return False
        if cond.get("module") != module:
            return False
        needle = cond.get("event_contains")
        if needle and needle not in event_text:
            return False
        min_conf = cond.get("min_confidence")
        if min_conf is not None:
            conf = parse_confidence(event_text)
            if conf is None or conf < float(min_conf):
                return False
        return True

    def _fire_policy(self, policy: dict):
        print(f"[!] POLICY MATCH: '{policy.get('name', 'unnamed')}' triggered.")
        for action in policy.get("actions", []):
            self.execute_action(action)

    def execute_action(self, action: dict):
        atype = action.get("type")
        state = self._get_state()

        if atype == "inhibit_all_triggers":
            self._on_inhibit(action.get("message", "Triggers inhibited"))
            return

        if atype == "hardware_trigger":
            if state.get("is_in_safe_zone") or state.get("triggers_inhibited"):
                return
            if not state.get("hardware_connected"):
                return
            self._on_hardware_trigger(action)
            return

        if atype == "start_module":
            cmd = resolve_template(action.get("command", ""), self.targets)
            self._on_start_module(action["module_name"], cmd)
            return

        if atype == "log_event":
            self._on_log_event(action.get("message", ""))
