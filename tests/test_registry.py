# ---
# id: TEST-GATEWAY-0003
# title: Test Registry Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gateway
# repo: ovis-runtime
# path: tests/test_registry.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-GATEWAY-0003.yaml
# module_id: MOD-TOOL-GATEWAY-0001
# module_slug: tool_gateway
# system_id: SYS-INTEGRATION-0001
# system_slug: integration_bridge
# ---
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_tool_gateway.registry import CapabilityRegistry  # noqa: E402
from ovis_tool_gateway.types import CapabilityDefinition  # noqa: E402


def test_registry_can_store_placeholder_definition() -> None:
    registry = CapabilityRegistry()
    definition = CapabilityDefinition(
        name="example.capability",
        version="v1",
        schema_ref="schemas/example.json",
        side_effect_class="read-only",
    )

    registry.register(definition)

    assert registry.get("example.capability") == definition
    assert len(registry.list()) == 1
