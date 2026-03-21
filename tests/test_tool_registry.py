# ---
# id: TEST-GATEWAY-0007
# title: Test Tool Registry Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gateway
# repo: ovis-runtime
# path: tests/test_tool_registry.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-GATEWAY-0007.yaml
# module_id: MOD-TOOL-GATEWAY-0001
# module_slug: tool_gateway
# system_id: SYS-INTEGRATION-0001
# system_slug: integration_bridge
# ---
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_tool_gateway import CapabilityDefinition, CapabilityRegistry, capability  # noqa: E402


def test_registry_registers_definition_and_handler_together() -> None:
    registry = CapabilityRegistry()

    def echo_handler(payload: dict[str, object]) -> dict[str, object]:
        return payload

    definition = CapabilityDefinition(
        name="echo.return",
        version="v1",
        schema_ref="schemas/echo.return.json",
        side_effect_class="read-only",
    )

    registry.register(definition, handler=echo_handler)

    resolved_definition, resolved_handler = registry.resolve("echo.return")
    assert registry.get("echo.return") == definition
    assert registry.get_handler("echo.return") is echo_handler
    assert resolved_definition == definition
    assert resolved_handler({"value": "hello"}) == {"value": "hello"}


def test_registry_rejects_duplicate_registration() -> None:
    registry = CapabilityRegistry()
    definition = CapabilityDefinition(
        name="math.add",
        version="v1",
        schema_ref="schemas/math.add.json",
        side_effect_class="read-only",
    )

    registry.register(definition, handler=lambda payload: payload)

    with pytest.raises(ValueError):
        registry.register(definition, handler=lambda payload: payload)


def test_capability_decorator_registers_handler_into_given_registry() -> None:
    registry = CapabilityRegistry()

    @capability(
        "math.add",
        version="v1",
        schema_ref="schemas/math.add.json",
        side_effect_class="read-only",
        registry=registry,
    )
    def add_handler(payload: dict[str, int]) -> int:
        return payload["a"] + payload["b"]

    definition, handler = registry.resolve("math.add")
    assert definition.name == "math.add"
    assert handler is add_handler
    assert handler({"a": 2, "b": 3}) == 5
