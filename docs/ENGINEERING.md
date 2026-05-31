# GhostStack Engineering Guide

Operating baseline for architecture, quality, and development workflow.

## Product scope

GhostStack is a **research framework** for defensive threat-modeling against autonomous systems. Effector paths assume **authorized lab use**. See `wiki/Legal-and-Ethics.md`.

## Repository map

| Area | Path | Role |
|------|------|------|
| **Core library** | `ghoststack/` | Shared DB, geo, policies, supervisor, health, pidfile |
| CLI | `scripts/ghoststack_ctl.py` | Thin entrypoint |
| Dashboard | `dashboard/app.py` | Flask + SocketIO (uses `ghoststack.database`) |
| RF/EW | `rf_ew/` | Scanners, GamutRF bridge, Remote ID |
| Network | `network_analysis/` | MAVLink, WiFi, robot research, ROS 2 nodes (optional) |
| CV | `cv_adversarial/` | YOLO patches (`requirements-ml.txt`) |
| Config | `config/` | `policies.yaml`, `safe_zones.yaml`, `targets.yaml` |
| Tests | `tests/` | pytest smoke suite |
| Ops | `docker-compose.yml`, `config/ghoststack.service` | Deploy |

## How to run

```bash
# Core RF profile
python3 scripts/ghoststack_ctl.py start-rf --esp-port /dev/ttyUSB0

# Network profile
python3 scripts/ghoststack_ctl.py start-network --esp-port /dev/ttyUSB0

# Full stack (+ sentry extras with --sentry)
python3 scripts/ghoststack_ctl.py start-all --sentry

# Stop background supervisor
python3 scripts/ghoststack_ctl.py stop-all

# Dashboard
python3 dashboard/app.py
```

**Dependencies:** `scripts/install_deps.sh` (apt + `requirements.txt`). ML: `pip install -r requirements-ml.txt`.

**Tests:** `pytest -q`

## Quality bar

1. CI: flake8 E9/F63/F7/F82 + pytest
2. Docs match CLI and `ghoststack/modules.py` profiles
3. Policies use `{target}` placeholders from `config/targets.yaml`
4. Threat lines use `ghoststack.events.format_threat()` for geo/confidence
5. No silent effectors: serial + safe zone + inhibit flags

## Architecture

- **SQLite** (`ghoststack.db`) — event bus
- **`[!]` log prefix** — policy triggers
- **Geo-fencing** — `SafeZoneChecker` updates `is_in_safe_zone` from parsed coordinates
- **PID file** — `run/ghoststack.pid` for `stop-all` and systemd
- **Module profiles** — `ghoststack/modules.py` (RF, network, sentry)

## Configuration

| File | Purpose |
|------|---------|
| `config/targets.yaml` | IPs, WiFi iface, map center (`{mavlink_broadcast}` in policies) |
| `config/safe_zones.yaml` | Geo-fences that inhibit effectors |
| `config/policies.yaml` | Automated responses |

Environment overrides: `GHOSTSTACK_DB`, `GHOSTSTACK_PIDFILE`, `GHOSTSTACK_SENTRY`, `GHOSTSTACK_WIFI_IFACE`.

## ROS 2 (optional)

`network_analysis/` ships `package.xml` for colcon on a ROS Humble host. CI validates metadata only; full build is optional on target hardware.

## Dashboard auth

- HTTP Basic or `X-GhostStack-Token` header on `/` and `/api/health`
- Session login at `/login`
- Socket.IO `connect` requires `auth: { token: "..." }` (see `dashboard/static/dashboard.js`)
- Configure via `config/dashboard.yaml` or `GHOSTSTACK_DASHBOARD_USER` / `GHOSTSTACK_DASHBOARD_PASSWORD` / `GHOSTSTACK_DASHBOARD_TOKEN`
- Disable for lab smoke tests: `GHOSTSTACK_DASHBOARD_AUTH=false`

## Smoke / integration

```bash
python3 scripts/smoke_test.py
docker compose -f docker-compose.smoke.yml run --rm ghoststack-smoke
```

## Contribution

1. Branch: `cursor/<name>-b8f3`
2. Extend `ghoststack/` for cross-cutting logic; keep field scripts thin
3. Add tests under `tests/`
4. Run `pytest` and flake8 before push
