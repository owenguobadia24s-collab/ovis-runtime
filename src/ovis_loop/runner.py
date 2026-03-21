# ---
# id: MODULE-LOOP-0002
# title: Runner Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: loop
# repo: ovis-runtime
# path: src/ovis_loop/runner.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-LOOP-0002.yaml
# module_id: MOD-PLANNING-EXECUTION-LOOP-0001
# module_slug: planning_execution_loop
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""Thin orchestration runner for one governed branch cycle."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from ovis_branch import (
    BranchEventReference,
    BranchLifecycleManager,
    BranchState,
    BranchStore,
    CreateBranchInput,
)
from ovis_branch_compaction import BranchCompactionExecutor, CompactionHooks, CompactionResponse, CompactionTriggerClass
from ovis_event_log import (
    AppendOnlyEventWriter,
    BRANCH_EVENT_FAMILIES,
    build_root_event,
    emit_event,
)
from ovis_event_log.writer import EventAppendReceipt, PersistedEventRecord
from ovis_ids import (
    generate_approval_id,
    generate_correlation_id,
    generate_execute_job_id,
    generate_event_id,
    generate_plan_job_id,
    generate_signal_id,
    generate_work_object_id,
)
from ovis_responses_runtime import (
    OpenAIResponsesProviderAdapter,
    RuntimeAdapter,
    RuntimeAdapterConfig,
    RuntimeHooks,
    RuntimeRequest,
    RuntimeTurnContext,
)
from ovis_state_models import (
    ActorType,
    Approval,
    ApprovalDecision,
    EventType,
    ExecuteJob,
    ExecuteJobStatus,
    ObjectType,
    PlanJob,
    PlanJobStatus,
    Signal,
    WorkObject,
    WorkObjectStatus,
)
from ovis_tool_gateway import CapabilityDispatcher, CapabilityRegistry, ExecutionRequest, ExecutionResultEnvelope, PolicyHook

from .types import (
    LoopApprovalInput,
    LoopExecutionMode,
    LoopRequest,
    LoopResult,
    LoopSignalInput,
    LoopStage,
)

_LOOP_ACTOR_ID = "ovis_loop.runner"


class RecordingEventWriter:
    """Internal wrapper that records already-persisted event records in write order."""

    def __init__(self, base_writer: AppendOnlyEventWriter) -> None:
        self._base_writer = base_writer
        self._records: list[PersistedEventRecord] = []
        self._last_persisted_record: PersistedEventRecord | None = None

    def append(self, event) -> EventAppendReceipt:
        receipt = self._base_writer.append(event)
        if not hasattr(self._base_writer, "get_last_persisted_record"):
            raise TypeError("RecordingEventWriter requires a base writer with get_last_persisted_record().")
        persisted_record = self._base_writer.get_last_persisted_record()
        if persisted_record is None:
            raise RuntimeError("Base writer did not expose the persisted record after append().")
        self._last_persisted_record = deepcopy(persisted_record)
        self._records.append(deepcopy(persisted_record))
        return receipt

    def append_many(self, events) -> tuple[EventAppendReceipt, ...]:
        return tuple(self.append(event) for event in events)

    def get_last_persisted_record(self) -> PersistedEventRecord | None:
        return deepcopy(self._last_persisted_record)

    def checkpoint(self) -> int:
        return len(self._records)

    def records_since(self, checkpoint: int) -> tuple[PersistedEventRecord, ...]:
        return tuple(deepcopy(record) for record in self._records[checkpoint:])


class RecursiveLoopRunner:
    """Compose the authoritative OVIS subsystems into one thin governed loop."""

    def __init__(
        self,
        *,
        event_writer: AppendOnlyEventWriter,
        runtime_config: RuntimeAdapterConfig,
        capability_registry: CapabilityRegistry,
        runtime_provider_adapter: OpenAIResponsesProviderAdapter | None = None,
        capability_policy_hook: PolicyHook | None = None,
        branch_store: BranchStore | None = None,
        compaction_artifact_root: Path | str = "compactions",
    ) -> None:
        self._recording_writer = RecordingEventWriter(event_writer)
        self._branch_lifecycle = BranchLifecycleManager(
            store=branch_store,
            event_writer=self._recording_writer,
        )
        self._runtime_adapter = RuntimeAdapter(
            config=runtime_config,
            hooks=RuntimeHooks(event_writer=self._recording_writer),
            provider_adapter=runtime_provider_adapter,
        )
        self._capability_dispatcher = CapabilityDispatcher(
            registry=capability_registry,
            policy_hook=capability_policy_hook,
            event_writer=self._recording_writer,
        )
        self._compaction_executor = BranchCompactionExecutor(
            branch_lifecycle=self._branch_lifecycle,
            artifact_root=compaction_artifact_root,
            hooks=CompactionHooks(event_writer=self._recording_writer),
        )
        self._runtime_config = runtime_config

    def run(self, request: LoopRequest) -> LoopResult:
        approval_input = self._require_approval(request.approval)
        self._validate_request_shape(request)

        signal_id = str(generate_signal_id())
        branch_state, branch_id, correlation_id = self._resolve_branch_state(request, signal_id=signal_id)
        signal = self._build_signal(request.signal, branch_id=branch_id, signal_id=signal_id)
        branch_state = self._persist_event_and_append_ref(
            branch_id=branch_id,
            correlation_id=correlation_id,
            event_type=EventType.SIGNAL_CREATED,
            object_type=ObjectType.SIGNAL,
            object_id=str(signal.signal_id),
            payload_inline={
                "source_type": signal.source_type,
                "source_ref": signal.source_ref,
            },
        )

        timestamp = datetime.now(UTC)
        work_object = WorkObject(
            work_object_id=generate_work_object_id(),
            title=request.title or request.objective,
            objective=request.objective,
            status=WorkObjectStatus.AWAITING_REVIEW,
            priority=request.priority,
            branch_id=branch_id,
            parent_signal_ids=(signal.signal_id,),
            owner=request.owner,
            created_at=timestamp,
            updated_at=timestamp,
        )
        branch_state = self._persist_event_and_append_ref(
            branch_id=branch_id,
            correlation_id=correlation_id,
            event_type=EventType.WORK_OBJECT_CREATED,
            object_type=ObjectType.WORK_OBJECT,
            object_id=str(work_object.work_object_id),
            payload_inline={
                "title": work_object.title,
                "status": str(work_object.status),
            },
        )

        plan_job = PlanJob(
            plan_job_id=generate_plan_job_id(),
            work_object_id=work_object.work_object_id,
            status=PlanJobStatus.READY_FOR_REVIEW,
            objective=request.objective,
            assumptions=(),
            constraints=(),
            output_ref=None,
            created_at=timestamp,
            updated_at=timestamp,
        )
        work_object = work_object.model_copy(
            update={
                "current_plan_id": plan_job.plan_job_id,
                "updated_at": datetime.now(UTC),
            }
        )
        branch_state = self._persist_event_and_append_ref(
            branch_id=branch_id,
            correlation_id=correlation_id,
            event_type=EventType.PLAN_JOB_CREATED,
            object_type=ObjectType.PLAN_JOB,
            object_id=str(plan_job.plan_job_id),
            payload_inline={"status": str(plan_job.status)},
        )

        approval = self._build_approval(approval_input, plan_job_id=str(plan_job.plan_job_id))
        branch_state = self._persist_event_and_append_ref(
            branch_id=branch_id,
            correlation_id=correlation_id,
            event_type=EventType.APPROVAL_RECORDED,
            object_type=ObjectType.APPROVAL,
            object_id=str(approval.approval_id),
            payload_inline={
                "decision": str(approval.decision),
                "policy_profile": str(approval.policy_profile),
                "risk_class": str(approval.risk_class),
            },
        )

        if approval.decision == ApprovalDecision.REJECT:
            plan_job = plan_job.model_copy(
                update={
                    "status": PlanJobStatus.REJECTED,
                    "updated_at": datetime.now(UTC),
                }
            )
            work_object = work_object.model_copy(
                update={
                    "status": WorkObjectStatus.BLOCKED,
                    "updated_at": datetime.now(UTC),
                }
            )
            branch_state = self._persist_event_and_append_ref(
                branch_id=branch_id,
                correlation_id=correlation_id,
                event_type=EventType.WORK_OBJECT_UPDATED,
                object_type=ObjectType.WORK_OBJECT,
                object_id=str(work_object.work_object_id),
                payload_inline={"status": str(work_object.status)},
            )
            return LoopResult(
                branch_id=branch_id,
                correlation_id=correlation_id,
                execution_mode=request.execution_mode,
                success=False,
                execution_succeeded=False,
                approval=approval,
                signal=signal,
                work_object=work_object,
                plan_job=plan_job,
                execute_job=None,
                runtime_response=None,
                capability_result=None,
                compaction_response=None,
                branch_state=branch_state,
                error_stage=LoopStage.APPROVAL,
                error_message=approval.rationale,
            )

        plan_job = plan_job.model_copy(
            update={
                "status": PlanJobStatus.APPROVED,
                "updated_at": datetime.now(UTC),
            }
        )
        execute_job = ExecuteJob(
            execute_job_id=generate_execute_job_id(),
            work_object_id=work_object.work_object_id,
            parent_plan_job_id=plan_job.plan_job_id,
            status=ExecuteJobStatus.READY,
            job_kind=str(request.execution_mode),
            execution_profile=(
                self._runtime_config.model.model_name
                if request.execution_mode == LoopExecutionMode.RUNTIME
                else self._require_capability_name(request.capability_name)
            ),
            input_ref=None,
            output_ref=None,
            run_id=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        work_object = work_object.model_copy(
            update={
                "current_execute_job_id": execute_job.execute_job_id,
                "updated_at": datetime.now(UTC),
            }
        )
        branch_state = self._persist_event_and_append_ref(
            branch_id=branch_id,
            correlation_id=correlation_id,
            event_type=EventType.EXECUTE_JOB_CREATED,
            object_type=ObjectType.EXECUTE_JOB,
            object_id=str(execute_job.execute_job_id),
            payload_inline={
                "status": str(execute_job.status),
                "job_kind": execute_job.job_kind,
                "execution_profile": execute_job.execution_profile,
            },
        )

        execute_job = execute_job.model_copy(
            update={
                "status": ExecuteJobStatus.RUNNING,
                "updated_at": datetime.now(UTC),
            }
        )
        branch_state = self._persist_event_and_append_ref(
            branch_id=branch_id,
            correlation_id=correlation_id,
            event_type=EventType.EXECUTE_JOB_STATUS_CHANGED,
            object_type=ObjectType.EXECUTE_JOB,
            object_id=str(execute_job.execute_job_id),
            payload_inline={"status": str(execute_job.status)},
        )

        work_object = work_object.model_copy(
            update={
                "status": WorkObjectStatus.EXECUTING,
                "updated_at": datetime.now(UTC),
            }
        )
        branch_state = self._persist_event_and_append_ref(
            branch_id=branch_id,
            correlation_id=correlation_id,
            event_type=EventType.WORK_OBJECT_UPDATED,
            object_type=ObjectType.WORK_OBJECT,
            object_id=str(work_object.work_object_id),
            payload_inline={"status": str(work_object.status)},
        )

        runtime_response: RuntimeResponse | None = None
        capability_result: ExecutionResultEnvelope | None = None
        execution_succeeded = False
        error_message: str | None = None

        subsystem_checkpoint = self._recording_writer.checkpoint()
        if request.execution_mode == LoopExecutionMode.RUNTIME:
            try:
                runtime_response = self._runtime_adapter.invoke(
                    RuntimeRequest(
                        input_payload=dict(request.runtime_input or {}),
                        turn_context=RuntimeTurnContext(
                            branch_id=branch_id,
                            correlation_id=correlation_id,
                            object_context=self._execution_object_context(work_object, plan_job, execute_job),
                        ),
                    )
                )
                execution_succeeded = True
            except Exception as exc:
                error_message = str(exc)
        else:
            capability_result = self._capability_dispatcher.execute(
                ExecutionRequest(
                    capability_name=self._require_capability_name(request.capability_name),
                    input_payload=dict(request.capability_payload or {}),
                    correlation_id=correlation_id,
                    idempotency_key=str(execute_job.execute_job_id),
                    object_context=self._execution_object_context(work_object, plan_job, execute_job),
                    branch_context={"branch_id": branch_id},
                )
            )
            if capability_result.execution_status == "success":
                execution_succeeded = True
            else:
                error_message = capability_result.error_details or capability_result.execution_status

        branch_state = self._append_persisted_records_to_branch(
            branch_id=branch_id,
            records=self._recording_writer.records_since(subsystem_checkpoint),
        )

        if request.execution_mode == LoopExecutionMode.RUNTIME:
            if execution_succeeded and runtime_response is not None:
                execute_job = execute_job.model_copy(
                    update={
                        "status": ExecuteJobStatus.COMPLETED,
                        "output_ref": runtime_response.provider_response_ref,
                        "updated_at": datetime.now(UTC),
                    }
                )
                work_object = work_object.model_copy(
                    update={
                        "status": WorkObjectStatus.COMPLETED,
                        "updated_at": datetime.now(UTC),
                    }
                )
            else:
                execute_job = execute_job.model_copy(
                    update={
                        "status": ExecuteJobStatus.FAILED,
                        "updated_at": datetime.now(UTC),
                    }
                )
                work_object = work_object.model_copy(
                    update={
                        "status": WorkObjectStatus.FAILED,
                        "updated_at": datetime.now(UTC),
                    }
                )
        else:
            assert capability_result is not None
            if capability_result.execution_status == "success":
                execute_job = execute_job.model_copy(
                    update={
                        "status": ExecuteJobStatus.COMPLETED,
                        "output_ref": capability_result.output_ref,
                        "updated_at": datetime.now(UTC),
                    }
                )
                work_object = work_object.model_copy(
                    update={
                        "status": WorkObjectStatus.COMPLETED,
                        "updated_at": datetime.now(UTC),
                    }
                )
            elif capability_result.execution_status == "blocked":
                execute_job = execute_job.model_copy(
                    update={
                        "status": ExecuteJobStatus.CANCELLED,
                        "updated_at": datetime.now(UTC),
                    }
                )
                work_object = work_object.model_copy(
                    update={
                        "status": WorkObjectStatus.BLOCKED,
                        "updated_at": datetime.now(UTC),
                    }
                )
            else:
                execute_job = execute_job.model_copy(
                    update={
                        "status": ExecuteJobStatus.FAILED,
                        "updated_at": datetime.now(UTC),
                    }
                )
                work_object = work_object.model_copy(
                    update={
                        "status": WorkObjectStatus.FAILED,
                        "updated_at": datetime.now(UTC),
                    }
                )

        branch_state = self._persist_event_and_append_ref(
            branch_id=branch_id,
            correlation_id=correlation_id,
            event_type=EventType.EXECUTE_JOB_STATUS_CHANGED,
            object_type=ObjectType.EXECUTE_JOB,
            object_id=str(execute_job.execute_job_id),
            payload_inline={"status": str(execute_job.status)},
        )
        branch_state = self._persist_event_and_append_ref(
            branch_id=branch_id,
            correlation_id=correlation_id,
            event_type=EventType.WORK_OBJECT_UPDATED,
            object_type=ObjectType.WORK_OBJECT,
            object_id=str(work_object.work_object_id),
            payload_inline={"status": str(work_object.status)},
        )

        compaction_response: CompactionResponse | None = None
        error_stage: LoopStage | None = None
        success = execution_succeeded
        if not execution_succeeded:
            error_stage = LoopStage.EXECUTION
            success = False

        if request.compact_after_run and execution_succeeded:
            compaction_checkpoint = self._recording_writer.checkpoint()
            try:
                compaction_response = self._compaction_executor.compact_branch(
                    branch_id=branch_id,
                    trigger=CompactionTriggerClass.EXECUTION_MILESTONE,
                    correlation_id=correlation_id,
                )
                branch_state = self._append_persisted_records_to_branch(
                    branch_id=branch_id,
                    records=self._recording_writer.records_since(compaction_checkpoint),
                )
            except Exception as exc:
                success = False
                error_stage = LoopStage.COMPACTION
                error_message = str(exc)
                branch_state = self._branch_lifecycle.get_branch(branch_id)

        if request.close_branch_after_run and execution_succeeded and (not request.compact_after_run or compaction_response is not None):
            branch_state = self._branch_lifecycle.close_branch(branch_id)

        return LoopResult(
            branch_id=branch_id,
            correlation_id=correlation_id,
            execution_mode=request.execution_mode,
            success=success,
            execution_succeeded=execution_succeeded,
            approval=approval,
            signal=signal,
            work_object=work_object,
            plan_job=plan_job,
            execute_job=execute_job,
            runtime_response=runtime_response,
            capability_result=capability_result,
            compaction_response=compaction_response,
            branch_state=branch_state,
            error_stage=error_stage,
            error_message=error_message,
        )

    def _resolve_branch_state(
        self,
        request: LoopRequest,
        *,
        signal_id: str,
    ) -> tuple[BranchState, str, str]:
        if request.branch_id is None:
            correlation_id = request.correlation_id or str(generate_correlation_id())
            state = self._branch_lifecycle.create_branch(
                CreateBranchInput(
                    root_signal_id=signal_id,
                    correlation_id=correlation_id,
                )
            )
            return state, str(state.branch.branch_id), correlation_id

        state = self._branch_lifecycle.get_branch(request.branch_id)
        branch_id = str(state.branch.branch_id)
        if state.correlation_id is not None:
            if request.correlation_id is not None and request.correlation_id != state.correlation_id:
                raise ValueError("LoopRequest.correlation_id must match the authoritative branch correlation_id.")
            return state, branch_id, state.correlation_id

        return state, branch_id, request.correlation_id or str(generate_correlation_id())

    def _build_signal(self, signal_input: Signal | LoopSignalInput, *, branch_id: str, signal_id: str) -> Signal:
        if isinstance(signal_input, Signal):
            source_type = signal_input.source_type
            source_ref = signal_input.source_ref
            raw_input_ref = signal_input.raw_input_ref
            raw_input_hash = signal_input.raw_input_hash
            compressed_summary = signal_input.compressed_summary
            extracted_signals = signal_input.extracted_signals
            nuance = signal_input.nuance
            created_by = signal_input.created_by
        else:
            source_type = signal_input.source_type
            source_ref = signal_input.source_ref
            raw_input_ref = signal_input.raw_input_ref
            raw_input_hash = signal_input.raw_input_hash
            compressed_summary = signal_input.compressed_summary
            extracted_signals = signal_input.extracted_signals
            nuance = signal_input.nuance
            created_by = signal_input.created_by

        return Signal(
            signal_id=signal_id,
            source_type=source_type,
            source_ref=source_ref,
            raw_input_ref=raw_input_ref,
            raw_input_hash=raw_input_hash,
            compressed_summary=compressed_summary,
            extracted_signals=extracted_signals,
            nuance=nuance,
            branch_id=branch_id,
            created_at=datetime.now(UTC),
            created_by=created_by,
        )

    def _build_approval(self, approval_input: LoopApprovalInput, *, plan_job_id: str) -> Approval:
        return Approval(
            approval_id=generate_approval_id(),
            target_object_type=ObjectType.PLAN_JOB,
            target_object_id=plan_job_id,
            decision=ApprovalDecision.APPROVE if approval_input.approved else ApprovalDecision.REJECT,
            rationale=approval_input.rationale,
            reviewer_id=approval_input.reviewer_id,
            risk_class=approval_input.risk_class,
            policy_profile=approval_input.policy_profile,
            approval_scope=approval_input.approval_scope,
            expires_at=approval_input.expires_at,
            created_at=datetime.now(UTC),
        )

    def _persist_event_and_append_ref(
        self,
        *,
        branch_id: str,
        correlation_id: str,
        event_type: EventType,
        object_type: ObjectType,
        object_id: str,
        payload_inline: Mapping[str, object],
    ) -> BranchState:
        persisted_record = emit_event(
            build_root_event(
                event_id=generate_event_id(),
                event_type=event_type,
                correlation_id=correlation_id,
                object_type=object_type,
                object_id=object_id,
                branch_id=branch_id,
                actor_type=ActorType.SYSTEM,
                actor_id=_LOOP_ACTOR_ID,
                created_at=datetime.now(UTC),
                payload_inline=payload_inline,
            ),
            self._recording_writer,
        )
        return self._branch_lifecycle.append_event(branch_id, self._record_to_branch_ref(persisted_record))

    def _append_persisted_records_to_branch(
        self,
        *,
        branch_id: str,
        records: tuple[PersistedEventRecord, ...],
    ) -> BranchState:
        state = self._branch_lifecycle.get_branch(branch_id)
        for record in records:
            if str(record["event_type"]) in {str(event_type) for event_type in BRANCH_EVENT_FAMILIES}:
                continue
            state = self._branch_lifecycle.append_event(branch_id, self._record_to_branch_ref(record))
        return state

    def _record_to_branch_ref(self, record: PersistedEventRecord) -> BranchEventReference:
        timestamp = record.get("timestamp")
        created_at = datetime.fromisoformat(str(timestamp)) if timestamp is not None else None
        return BranchEventReference(
            event_id=str(record["event_id"]),
            event_type=str(record["event_type"]),
            created_at=created_at,
            correlation_id=str(record["correlation_id"]) if record.get("correlation_id") is not None else None,
        )

    def _execution_object_context(
        self,
        work_object: WorkObject,
        plan_job: PlanJob,
        execute_job: ExecuteJob,
    ) -> dict[str, str]:
        return {
            "work_object_id": str(work_object.work_object_id),
            "plan_job_id": str(plan_job.plan_job_id),
            "execute_job_id": str(execute_job.execute_job_id),
        }

    def _require_approval(self, approval: LoopApprovalInput | None) -> LoopApprovalInput:
        if approval is None:
            raise ValueError("LoopRequest.approval is required.")
        return approval

    def _require_capability_name(self, capability_name: str | None) -> str:
        if not capability_name:
            raise ValueError("LoopRequest.capability_name is required for capability execution.")
        return capability_name

    def _validate_request_shape(self, request: LoopRequest) -> None:
        if request.execution_mode == LoopExecutionMode.RUNTIME:
            if request.runtime_input is None:
                raise ValueError("LoopRequest.runtime_input is required for runtime execution.")
            return
        if request.capability_name is None:
            raise ValueError("LoopRequest.capability_name is required for capability execution.")
        if request.capability_payload is None:
            raise ValueError("LoopRequest.capability_payload is required for capability execution.")
