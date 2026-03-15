from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_state_models.export import (  # noqa: E402
    export_model_schemas,
    export_schema_manifest,
    get_model_registry,
)


def test_schema_export_surface_covers_all_canonical_models() -> None:
    registry = get_model_registry()
    schemas = export_model_schemas()
    manifest = export_schema_manifest()

    assert set(registry) == set(schemas)
    assert set(registry) == set(manifest)
    assert "Signal" in schemas
    assert schemas["Signal"]["type"] == "object"
    assert "signal_id" in schemas["Signal"]["properties"]
    assert manifest["Signal"] == "schemas/generated/Signal.json"
