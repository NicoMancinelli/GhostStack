"""Dashboard authentication helpers."""

import os
import secrets
from functools import wraps
from typing import Optional

from flask import Request, request, session

from ghoststack.config_loader import load_yaml_key
from ghoststack.paths import REPO_ROOT

def _auth_enabled(cfg: dict) -> bool:
    raw = os.environ.get("GHOSTSTACK_DASHBOARD_AUTH")
    if raw is not None:
        return raw.lower() not in ("0", "false", "no")
    return bool(cfg.get("auth_enabled", True))


DASHBOARD_CONFIG_PATH = os.environ.get(
    "GHOSTSTACK_DASHBOARD_CONFIG",
    os.path.join(REPO_ROOT, "config", "dashboard.yaml"),
)


def _dashboard_config() -> dict:
    cfg = load_yaml_key(DASHBOARD_CONFIG_PATH, "dashboard", default={}) or {}
    return {
        "username": os.environ.get("GHOSTSTACK_DASHBOARD_USER", cfg.get("username", "ghost")),
        "password": os.environ.get("GHOSTSTACK_DASHBOARD_PASSWORD", cfg.get("password", "stack")),
        "token": os.environ.get("GHOSTSTACK_DASHBOARD_TOKEN", cfg.get("token", "")),
        "auth_enabled": _auth_enabled(cfg),
    }


def credentials_valid(username: str, password: str) -> bool:
    cfg = _dashboard_config()
    if not cfg["auth_enabled"]:
        return True
    return secrets.compare_digest(username, cfg["username"]) and secrets.compare_digest(
        password, cfg["password"]
    )


def token_valid(token: Optional[str]) -> bool:
    cfg = _dashboard_config()
    if not cfg["auth_enabled"]:
        return True
    expected = cfg["token"] or f"{cfg['username']}:{cfg['password']}"
    if not token:
        return False
    return secrets.compare_digest(token, expected)


def check_http_auth(req: Request) -> bool:
    cfg = _dashboard_config()
    if not cfg["auth_enabled"]:
        return True
    auth = req.authorization
    if auth and credentials_valid(auth.username, auth.password):
        return True
    return token_valid(req.headers.get("X-GhostStack-Token"))


def check_socket_auth(auth: Optional[dict]) -> bool:
    cfg = _dashboard_config()
    if not cfg["auth_enabled"]:
        return True
    if not auth:
        return False
    if auth.get("token") and token_valid(auth.get("token")):
        return True
    user = auth.get("username") or ""
    password = auth.get("password") or ""
    return credentials_valid(user, password)


def require_http_auth(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if check_http_auth(request) or session.get("authenticated"):
            return view(*args, **kwargs)
        return (
            "Authentication required. Use HTTP Basic or X-GhostStack-Token.",
            401,
            {"WWW-Authenticate": 'Basic realm="GhostStack Dashboard"'},
        )

    return wrapped
