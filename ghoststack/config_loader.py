"""YAML configuration loading with target variable substitution."""

import os
from typing import Any, Dict, List

import yaml

from ghoststack.paths import POLICIES_PATH, SAFE_ZONES_PATH, TARGETS_PATH


def load_yaml_key(path: str, key: str, default=None):
    if not os.path.exists(path):
        return default if default is not None else []
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data.get(key, default if default is not None else [])


def load_targets() -> Dict[str, Any]:
    raw = load_yaml_key(TARGETS_PATH, "targets", default={})
    if not isinstance(raw, dict):
        return {}
    return raw


def load_safe_zones() -> List[dict]:
    return load_yaml_key(SAFE_ZONES_PATH, "safe_zones", default=[])


def load_policies() -> List[dict]:
    return load_yaml_key(POLICIES_PATH, "policies", default=[])


def resolve_template(value: str, variables: Dict[str, Any]) -> str:
    """Replace {key} placeholders using targets config."""
    if not value or "{" not in value:
        return value
    try:
        return value.format(**{k: str(v) for k, v in variables.items()})
    except KeyError as exc:
        raise KeyError(f"Missing target variable for policy command: {exc}") from exc
