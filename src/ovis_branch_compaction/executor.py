"""First working branch compaction executor."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from ovis_branch import BranchLifecycleManager
from ovis_event_log import emit_event
from ovis_state_models import CompactionRecord, generate_compaction_id

from .commands import BranchCompactionCommandRunner, CompactionCommand
from .hooks import CompactionHookContext, CompactionHooks, build_compaction_created_event
from .runtime_compactor import RuntimeBranchCompactor
from .triggers import CompactionTriggerClass
from .types import CompactedStateOutput, CompactionResponse
from .validation import validate_compaction_response


class BranchCompactionExecutor(BranchCompactionCommandRunner):
    """Canonical executor for governed branch compaction."""

    def __init__(
        self,
        *,
        branch_lifecycle: BranchLifecycleManager,
        artifact_root: Path | str = "compactions",
        hooks: CompactionHooks | None = None,
        compactor: RuntimeBranchCompactor | None = None,
    ) -> None:
        self._branch_lifecycle = branch_lifecycle
        self._artifact_root = Path(artifact_root)
        self._hooks = hooks or CompactionHooks()
        self._compactor = compactor or RuntimeBranchCompactor()

    def compact_branch(
        self,
        branch_id: str,
        trigger: CompactionTriggerClass,
        correlation_id: str | None = None,
        parent_event_id: str | None = None,
    ) -> CompactionResponse:
        self._validate_branch_id(branch_id)
        effective_correlation = correlation_id
        if effective_correlation is not None:
            self._validate_correlation_id(effective_correlation)
        if parent_event_id is not None:
            self._validate_parent_event_id(parent_event_id)

        branch_state = self._branch_lifecycle.get_branch(branch_id)
        if branch_state.correlation_id is not None:
            if effective_correlation is not None and effective_correlation != branch_state.correlation_id:
                raise ValueError("Compaction correlation_id must match the authoritative branch correlation_id.")
            effective_correlation = branch_state.correlation_id

        compaction_id = str(generate_compaction_id())
        self._validate_compaction_id(compaction_id)

        artifact_path = self._build_artifact_path(branch_id, compaction_id)
        created_at = datetime.now(UTC)
        reduction = self._compactor.compact(
            branch_state=branch_state,
            trigger=trigger,
            compaction_id=compaction_id,
            created_at=created_at,
            artifact_path=artifact_path.as_posix(),
            correlation_id=effective_correlation,
        )
        self._write_artifact(artifact_path, reduction.artifact_payload)

        updated_state = self._branch_lifecycle.record_compaction(
            branch_id=branch_id,
            compaction_id=compaction_id,
            compacted_state_ref=artifact_path.as_posix(),
        )
        record = CompactionRecord(
            compaction_id=compaction_id,
            branch_id=updated_state.branch.branch_id,
            source_range=reduction.source_range,
            compacted_state_ref=artifact_path.as_posix(),
            preserved_reference_index=reduction.preserved_reference_index.references,
            created_at=created_at,
        )
        output = CompactedStateOutput(
            compacted_state_ref=artifact_path.as_posix(),
            preserved_reference_index=reduction.preserved_reference_index,
            source_range=reduction.source_range,
        )
        response = CompactionResponse(
            branch=updated_state.branch,
            record=record,
            output=output,
        )
        validate_compaction_response(response)

        if effective_correlation is not None and self._hooks.event_writer is not None:
            event = build_compaction_created_event(
                record=record,
                branch=updated_state.branch,
                context=CompactionHookContext(
                    correlation_id=effective_correlation,
                    actor_type="system",
                    actor_id="ovis_branch_compaction.executor",
                    created_at=created_at,
                    parent_event_id=parent_event_id,
                ),
                payload_inline={
                    "compaction_id": compaction_id,
                    "branch_id": branch_id,
                    "source_event_count": reduction.source_event_count,
                    "artifact_path": artifact_path.as_posix(),
                },
            )
            emit_event(event, self._hooks.event_writer)

        return response

    def compact(self, command: CompactionCommand) -> CompactionResponse:
        request = command.request
        return self.compact_branch(
            branch_id=str(request.branch.branch_id),
            trigger=request.trigger,
            correlation_id=request.correlation_id,
            parent_event_id=request.parent_event_id,
        )

    def _build_artifact_path(self, branch_id: str, compaction_id: str) -> Path:
        return self._artifact_root / f"branch_{branch_id}_compaction_{compaction_id}.json"

    def _write_artifact(self, artifact_path: Path, artifact_payload: dict[str, object]) -> None:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(
            json.dumps(artifact_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _validate_branch_id(self, branch_id: str) -> None:
        if not branch_id.startswith("br_"):
            raise ValueError("branch_id must use the canonical br_ prefix.")

    def _validate_compaction_id(self, compaction_id: str) -> None:
        if not compaction_id.startswith("cmp_"):
            raise ValueError("compaction_id must use the canonical cmp_ prefix.")

    def _validate_correlation_id(self, correlation_id: str) -> None:
        if not correlation_id.startswith("corr_"):
            raise ValueError("correlation_id must use the canonical corr_ prefix.")

    def _validate_parent_event_id(self, parent_event_id: str) -> None:
        if not parent_event_id.startswith("evt_"):
            raise ValueError("parent_event_id must use the canonical evt_ prefix.")
