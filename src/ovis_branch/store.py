"""In-memory store for branch lifecycle state."""

from __future__ import annotations

from copy import deepcopy
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
