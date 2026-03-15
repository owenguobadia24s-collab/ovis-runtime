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
