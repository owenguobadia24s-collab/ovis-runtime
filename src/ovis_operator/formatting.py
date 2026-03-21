# ---
# id: MODULE-OPERATOR-0004
# title: Formatting Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: operator
# repo: ovis-runtime
# path: src/ovis_operator/formatting.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-OPERATOR-0004.yaml
# module_id: MOD-OPERATOR-SURFACE-0001
# module_slug: operator_surface
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""Deterministic CLI formatting helpers."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import date, datetime
from enum import Enum
import json
from pathlib import Path
from typing import Any, Mapping


def to_jsonable(value: Any) -> Any:
    """Recursively convert supported objects into deterministic JSON-safe structures."""

    if hasattr(value, "model_dump"):
        return to_jsonable(value.model_dump(mode="json"))
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: to_jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, set):
        return [to_jsonable(item) for item in sorted(value)]
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    return value


def render_json(value: Any) -> str:
    return json.dumps(to_jsonable(value), indent=2, sort_keys=True) + "\n"


def render_pretty(value: Any) -> str:
    return render_json(value)


def render_error(error_type: str, message: str, *, as_json: bool) -> str:
    payload = {"error_type": error_type, "message": message}
    if as_json:
        return render_json(payload)
    return render_pretty(payload)
