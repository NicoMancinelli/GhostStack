"""Central path and environment configuration."""

import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DB_PATH = os.environ.get("GHOSTSTACK_DB", os.path.join(REPO_ROOT, "ghoststack.db"))
SAFE_ZONES_PATH = os.environ.get(
    "GHOSTSTACK_SAFE_ZONES", os.path.join(REPO_ROOT, "config", "safe_zones.yaml")
)
POLICIES_PATH = os.environ.get(
    "GHOSTSTACK_POLICIES", os.path.join(REPO_ROOT, "config", "policies.yaml")
)
TARGETS_PATH = os.environ.get(
    "GHOSTSTACK_TARGETS", os.path.join(REPO_ROOT, "config", "targets.yaml")
)
MISSIONS_DIR = os.environ.get(
    "GHOSTSTACK_MISSIONS", os.path.join(REPO_ROOT, "missions")
)
PIDFILE_PATH = os.environ.get(
    "GHOSTSTACK_PIDFILE", os.path.join(REPO_ROOT, "run", "ghoststack.pid")
)
