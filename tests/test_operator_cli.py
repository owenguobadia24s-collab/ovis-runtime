# ---
# id: TEST-OPERATOR-0001
# title: Test Operator Cli Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: operator
# repo: ovis-runtime
# path: tests/test_operator_cli.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-OPERATOR-0001.yaml
# module_id: MOD-OPERATOR-SURFACE-0001
# module_slug: operator_surface
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# related_module_ids:
# - MOD-TOOL-GATEWAY-0001
# ---
import json
from datetime import UTC, datetime
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_branch import BranchEventReference, BranchLifecycleManager, CreateBranchInput, JsonFileBranchStore  # noqa: E402
from ovis_event_log import FileEventWriter, build_root_event, emit_event  # noqa: E402
from ovis_operator import cli  # noqa: E402
from ovis_state_models import ActorType, EventType, ObjectType  # noqa: E402
from ovis_tool_gateway import CapabilityDefinition, CapabilityRegistry  # noqa: E402


class _FakeProviderAdapter:
    def __init__(self, *, response_id: str = "resp_001", output_text: str = "hello world") -> None:
        self.calls = 0
        self._response_id = response_id
        self._output_text = output_text

    def invoke(self, request, config):
        from ovis_responses_runtime import OpenAIProviderResult

        self.calls += 1
        return OpenAIProviderResult(
            provider_name="openai",
            provider_response_id=self._response_id,
            output_text=self._output_text,
            finish_reason="stop",
        )


def test_signal_create_outputs_operator_loop_input_artifact_json(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(
        [
            "signal",
            "create",
            "--text",
            "operator text",
            "--correlation-id",
            "corr_001",
            "--execution-mode-hint",
            "runtime",
            "--json",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["source_type"] == "operator"
    assert output["source_ref"] == "operator://signal/create"
    assert output["compressed_summary"] == "operator text"
    assert output["correlation_id"] == "corr_001"
    assert output["execution_mode_hint"] == "runtime"
    assert output["raw_input_hash"]


def test_branch_inspect_reads_persisted_branch_state(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    manager = BranchLifecycleManager(store=JsonFileBranchStore(tmp_path / "branches"))
    created = manager.create_branch(CreateBranchInput(root_signal_id="sig_001", correlation_id="corr_001"))
    manager.append_event(
        str(created.branch.branch_id),
        BranchEventReference(event_id="evt_001", event_type="signal.created", correlation_id="corr_001"),
    )

    exit_code = cli.main(
        [
            "branch",
            "inspect",
            "--root",
            str(tmp_path),
            "--branch-id",
            str(created.branch.branch_id),
            "--json",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["branch"]["branch_id"] == str(created.branch.branch_id)
    assert output["correlation_id"] == "corr_001"
    assert output["event_refs"][0]["event_id"] == "evt_001"


def test_event_tail_reads_recent_events(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    writer = FileEventWriter(tmp_path)
    first = build_root_event(
        event_id="evt_001",
        event_type=EventType.SIGNAL_CREATED,
        correlation_id="corr_001",
        object_type=ObjectType.SIGNAL,
        object_id="sig_001",
        branch_id="br_001",
        actor_type=ActorType.SYSTEM,
        actor_id="tester",
        created_at=datetime.now(UTC),
        payload_inline={"source": "first"},
    )
    second = build_root_event(
        event_id="evt_002",
        event_type=EventType.WORK_OBJECT_CREATED,
        correlation_id="corr_001",
        object_type=ObjectType.WORK_OBJECT,
        object_id="wo_001",
        branch_id="br_001",
        actor_type=ActorType.SYSTEM,
        actor_id="tester",
        created_at=datetime.now(UTC),
        payload_inline={"source": "second"},
    )
    emit_event(first, writer)
    emit_event(second, writer)

    exit_code = cli.main(
        [
            "event",
            "tail",
            "--root",
            str(tmp_path),
            "--date",
            datetime.now().date().isoformat(),
            "--count",
            "1",
            "--json",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert len(output) == 1
    assert output[0]["event_id"] == "evt_002"


def test_compact_invokes_canonical_executor(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    manager = BranchLifecycleManager(store=JsonFileBranchStore(tmp_path / "branches"))
    created = manager.create_branch(CreateBranchInput(root_signal_id="sig_001", correlation_id="corr_001"))
    manager.append_event(
        str(created.branch.branch_id),
        BranchEventReference(event_id="evt_001", event_type="signal.created", correlation_id="corr_001"),
    )

    exit_code = cli.main(
        [
            "compact",
            "--root",
            str(tmp_path),
            "--branch-id",
            str(created.branch.branch_id),
            "--json",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["branch_id"] == str(created.branch.branch_id)
    assert output["compaction_id"].startswith("cmp_")
    assert output["source_event_count"] == 1
    assert Path(output["artifact_path"]).exists()


def test_run_runtime_and_branch_inspect_share_file_backed_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_provider = _FakeProviderAdapter()
    monkeypatch.setattr(cli, "_build_provider_adapter", lambda: fake_provider)

    run_exit = cli.main(
        [
            "run",
            "--root",
            str(tmp_path),
            "--objective",
            "Say hello",
            "--signal-text",
            "hello signal",
            "--mode",
            "runtime",
            "--model",
            "gpt-5",
            "--json",
        ]
    )
    run_output = json.loads(capsys.readouterr().out)

    inspect_exit = cli.main(
        [
            "branch",
            "inspect",
            "--root",
            str(tmp_path),
            "--branch-id",
            run_output["branch_id"],
            "--json",
        ]
    )
    inspect_output = json.loads(capsys.readouterr().out)

    assert run_exit == 0
    assert inspect_exit == 0
    assert fake_provider.calls == 1
    assert run_output["success"] is True
    assert inspect_output["branch"]["branch_id"] == run_output["branch_id"]
    assert inspect_output["correlation_id"] == run_output["correlation_id"]


def test_run_capability_mode_uses_loop_runner_without_provider_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_provider = _FakeProviderAdapter()
    registry = CapabilityRegistry()
    registry.register(
        CapabilityDefinition(
            name="math.add",
            version="v1",
            schema_ref="schemas/math.add.json",
            side_effect_class="read-only",
        ),
        handler=lambda payload: payload["a"] + payload["b"],
    )
    monkeypatch.setattr(cli, "_build_provider_adapter", lambda: fake_provider)
    monkeypatch.setattr(cli, "DEFAULT_CAPABILITY_REGISTRY", registry)

    exit_code = cli.main(
        [
            "run",
            "--root",
            str(tmp_path),
            "--objective",
            "Add numbers",
            "--mode",
            "capability",
            "--signal-text",
            "capability signal",
            "--capability-name",
            "math.add",
            "--capability-payload-json",
            '{"a":2,"b":3}',
            "--json",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert fake_provider.calls == 0
    assert output["execution_mode"] == "capability"
    assert output["capability_result"] == 5


def test_invalid_runtime_run_fails_cleanly_without_model(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("OVIS_MODEL", raising=False)

    exit_code = cli.main(
        [
            "run",
            "--root",
            str(tmp_path),
            "--objective",
            "Missing model",
            "--mode",
            "runtime",
            "--json",
        ]
    )

    error_output = json.loads(capsys.readouterr().err)
    assert exit_code == 1
    assert error_output["error_type"] == "ValueError"
    assert "OVIS_MODEL" in error_output["message"]


def test_invalid_json_input_fails_cleanly(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = cli.main(
        [
            "run",
            "--root",
            str(tmp_path),
            "--objective",
            "Bad payload",
            "--mode",
            "capability",
            "--capability-name",
            "math.add",
            "--capability-payload-json",
            "{bad json}",
            "--json",
        ]
    )

    error_output = json.loads(capsys.readouterr().err)
    assert exit_code == 1
    assert error_output["error_type"] == "ValueError"
    assert "--capability-payload-json" in error_output["message"]


def test_signal_create_output_can_feed_directly_into_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_provider = _FakeProviderAdapter()
    monkeypatch.setattr(cli, "_build_provider_adapter", lambda: fake_provider)

    create_exit = cli.main(
        [
            "signal",
            "create",
            "--text",
            "created for run",
            "--correlation-id",
            "corr_010",
            "--execution-mode-hint",
            "runtime",
            "--json",
        ]
    )
    signal_artifact = capsys.readouterr().out.strip()

    run_exit = cli.main(
        [
            "run",
            "--root",
            str(tmp_path),
            "--objective",
            "Use the created signal",
            "--signal-json",
            signal_artifact,
            "--model",
            "gpt-5",
            "--json",
        ]
    )
    run_output = json.loads(capsys.readouterr().out)

    assert create_exit == 0
    assert run_exit == 0
    assert run_output["correlation_id"] == "corr_010"
    assert fake_provider.calls == 1
