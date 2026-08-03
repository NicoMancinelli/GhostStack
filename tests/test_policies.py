from ghoststack.policies import PolicyEngine


def test_policy_min_confidence_match():
    fired = []

    engine = PolicyEngine(
        policies=[
            {
                "name": "test",
                "condition": {
                    "module": "gamutrf",
                    "event_contains": "dji_mavic",
                    "min_confidence": 0.9,
                },
                "actions": [{"type": "log_event", "message": "hit"}],
            }
        ],
        targets={},
        get_state=lambda: {"is_in_safe_zone": False, "triggers_inhibited": False, "hardware_connected": True},
        on_hardware_trigger=lambda a: fired.append("hw"),
        on_start_module=lambda n, c: None,
        on_log_event=lambda m: fired.append(m),
        on_inhibit=lambda m: None,
    )
    engine.evaluate_module_event(
        "gamutrf",
        "[!] GamutRF Detection: 'dji_mavic' | confidence: 0.92",
    )
    assert "hit" in fired


def test_policy_target_substitution():
    started = []

    engine = PolicyEngine(
        policies=[],
        targets={"mavlink_broadcast": "10.0.0.255"},
        get_state=lambda: {},
        on_hardware_trigger=lambda a: None,
        on_start_module=lambda n, c: started.append((n, c)),
        on_log_event=lambda m: None,
        on_inhibit=lambda m: None,
    )
    engine.execute_action(
        {
            "type": "start_module",
            "module_name": "killswitch",
            "command": "python3 killswitch.py {mavlink_broadcast}",
        }
    )
    assert started[0][1] == "python3 killswitch.py 10.0.0.255"
