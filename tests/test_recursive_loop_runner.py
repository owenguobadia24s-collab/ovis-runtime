from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_branch import BranchStatus  # noqa: E402
from ovis_event_log import MemoryEventWriter  # noqa: E402
from ovis_loop import (  # noqa: E402
    LoopApprovalInput,
    LoopExecutionMode,
    LoopRequest,
    LoopSignalInput,
    LoopStage,
    RecursiveLoopRunner,
)
from ovis_responses_runtime import (  # noqa: E402
    OpenAIProviderResult,
    RuntimeAdapterConfig,
    RuntimeModelConfig,
    RuntimeSessionConfig,
    SessionMode,
)
from ovis_state_models import PolicyProfile, RiskClass  # noqa: E402
from ovis_tool_gateway import CapabilityDefinition, CapabilityRegistry, PolicyDecision  # noqa: E402


class _FakeProviderAdapter:
    def __init__(self, result: OpenAIProviderResult | Exception) -> None:
        self._result = result
        self.calls = 0

    def invoke(self, request, config):
        self.calls += 1
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


class _DenyPolicyHook:
    def evaluate(self, request, definition):
        return PolicyDecision(
            disposition="deny",
            risk_class="R2",
            policy_profile="human-approved",
            approval_required=True,
            rationale="Denied by policy.",
        )


def _runtime_config() -> RuntimeAdapterConfig:
    return RuntimeAdapterConfig(
        model=RuntimeModelConfig(model_name="gpt-5"),
        session=RuntimeSessionConfig(
            session_mode=SessionMode.ZDR_FIRST,
            store_enabled=False,
            durable_state_allowed=False,
        ),
    )


def _approval(approved: bool = True) -> LoopApprovalInput:
    return LoopApprovalInput(
        approved=approved,
        reviewer_id="reviewer_001",
        rationale="Looks good." if approved else "Stop here.",
        risk_class=RiskClass.R1,
        policy_profile=PolicyProfile.HUMAN_APPROVED,
        approval_scope="loop-run",
    )


def _signal_input(label: str = "001") -> LoopSignalInput:
    return LoopSignalInput(
        source_type="test",
        source_ref=f"signal://{label}",
        raw_input_ref=f"raw://{label}",
        raw_input_hash=None,
        compressed_summary=f"summary-{label}",
        extracted_signals=("signal",),
    )


def test_new_branch_runtime_path_succeeds_and_appends_events_in_order(tmp_path: Path) -> None:
    writer = MemoryEventWriter()
    provider = _FakeProviderAdapter(
        OpenAIProviderResult(
            provider_name="openai",
            provider_response_id="resp_001",
            output_text="hello",
            finish_reason="stop",
        )
    )
    runner = RecursiveLoopRunner(
        event_writer=writer,
        runtime_config=_runtime_config(),
        capability_registry=CapabilityRegistry(),
        runtime_provider_adapter=provider,
        compaction_artifact_root=tmp_path / "compactions",
    )

    result = runner.run(
        LoopRequest(
            signal=_signal_input(),
            objective="Answer the request",
            execution_mode=LoopExecutionMode.RUNTIME,
            runtime_input={"prompt": "hello"},
            approval=_approval(),
        )
    )

    assert provider.calls == 1
    assert result.success is True
    assert result.execution_succeeded is True
    assert result.runtime_response is not None
    assert result.capability_result is None
    assert result.branch_id.startswith("br_")
    assert result.correlation_id.startswith("corr_")
    assert result.branch_state.correlation_id == result.correlation_id
    assert [event.event_type for event in result.branch_state.event_refs] == [
        "signal.created",
        "work_object.created",
        "plan_job.created",
        "approval.recorded",
        "execute_job.created",
        "execute_job.status_changed",
        "work_object.updated",
        "runtime.requested",
        "runtime.response_received",
        "execute_job.status_changed",
        "work_object.updated",
    ]
    assert all(not str(record["event_type"]).startswith("loop.") for record in writer.records())


def test_new_branch_capability_path_succeeds_without_provider_bypass(tmp_path: Path) -> None:
    writer = MemoryEventWriter()
    provider = _FakeProviderAdapter(
        OpenAIProviderResult(
            provider_name="openai",
            provider_response_id="resp_unused",
            output_text="unused",
            finish_reason="stop",
        )
    )
    registry = CapabilityRegistry()
    calls: list[dict[str, object]] = []

    def add_handler(payload: dict[str, object]) -> int:
        calls.append(payload)
        return int(payload["a"]) + int(payload["b"])

    registry.register(
        CapabilityDefinition(
            name="math.add",
            version="v1",
            schema_ref="schemas/math.add.json",
            side_effect_class="read-only",
        ),
        handler=add_handler,
    )
    runner = RecursiveLoopRunner(
        event_writer=writer,
        runtime_config=_runtime_config(),
        capability_registry=registry,
        runtime_provider_adapter=provider,
        compaction_artifact_root=tmp_path / "compactions",
    )

    result = runner.run(
        LoopRequest(
            signal=_signal_input(),
            objective="Add two numbers",
            execution_mode=LoopExecutionMode.CAPABILITY,
            capability_name="math.add",
            capability_payload={"a": 2, "b": 3},
            approval=_approval(),
        )
    )

    assert provider.calls == 0
    assert calls == [{"a": 2, "b": 3}]
    assert result.success is True
    assert result.capability_result is not None
    assert result.capability_result.result_payload == 5
    assert [event.event_type for event in result.branch_state.event_refs] == [
        "signal.created",
        "work_object.created",
        "plan_job.created",
        "approval.recorded",
        "execute_job.created",
        "execute_job.status_changed",
        "work_object.updated",
        "capability.requested",
        "capability.completed",
        "execute_job.status_changed",
        "work_object.updated",
    ]


def test_existing_branch_continuation_preserves_branch_and_grows_event_refs(tmp_path: Path) -> None:
    writer = MemoryEventWriter()
    provider = _FakeProviderAdapter(
        OpenAIProviderResult(
            provider_name="openai",
            provider_response_id="resp_001",
            output_text="hello",
            finish_reason="stop",
        )
    )
    runner = RecursiveLoopRunner(
        event_writer=writer,
        runtime_config=_runtime_config(),
        capability_registry=CapabilityRegistry(),
        runtime_provider_adapter=provider,
        compaction_artifact_root=tmp_path / "compactions",
    )

    first = runner.run(
        LoopRequest(
            signal=_signal_input("001"),
            objective="First turn",
            correlation_id="corr_001",
            execution_mode=LoopExecutionMode.RUNTIME,
            runtime_input={"prompt": "hello"},
            approval=_approval(),
        )
    )
    second = runner.run(
        LoopRequest(
            signal=_signal_input("002"),
            objective="Second turn",
            branch_id=first.branch_id,
            execution_mode=LoopExecutionMode.RUNTIME,
            runtime_input={"prompt": "again"},
            approval=_approval(),
        )
    )

    assert second.branch_id == first.branch_id
    assert second.correlation_id == "corr_001"
    assert len(second.branch_state.event_refs) > len(first.branch_state.event_refs)


def test_approval_denial_stops_before_execute_job(tmp_path: Path) -> None:
    writer = MemoryEventWriter()
    provider = _FakeProviderAdapter(
        OpenAIProviderResult(
            provider_name="openai",
            provider_response_id="resp_unused",
            output_text="unused",
            finish_reason="stop",
        )
    )
    runner = RecursiveLoopRunner(
        event_writer=writer,
        runtime_config=_runtime_config(),
        capability_registry=CapabilityRegistry(),
        runtime_provider_adapter=provider,
        compaction_artifact_root=tmp_path / "compactions",
    )

    result = runner.run(
        LoopRequest(
            signal=_signal_input(),
            objective="Denied turn",
            execution_mode=LoopExecutionMode.RUNTIME,
            runtime_input={"prompt": "hello"},
            approval=_approval(approved=False),
        )
    )

    assert result.success is False
    assert result.error_stage == LoopStage.APPROVAL
    assert result.execute_job is None
    assert provider.calls == 0
    assert [event.event_type for event in result.branch_state.event_refs] == [
        "signal.created",
        "work_object.created",
        "plan_job.created",
        "approval.recorded",
        "work_object.updated",
    ]


def test_runtime_failure_is_surfaced_and_branch_continuity_stays_honest(tmp_path: Path) -> None:
    writer = MemoryEventWriter()
    provider = _FakeProviderAdapter(RuntimeError("provider failure"))
    runner = RecursiveLoopRunner(
        event_writer=writer,
        runtime_config=_runtime_config(),
        capability_registry=CapabilityRegistry(),
        runtime_provider_adapter=provider,
        compaction_artifact_root=tmp_path / "compactions",
    )

    result = runner.run(
        LoopRequest(
            signal=_signal_input(),
            objective="Failing runtime turn",
            execution_mode=LoopExecutionMode.RUNTIME,
            runtime_input={"prompt": "hello"},
            approval=_approval(),
        )
    )

    assert result.success is False
    assert result.execution_succeeded is False
    assert result.error_stage == LoopStage.EXECUTION
    assert result.execute_job is not None
    assert result.execute_job.status == "failed"
    assert result.work_object.status == "failed"
    assert [event.event_type for event in result.branch_state.event_refs][-4:] == [
        "runtime.requested",
        "runtime.error",
        "execute_job.status_changed",
        "work_object.updated",
    ]


@pytest.mark.parametrize(
    ("policy_hook", "handler", "expected_execute_status", "expected_work_status", "expected_subsystem_event"),
    [
        (_DenyPolicyHook(), lambda payload: payload, "cancelled", "blocked", "capability.error"),
        (None, lambda payload: (_ for _ in ()).throw(RuntimeError("boom")), "failed", "failed", "capability.error"),
    ],
)
def test_capability_blocked_and_error_are_surfaced_honestly(
    tmp_path: Path,
    policy_hook,
    handler,
    expected_execute_status: str,
    expected_work_status: str,
    expected_subsystem_event: str,
) -> None:
    writer = MemoryEventWriter()
    registry = CapabilityRegistry()
    registry.register(
        CapabilityDefinition(
            name="echo.return",
            version="v1",
            schema_ref="schemas/echo.return.json",
            side_effect_class="read-only",
        ),
        handler=handler,
    )
    runner = RecursiveLoopRunner(
        event_writer=writer,
        runtime_config=_runtime_config(),
        capability_registry=registry,
        capability_policy_hook=policy_hook,
        compaction_artifact_root=tmp_path / "compactions",
    )

    result = runner.run(
        LoopRequest(
            signal=_signal_input(),
            objective="Capability branch",
            execution_mode=LoopExecutionMode.CAPABILITY,
            capability_name="echo.return",
            capability_payload={"value": "hello"},
            approval=_approval(),
        )
    )

    assert result.success is False
    assert result.execution_succeeded is False
    assert result.error_stage == LoopStage.EXECUTION
    assert result.execute_job is not None
    assert result.execute_job.status == expected_execute_status
    assert result.work_object.status == expected_work_status
    assert expected_subsystem_event in [event.event_type for event in result.branch_state.event_refs]


def test_compact_after_run_triggers_compaction_after_success(tmp_path: Path) -> None:
    writer = MemoryEventWriter()
    provider = _FakeProviderAdapter(
        OpenAIProviderResult(
            provider_name="openai",
            provider_response_id="resp_001",
            output_text="hello",
            finish_reason="stop",
        )
    )
    runner = RecursiveLoopRunner(
        event_writer=writer,
        runtime_config=_runtime_config(),
        capability_registry=CapabilityRegistry(),
        runtime_provider_adapter=provider,
        compaction_artifact_root=tmp_path / "compactions",
    )

    result = runner.run(
        LoopRequest(
            signal=_signal_input(),
            objective="Compact this branch",
            execution_mode=LoopExecutionMode.RUNTIME,
            runtime_input={"prompt": "hello"},
            approval=_approval(),
            compact_after_run=True,
        )
    )

    assert result.success is True
    assert result.compaction_response is not None
    assert result.branch_state.branch.current_state_ref.endswith(".json")
    assert result.branch_state.branch.latest_compaction_id == result.compaction_response.record.compaction_id
    assert result.branch_state.event_refs[-1].event_type == "compaction.created"


def test_compaction_failure_does_not_erase_execution_success(tmp_path: Path) -> None:
    writer = MemoryEventWriter()
    provider = _FakeProviderAdapter(
        OpenAIProviderResult(
            provider_name="openai",
            provider_response_id="resp_001",
            output_text="hello",
            finish_reason="stop",
        )
    )
    runner = RecursiveLoopRunner(
        event_writer=writer,
        runtime_config=_runtime_config(),
        capability_registry=CapabilityRegistry(),
        runtime_provider_adapter=provider,
        compaction_artifact_root=tmp_path / "compactions",
    )

    class _FailingCompactor:
        def compact_branch(self, branch_id, trigger, correlation_id=None, parent_event_id=None):
            raise RuntimeError("compaction failure")

    runner._compaction_executor = _FailingCompactor()  # type: ignore[attr-defined]

    result = runner.run(
        LoopRequest(
            signal=_signal_input(),
            objective="Fail compaction only",
            execution_mode=LoopExecutionMode.RUNTIME,
            runtime_input={"prompt": "hello"},
            approval=_approval(),
            compact_after_run=True,
        )
    )

    assert result.execution_succeeded is True
    assert result.success is False
    assert result.error_stage == LoopStage.COMPACTION
    assert result.compaction_response is None


def test_close_branch_after_run_closes_only_after_optional_compaction(tmp_path: Path) -> None:
    writer = MemoryEventWriter()
    provider = _FakeProviderAdapter(
        OpenAIProviderResult(
            provider_name="openai",
            provider_response_id="resp_001",
            output_text="hello",
            finish_reason="stop",
        )
    )
    runner = RecursiveLoopRunner(
        event_writer=writer,
        runtime_config=_runtime_config(),
        capability_registry=CapabilityRegistry(),
        runtime_provider_adapter=provider,
        compaction_artifact_root=tmp_path / "compactions",
    )

    result = runner.run(
        LoopRequest(
            signal=_signal_input(),
            objective="Close branch on success",
            execution_mode=LoopExecutionMode.RUNTIME,
            runtime_input={"prompt": "hello"},
            approval=_approval(),
            compact_after_run=True,
            close_branch_after_run=True,
        )
    )

    assert result.success is True
    assert result.branch_state.branch.status == BranchStatus.CLOSED
