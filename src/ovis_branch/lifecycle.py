"""Canonical branch lifecycle manager."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

from ovis_event_log import AppendOnlyEventWriter, build_root_event, emit_event
from ovis_state_models import ActorType, Branch, Event, EventType, ObjectType, Signal, generate_branch_id, generate_event_id

from .store import BranchStore, InMemoryBranchStore
from .types import BranchEventReference, BranchState, BranchStatus, CreateBranchInput

_BRANCH_ACTOR_ID = "ovis_branch.lifecycle"


class BranchLifecycleManager:
    """Thin governed lifecycle for canonical branch state."""

    def __init__(
        self,
        *,
        store: BranchStore | None = None,
        event_writer: AppendOnlyEventWriter | None = None,
    ) -> None:
        self._store = store or InMemoryBranchStore()
        self._event_writer = event_writer

    def create_branch(self, source: Signal | CreateBranchInput) -> BranchState:
        root_signal_id, correlation_id, current_state_ref = self._normalize_create_source(source)
        if correlation_id is not None:
            self._validate_correlation_id(correlation_id)

        branch_id = str(generate_branch_id())
        timestamp = datetime.now(UTC)
        branch = Branch(
            branch_id=branch_id,
            root_signal_id=root_signal_id,
            current_state_ref=current_state_ref or f"memory://branches/{branch_id}",
            latest_compaction_id=None,
            status=BranchStatus.OPEN,
            created_at=timestamp,
            updated_at=timestamp,
        )
        state = BranchState(
            branch=branch,
            correlation_id=correlation_id,
            event_refs=(),
            latest_event=None,
        )
        created_state = self._store.create(state)
        self._emit_lifecycle_event(
            state=created_state,
            event_type=EventType.BRANCH_CREATED,
            payload_inline={"root_signal_id": root_signal_id},
        )
        return created_state

    def append_event(self, branch_id: str, event: Event | BranchEventReference) -> BranchState:
        self._validate_branch_id(branch_id)
        state = self._store.get(branch_id)
        self._require_open_branch(state)

        event_ref = self._normalize_event_reference(event, state)
        correlation_id = state.correlation_id or event_ref.correlation_id
        if correlation_id is not None:
            self._validate_correlation_id(correlation_id)

        timestamp = datetime.now(UTC)
        updated_branch = state.branch.model_copy(update={"updated_at": timestamp})
        updated_event_refs = state.event_refs + (event_ref,)
        updated_state = BranchState(
            branch=updated_branch,
            correlation_id=correlation_id,
            event_refs=updated_event_refs,
            latest_event=event_ref,
        )
        stored_state = self._store.replace(updated_state)
        self._emit_lifecycle_event(
            state=stored_state,
            event_type=EventType.BRANCH_EVENT_APPENDED,
            payload_inline={
                "event_id": event_ref.event_id,
                "event_type": event_ref.event_type,
            },
        )
        return stored_state

    def get_branch(self, branch_id: str) -> BranchState:
        self._validate_branch_id(branch_id)
        return self._store.get(branch_id)

    def close_branch(self, branch_id: str) -> BranchState:
        self._validate_branch_id(branch_id)
        state = self._store.get(branch_id)
        self._require_open_branch(state)

        timestamp = datetime.now(UTC)
        updated_branch = state.branch.model_copy(
            update={"status": BranchStatus.CLOSED, "updated_at": timestamp}
        )
        updated_state = BranchState(
            branch=updated_branch,
            correlation_id=state.correlation_id,
            event_refs=state.event_refs,
            latest_event=state.latest_event,
        )
        stored_state = self._store.replace(updated_state)
        self._emit_lifecycle_event(
            state=stored_state,
            event_type=EventType.BRANCH_CLOSED,
            payload_inline={"status": str(BranchStatus.CLOSED)},
        )
        return stored_state

    def _normalize_create_source(
        self,
        source: Signal | CreateBranchInput,
    ) -> tuple[str, str | None, str | None]:
        if isinstance(source, Signal):
            return str(source.signal_id), None, None
        return source.root_signal_id, source.correlation_id, source.current_state_ref

    def _normalize_event_reference(
        self,
        event: Event | BranchEventReference,
        state: BranchState,
    ) -> BranchEventReference:
        if isinstance(event, Event):
            self._validate_event_id(str(event.event_id))
            self._validate_branch_id(str(event.branch_id))
            if str(event.branch_id) != str(state.branch.branch_id):
                raise ValueError("Appended Event must preserve the branch_id.")
            event_correlation_id = str(event.correlation_id)
            self._validate_correlation_id(event_correlation_id)
            if state.correlation_id is not None and event_correlation_id != state.correlation_id:
                raise ValueError("Appended Event correlation_id must match the branch correlation_id.")
            return BranchEventReference(
                event_id=str(event.event_id),
                event_type=str(event.event_type),
                created_at=event.created_at,
                correlation_id=event_correlation_id,
            )

        self._validate_event_id(event.event_id)
        if event.correlation_id is not None:
            self._validate_correlation_id(event.correlation_id)
        if state.correlation_id is not None and event.correlation_id is not None and event.correlation_id != state.correlation_id:
            raise ValueError("Appended event correlation_id must match the branch correlation_id.")
        return event

    def _emit_lifecycle_event(
        self,
        *,
        state: BranchState,
        event_type: EventType,
        payload_inline: dict[str, object],
    ) -> None:
        if self._event_writer is None:
            return
        if state.correlation_id is None:
            return

        event = build_root_event(
            event_id=generate_event_id(),
            event_type=event_type,
            correlation_id=state.correlation_id,
            object_type=ObjectType.BRANCH,
            object_id=str(state.branch.branch_id),
            branch_id=state.branch.branch_id,
            actor_type=ActorType.SYSTEM,
            actor_id=_BRANCH_ACTOR_ID,
            created_at=datetime.now(UTC),
            payload_inline=payload_inline,
        )
        emit_event(event, self._event_writer)

    def _require_open_branch(self, state: BranchState) -> None:
        if state.branch.status == BranchStatus.CLOSED:
            raise ValueError("Closed branches cannot accept this lifecycle operation.")
        if state.branch.status != BranchStatus.OPEN:
            raise ValueError(f"Unsupported branch status: {state.branch.status}")

    def _validate_branch_id(self, branch_id: str) -> None:
        if not branch_id.startswith("br_"):
            raise ValueError("branch_id must use the canonical br_ prefix.")

    def _validate_correlation_id(self, correlation_id: str) -> None:
        if not correlation_id.startswith("corr_"):
            raise ValueError("correlation_id must use the canonical corr_ prefix.")

    def _validate_event_id(self, event_id: str) -> None:
        if not event_id.startswith("evt_"):
            raise ValueError("event_id must use the canonical evt_ prefix.")
