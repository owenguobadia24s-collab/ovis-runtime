"""In-memory store for branch lifecycle state."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
from typing import Protocol

from .types import BranchState


class BranchStore(Protocol):
    """Storage interface for canonical branch lifecycle state."""

    def create(self, state: BranchState) -> BranchState:
        """Persist one new branch state."""

    def get(self, branch_id: str) -> BranchState:
        """Return the current branch state."""

    def replace(self, state: BranchState) -> BranchState:
        """Replace the stored branch state."""


class InMemoryBranchStore:
    """In-memory-only branch state store for CJ-009."""

    def __init__(self) -> None:
        self._states: dict[str, BranchState] = {}

    def create(self, state: BranchState) -> BranchState:
        branch_id = str(state.branch.branch_id)
        if branch_id in self._states:
            raise ValueError(f"Branch already exists: {branch_id}")
        self._states[branch_id] = deepcopy(state)
        return deepcopy(state)

    def get(self, branch_id: str) -> BranchState:
        if branch_id not in self._states:
            raise KeyError(branch_id)
        return deepcopy(self._states[branch_id])

    def replace(self, state: BranchState) -> BranchState:
        branch_id = str(state.branch.branch_id)
        if branch_id not in self._states:
            raise KeyError(branch_id)
        self._states[branch_id] = deepcopy(state)
        return deepcopy(state)


class JsonFileBranchStore:
    """File-backed branch store that persists the canonical BranchState shape directly."""

    def __init__(self, root_dir: str | Path) -> None:
        self._root_dir = Path(root_dir)

    def create(self, state: BranchState) -> BranchState:
        branch_id = str(state.branch.branch_id)
        path = self._path_for(branch_id)
        if path.exists():
            raise ValueError(f"Branch already exists: {branch_id}")
        self._write_state(path, state)
        return self.get(branch_id)

    def get(self, branch_id: str) -> BranchState:
        path = self._path_for(branch_id)
        if not path.exists():
            raise KeyError(branch_id)
        payload = json.loads(path.read_text(encoding="utf-8"))
        return self._deserialize_state(payload)

    def replace(self, state: BranchState) -> BranchState:
        branch_id = str(state.branch.branch_id)
        path = self._path_for(branch_id)
        if not path.exists():
            raise KeyError(branch_id)
        self._write_state(path, state)
        return self.get(branch_id)

    def _path_for(self, branch_id: str) -> Path:
        return self._root_dir / f"{branch_id}.json"

    def _write_state(self, path: Path, state: BranchState) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._serialize_state(state)
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _serialize_state(self, state: BranchState) -> dict[str, object]:
        return {
            "branch": state.branch.model_dump(mode="json"),
            "correlation_id": state.correlation_id,
            "event_refs": [self._serialize_event_ref(event_ref) for event_ref in state.event_refs],
            "latest_event": self._serialize_event_ref(state.latest_event),
        }

    def _serialize_event_ref(self, event_ref) -> dict[str, object] | None:
        if event_ref is None:
            return None
        payload = asdict(event_ref)
        created_at = payload.get("created_at")
        if isinstance(created_at, datetime):
            payload["created_at"] = created_at.isoformat()
        return payload

    def _deserialize_state(self, payload: dict[str, object]) -> BranchState:
        from .types import BranchEventReference

        branch_payload = payload["branch"]
        assert isinstance(branch_payload, dict)
        event_refs_payload = payload.get("event_refs", [])
        assert isinstance(event_refs_payload, list)
        latest_event_payload = payload.get("latest_event")
        return BranchState(
            branch=self._deserialize_branch(branch_payload),
            correlation_id=payload.get("correlation_id"),
            event_refs=tuple(self._deserialize_event_ref(event_ref) for event_ref in event_refs_payload),
            latest_event=self._deserialize_event_ref(latest_event_payload),
        )

    def _deserialize_branch(self, payload: dict[str, object]):
        from ovis_state_models import Branch

        return Branch.model_validate(payload)

    def _deserialize_event_ref(self, payload):
        from .types import BranchEventReference

        if payload is None:
            return None
        assert isinstance(payload, dict)
        created_at = payload.get("created_at")
        return BranchEventReference(
            event_id=str(payload["event_id"]),
            event_type=payload.get("event_type"),
            created_at=datetime.fromisoformat(str(created_at)) if created_at is not None else None,
            correlation_id=payload.get("correlation_id"),
        )
