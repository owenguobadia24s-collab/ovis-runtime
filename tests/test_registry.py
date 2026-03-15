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
