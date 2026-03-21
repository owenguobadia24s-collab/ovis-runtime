# ---
# id: TEST-GATEWAY-0004
# title: Test Schema Loader Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gateway
# repo: ovis-runtime
# path: tests/test_schema_loader.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-GATEWAY-0004.yaml
# module_id: MOD-TOOL-GATEWAY-0001
# module_slug: tool_gateway
# system_id: SYS-INTEGRATION-0001
# system_slug: integration_bridge
# ---
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_tool_gateway.schema_loader import PlaceholderSchemaLoader  # noqa: E402


def test_placeholder_schema_loader_is_explicitly_unimplemented() -> None:
    loader = PlaceholderSchemaLoader()

    with pytest.raises(NotImplementedError):
        loader.load_schema("schemas/example.json")
