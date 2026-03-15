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
