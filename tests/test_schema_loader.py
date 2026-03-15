from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_tool_gateway.schema_loader import PlaceholderSchemaLoader  # noqa: E402


def test_placeholder_schema_loader_is_explicitly_unimplemented() -> None:
    loader = PlaceholderSchemaLoader()

    with pytest.raises(NotImplementedError):
        loader.load_schema("schemas/example.json")
