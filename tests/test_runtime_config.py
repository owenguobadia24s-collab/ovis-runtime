# ---
# id: TEST-RUNTIME-0004
# title: Test Runtime Config Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: runtime
# repo: ovis-runtime
# path: tests/test_runtime_config.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-RUNTIME-0004.yaml
# module_id: MOD-RUNTIME-GATEWAY-0001
# module_slug: runtime_gateway
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_responses_runtime import (  # noqa: E402
    RuntimeAdapterConfig,
    RuntimeModelConfig,
    RuntimeSessionConfig,
    SessionMode,
    default_session_config,
)


def test_runtime_config_structures_are_constructible() -> None:
    session = RuntimeSessionConfig(
        session_mode=SessionMode.DURABLE_OPTIONAL,
        store_enabled=True,
        durable_state_allowed=True,
    )
    config = RuntimeAdapterConfig(
        model=RuntimeModelConfig(model_name="gpt-test"),
        session=session,
    )

    assert config.model.model_name == "gpt-test"
    assert config.session.session_mode == SessionMode.DURABLE_OPTIONAL


def test_default_session_config_is_zdr_first() -> None:
    default_config = default_session_config()

    assert default_config.session_mode == SessionMode.ZDR_FIRST
    assert default_config.store_enabled is False
    assert default_config.durable_state_allowed is False
