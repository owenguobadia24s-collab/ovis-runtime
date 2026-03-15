"""Hook surfaces for canonical compaction event emission."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ovis_event_log import AppendOnlyEventWriter, build_child_event, build_root_event
from ovis_state_models import ActorType, Branch, CompactionRecord, Event


@dataclass(frozen=True)
class CompactionHookContext:
    """Context required to build a canonical compaction event."""

    correlation_id: str
    actor_type: ActorType | str
    actor_id: str
    created_at: datetime
    parent_event_id: str | None = None


@dataclass(frozen=True)
class CompactionHooks:
    """Optional hooks for compaction scaffolds."""

    event_writer: AppendOnlyEventWriter | None = None


def build_compaction_created_event(
    record: CompactionRecord,
    branch: Branch,
    context: CompactionHookContext,
) -> Event:
    """Build the canonical compaction.created event without emitting it."""

    payload_ref = record.compacted_state_ref
    if context.parent_event_id:
        parent_event = build_root_event(
            event_id=context.parent_event_id,
            event_type="compaction.created",
            correlation_id=context.correlation_id,
            object_type="branch",
            object_id=branch.branch_id,
            branch_id=branch.branch_id,
            actor_type=context.actor_type,
            actor_id=context.actor_id,
            created_at=context.created_at,
            payload_ref=payload_ref,
        )
        return build_child_event(
            parent_event=parent_event,
            event_id=f"{record.compaction_id}-event",
            event_type="compaction.created",
            object_type="compaction_record",
            object_id=record.compaction_id,
            actor_type=context.actor_type,
            actor_id=context.actor_id,
            created_at=context.created_at,
            payload_ref=payload_ref,
        )

    return build_root_event(
        event_id=f"{record.compaction_id}-event",
        event_type="compaction.created",
        correlation_id=context.correlation_id,
        object_type="compaction_record",
        object_id=record.compaction_id,
        branch_id=branch.branch_id,
        actor_type=context.actor_type,
        actor_id=context.actor_id,
        created_at=context.created_at,
        payload_ref=payload_ref,
    )
