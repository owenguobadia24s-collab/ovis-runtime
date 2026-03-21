# ---
# id: TEST-RUNTIME-0007
# title: Test Runtime Session Modes Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: runtime
# repo: ovis-runtime
# path: tests/test_runtime_session_modes.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-RUNTIME-0007.yaml
# module_id: MOD-RUNTIME-GATEWAY-0001
# module_slug: runtime_gateway
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_responses_runtime import SessionMode, default_session_config  # noqa: E402


def test_session_mode_enum_exposes_expected_values() -> None:
    assert SessionMode.ZDR_FIRST == "zdr-first"
    assert SessionMode.DURABLE_OPTIONAL == "durable-optional"
    assert SessionMode.DURABLE_PROHIBITED == "durable-prohibited"


def test_default_session_mode_is_canonical() -> None:
    assert default_session_config().session_mode == SessionMode.ZDR_FIRST
