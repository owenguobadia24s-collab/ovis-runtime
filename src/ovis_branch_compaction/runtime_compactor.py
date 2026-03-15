"""Deterministic local branch runtime compactor."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from ovis_branch import BranchEventReference, BranchState
from ovis_state_models import ObjectRef, ObjectType

from .triggers import CompactionTriggerClass
from .types import PreservedReferenceIndex


@dataclass(frozen=True)
class RuntimeCompactionResult:
    """Deterministic reduction output for one branch compaction."""

    source_range: str
    source_event_count: int
    preserved_reference_index: PreservedReferenceIndex
    summary: str
    artifact_payload: dict[str, Any]


class RuntimeBranchCompactor:
    """Deterministic local reducer for branch continuity state."""

    def compact(
        self,
        *,
        branch_state: BranchState,
        trigger: CompactionTriggerClass,
        compaction_id: str,
        created_at: datetime,
        artifact_path: str,
        correlation_id: str | None,
    ) -> RuntimeCompactionResult:
        event_count = len(branch_state.event_refs)
        source_range = f"events:0" if event_count == 0 else f"events:1-{event_count}"
        preserved_refs = self._build_preserved_references(branch_state)
        latest_event = branch_state.latest_event
        latest_event_id = latest_event.event_id if latest_event is not None else "none"
        created_at_text = created_at.isoformat()
        summary = (
            f"Branch {branch_state.branch.branch_id} compacted at {created_at_text}; "
            f"status={branch_state.branch.status}; "
            f"root_signal={branch_state.branch.root_signal_id}; "
            f"source_events={event_count}; "
            f"latest_event={latest_event_id}; "
            f"trigger={trigger}"
        )
        artifact_payload = {
            "compaction_id": compaction_id,
            "branch_id": str(branch_state.branch.branch_id),
            "created_at": created_at_text,
            "source_range": source_range,
            "source_event_count": event_count,
            "correlation_id": correlation_id,
            "branch_status": str(branch_state.branch.status),
            "root_signal_id": str(branch_state.branch.root_signal_id),
            "latest_compaction_id_previous": (
                str(branch_state.branch.latest_compaction_id)
                if branch_state.branch.latest_compaction_id is not None
                else None
            ),
            "latest_event": self._serialize_event_reference(latest_event),
            "event_refs": [self._serialize_event_reference(event) for event in branch_state.event_refs],
            "preserved_references": [
                {
                    "object_type": str(reference.object_type),
                    "object_id": reference.object_id,
                }
                for reference in preserved_refs.references
            ],
            "summary": summary,
            "artifact_path": artifact_path,
        }
        return RuntimeCompactionResult(
            source_range=source_range,
            source_event_count=event_count,
            preserved_reference_index=preserved_refs,
            summary=summary,
            artifact_payload=artifact_payload,
        )

    def _build_preserved_references(self, branch_state: BranchState) -> PreservedReferenceIndex:
        references = [
            ObjectRef(object_type=ObjectType.SIGNAL, object_id=branch_state.branch.root_signal_id)
        ]
        references.extend(
            ObjectRef(object_type=ObjectType.EVENT, object_id=event_ref.event_id)
            for event_ref in branch_state.event_refs
        )
        return PreservedReferenceIndex(references=tuple(references))

    def _serialize_event_reference(
        self,
        event_ref: BranchEventReference | None,
    ) -> dict[str, Any] | None:
        if event_ref is None:
            return None
        return {
            "event_id": event_ref.event_id,
            "event_type": event_ref.event_type,
            "created_at": event_ref.created_at.isoformat() if event_ref.created_at is not None else None,
            "correlation_id": event_ref.correlation_id,
        }
