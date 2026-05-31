# GhostStack Engineering Guide

This document is the operating baseline for GhostStack development: architecture boundaries, quality bar, and prioritized backlog.

## Product scope

GhostStack is a **research framework** for defensive threat-modeling against autonomous systems (UAV/UGV/quadruped). It is not a turnkey weapon system. All effector paths assume **authorized lab use** with hardware present; see `wiki/Legal-and-Ethics.md`.

## Repository map

| Area | Path | Role |
|------|------|------|
| Orchestrator | `scripts/ghoststack_ctl.py` | Process supervisor, policy engine, mission archive, hardware triggers |
| Dashboard | `dashboard/app.py` | Flask + SocketIO tactical UI |
| RF/EW | `rf_ew/` | Scanners, GamutRF bridge, Remote ID |
| Network | `network_analysis/` | MAVLink, WiFi, robot research, ROS 2 nodes |
| CV | `cv_adversarial/` | YOLO patches and evaluation |
| Optical | `optical_disruption/esp32/` | ESP32 IR strobe firmware |
| Config | `config/` | Policies, safe zones, systemd unit |
| Ops | `docker-compose.yml`, `Dockerfile` | Containerized demo stack |

## How to run (canonical)

```bash
# Docker (dashboard + RF profile)
docker-compose up --build

# Bare metal — RF only
python3 scripts/ghoststack_ctl.py start-rf --esp-port /dev/ttyUSB0

# Bare metal — network stack
python3 scripts/ghoststack_ctl.py start-network --esp-port /dev/ttyUSB0

# Full stack
python3 scripts/ghoststack_ctl.py start-all --esp-port /dev/ttyUSB0

# Dashboard (separate terminal)
python3 dashboard/app.py
```

Dependencies: **apt** for SDR/ROS (`scripts/install_deps.sh`), **pip** for Python (`requirements.txt`).

## Quality bar

1. **Syntax / undefined names**: CI `flake8` E9,F63,F7,F82 must pass.
2. **Docs match CLI**: README, `docker-compose.yml`, and `DEMO_SCRIPT.md` must agree with `ghoststack_ctl.py` commands.
3. **Policies are honest**: If `config/policies.yaml` declares a condition, the orchestrator must implement it or the policy must be marked experimental.
4. **No silent effectors**: Hardware triggers require serial connection, safe-zone clearance, and no inhibit flag.

## Architecture decisions (current)

- **SQLite** (`ghoststack.db`) is the integration bus between modules, dashboard, and hijack orchestrator.
- **Line-delimited logs** with `[!]` prefix drive policy evaluation (simple, debuggable).
- **Mission archives** timestamp each supervisor run under `missions/`.
- **Docker** uses ROS Humble base image for GNU Radio; bare-metal uses Kali/apt.

## Known gaps (backlog)

### P0 — reliability

- [ ] **Automated tests**: No `tests/` directory; add smoke tests for policy parsing, DB schema, and CLI argument validation.
- [ ] **Geo-fencing**: `config/safe_zones.yaml` exists but `is_in_safe_zone` is never updated from telemetry — wire GPS from MAVLink/Remote ID events.
- [ ] **PID file / remote stop**: `stop-all` cannot stop a background supervisor; add pidfile or systemd integration (`config/ghoststack.service`).

### P1 — feature completeness

- [ ] **Policy `min_confidence`**: Requires classifiers to emit `confidence: <float>` in log lines (GamutRF connector).
- [ ] **Sentry mode**: `--sentry` flag is accepted but not yet wired to module set or thresholds.
- [ ] **Dashboard health**: UI shows static "ACTIVE" labels; bind to `system_health` table populated by orchestrator.
- [ ] **ROS 2 package**: `network_analysis/` has package.xml but CI only checks directory existence — add colcon build in CI or document as optional.

### P2 — hardening

- [ ] **Split requirements**: Optional `requirements-ml.txt` for ultralytics/opencv to speed headless RF-only installs.
- [ ] **Secrets / targets**: No env-based target config; hardcoded IPs in policies should move to `config/targets.yaml`.
- [ ] **README clone URL**: Replace `your-repo` placeholder with real remote.

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`): Python 3.10, flake8, pip install from `requirements.txt`. Full hardware stack is **not** exercised in CI.

## Contribution workflow

1. Branch: `cursor/<descriptive-name>-b8f3`
2. Small, focused commits with rationale in message body
3. Run `python3 -m flake8 . --select=E9,F63,F7,F82` before push
4. Update this backlog when closing a known gap

## Risk register

| Risk | Mitigation |
|------|------------|
| Regulatory misuse of EW/optical modules | Prominent disclaimers; policy inhibit + safe zones (when wired) |
| `shell=True` in subprocess supervisor | Acceptable for research orchestrator; restrict commands to internal module list |
| Privileged Docker (`privileged: true`) | Required for USB SDR; document host-only deployment |
| Policy auto-trigger | Requires ESP32 + explicit lab setup; geo-fence still TODO |
