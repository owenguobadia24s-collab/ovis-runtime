---
id: DOC-RUN-0002
title: Post CJ12 System State
type: DOC
status: active
authority: operational
version: '0.1'
layer: runtime
domain: run
repo: ovis-runtime
path: docs/POST_CJ12_SYSTEM_STATE.md
owner: Owen Vitae
created: '2026-03-21'
last_updated: '2026-03-21'
registry: ovis-blueprint/REGISTRIES/entries/DOC-RUN-0002.yaml
---

# Purpose

Describe Post CJ12 System State within the OVIS workspace.

# Scope

This file governs or documents Post CJ12 System State within the ovis-runtime repository.

# Content

## POST CJ12 System State

### 1. Purpose

This document records the authoritative system state of OVIS after completion of the first implementation cycle, covering CJ-001 through CJ-012.

OVIS now operates as a functioning governed cognitive execution system composed of these layers:

- event log
- runtime adapter
- capability gateway
- branch lifecycle
- branch compaction
- recursive loop
- operator interface

This document establishes the stable baseline for the next development phase. Its purpose is to freeze the architecture, operational boundaries, and system invariants that now exist in `ovis-runtime`.

### 2. System Overview

OVIS is organized as a layered governed execution system. A loop cycle begins with operator or upstream signal input, passes through approval and explicit execution selection, records its activity in the append-only event log, preserves continuity in branch state, and may optionally reduce continuity through compaction.

The current high-level architecture is:

```text
Signal
  ↓
Loop Runner
  ↓
Approval / Policy
  ↓
Execution Path
   ├─ Runtime Adapter
   └─ Capability Dispatcher
  ↓
Event Log
  ↓
Branch Lifecycle
  ↓
Optional Compaction
  ↓
Operator Inspection
```

The loop orchestrates subsystems but does not replace them. Runtime invocation, capability execution, branch continuity, compaction, and event persistence remain owned by their respective canonical layers. Operator access sits on top of those layers and is constrained to their public entrypoints.

### 3. Canonical Subsystems

#### Event Log (CJ-006)

Responsibilities:

- append-only JSONL event persistence
- deterministic serialization
- canonical event IDs
- event hashing
- daily file rotation

Location: `src/ovis_event_log/`

Key invariant: events are append-only and never mutated after persistence.

#### Runtime Adapter (CJ-007)

Responsibilities:

- canonical entrypoint for model invocation
- provider-specific logic isolated in the provider adapter
- runtime lifecycle event emission

Location: `src/ovis_responses_runtime/`

Key invariant: all model calls must pass through `RuntimeAdapter.invoke()`.

#### Capability Gateway (CJ-008)

Responsibilities:

- governed capability execution
- registry-based capability resolution
- policy hook enforcement
- execution lifecycle event emission

Location: `src/ovis_tool_gateway/`

Key invariant: capabilities execute only through `CapabilityDispatcher.execute()`.

#### Branch Lifecycle (CJ-009)

Responsibilities:

- canonical branch continuity container
- event reference tracking
- branch state persistence

Location: `src/ovis_branch/`

Key invariant: `branch_id` is the continuity anchor.

#### Branch Compaction (CJ-010)

Responsibilities:

- continuity reduction
- compaction artifact generation
- compaction record issuance

Location: `src/ovis_branch_compaction/`

Key invariant: compaction reduces continuity but does not replace branch identity.

#### Recursive Loop (CJ-011)

Responsibilities:

- orchestration of a single governed cognitive cycle
- integration of runtime, dispatcher, branch lifecycle, compaction, and event persistence

Location: `src/ovis_loop/`

Key invariant: the loop composes subsystems but does not reimplement them.

#### Operator Interface (CJ-012)

Responsibilities:

- CLI entrypoint for human interaction
- commands:
  - `signal create`
  - `branch inspect`
  - `event tail`
  - `compact`
  - `run`

Location: `src/ovis_operator/`

Key invariant: the CLI calls canonical subsystems rather than bypassing them.

### 4. Canonical Identity Model

OVIS identity remains OVIS-owned and prefix-governed. Canonical identifiers are distinct from ordering metadata, hashes, and any external provider references.

Implemented identity families include:

- `event_id`
- `branch_id`
- `correlation_id`
- `compaction_id`
- job-family IDs

The implemented canonical prefixes are:

- `evt_`
- `br_`
- `corr_`
- `cmp_`
- `job_plan_`
- `job_execute_`

The two job ID families are part of the broader job identity family, but they are issued as distinct canonical prefixes in the current implementation.

Identity is explicitly distinct from:

- sequence ordering
- content hashes
- provider identifiers

Sequence is used for event ordering within persisted event files. Hashes are used for deterministic event and payload integrity checks. Provider-managed identifiers remain external references and do not replace canonical OVIS identity.

Identity helpers are centralized in `src/ovis_ids/`.

### 5. Persisted Artifacts

OVIS now persists three operator-visible artifact classes.

Event logs are stored at:

- `events/YYYY-MM-DD.jsonl`

Branch state is stored at:

- `branches/<branch_id>.json`

Compaction artifacts are stored at:

- `compactions/branch_<branch_id>_compaction_<compaction_id>.json`

Branch persistence is direct canonical `BranchState` persistence. It does not use an operator-specific shadow schema. The persisted branch file contains the canonical `branch`, `correlation_id`, `event_refs`, and `latest_event` shape.

Together, these artifacts form the audit surface of the current system. They expose execution history, continuity state, and continuity reduction outputs without introducing a separate query or reconstruction layer.

### 6. Canonical Entry Points

The only legitimate entrypoints for system behavior are:

- runtime invocation: `RuntimeAdapter.invoke()`
- capability execution: `CapabilityDispatcher.execute()`
- branch management: `BranchLifecycleManager`
- compaction execution: `BranchCompactionExecutor`
- recursive cycle: `RecursiveLoopRunner.run()`
- operator access: `ovis` CLI

Subsystems must not bypass these entrypoints. New work should compose these surfaces rather than introducing alternate control paths.

### 7. System Invariants

The following rules are baseline system invariants and must not be violated:

- events are append-only
- canonical IDs are OVIS-owned
- `correlation_id` is propagated through a flow rather than regenerated mid-flow
- provider IDs remain external references only
- `branch_id` remains stable for the lifetime of a branch
- compaction preserves lineage and does not replace branch identity
- the loop composes subsystems rather than replacing them
- the CLI must call canonical layers rather than bypassing them

These invariants define both the architectural boundary and the audit boundary of the current implementation.

### 8. Known Constraints (v1)

The current system intentionally remains narrow:

- branch persistence is file-backed, not database-backed
- event tail is a simple file reader, not a query layer
- compaction is deterministic local reduction, not model summarization
- the approval gate is intentionally thin
- the operator CLI is intentionally minimal

These constraints keep the system understandable, inspectable, and auditable while the baseline architecture stabilizes.

### 9. Phase S1 Stabilization Targets

The next phase should prioritize stabilization and hardening rather than architectural expansion. Current targets are:

- persistence hardening
- artifact schema versioning
- operator diagnostics
- event replay utilities
- branch recovery tools
- governance and review refinement

The intent of Phase S1 is to strengthen the reliability and operational clarity of the existing system before expanding behavior.

### 10. Summary

OVIS now operates as a governed cognitive infrastructure with the following operational flow:

`state -> reasoning -> execution -> audit -> continuity -> recursion`

CJ-001 through CJ-012 collectively define the first operational version of the system. The architecture now exists as a composed set of canonical layers with stable entrypoints, persistent audit artifacts, governed execution paths, and an operator-facing shell that remains subordinate to those canonical subsystems.

# References

- ovis-blueprint/REGISTRIES/entries/
