---
id: DOC-RUN-0001
title: OVIS Runtime
type: DOC
status: active
authority: operational
version: '0.1'
layer: runtime
domain: run
repo: ovis-runtime
path: README.md
owner: Owen Vitae
created: '2026-03-21'
last_updated: '2026-06-30'
registry: ovis-blueprint/REGISTRIES/entries/DOC-RUN-0001.yaml
---

# Purpose

Describe OVIS Runtime within the OVIS workspace.

# Scope

This file governs or documents OVIS Runtime within the ovis-runtime repository.

# Content

## OVIS Runtime

Operational Python package for the implemented OVIS runtime baseline. This repo contains the runtime surfaces that execute, persist, inspect, and validate governed OVIS activity while remaining subordinate to blueprint doctrine and metadata authority.

Implemented:
- canonical state models and transition validation
- JSON Schema export from Python model definitions
- append-only event log writers with validation, hashing, and JSONL file persistence
- runtime adapter and OpenAI provider boundary
- branch lifecycle with in-memory and file-backed branch stores
- branch compaction executor with deterministic local reduction
- recursive loop runner for governed runtime or capability cycles
- operator CLI for signal creation, branch inspection, event tailing, compaction, loop runs, and metadata commands
- metadata scan, validation, reconciliation, normalization, and file initialization tooling
- local deterministic retrieval scaffold with document types, word-window chunking, lexical scoring, in-memory indexing, and cited result records

Partial:
- tool gateway registry, dispatcher, result envelopes, event emission, and registered in-process capability execution are implemented
- tool gateway schema loading remains a placeholder surface
- policy hooks are supported when supplied, but bundled production policy evaluation is not complete
- idempotency fields exist on execution requests and envelopes, but no durable idempotency store is implemented
- bridge preview is dry-run only; it can produce local `BridgeAction` previews and optional audit events, but it never performs external dispatch

Planned or out of scope for this repo baseline:
- Notion bridge
- OVIS/OVC bridge
- knowledge implementation
- chat ingestion, boundary classification, review queue, promotion workflow, and operating hub behavior
- production external side-effect dispatch
- validator exit-code repair
- policy or gateway expansion beyond the current surfaces

Architectural and metadata truth remains upstream in `ovis-blueprint`, especially the canonical ADRs, policies, and registry entries. Runtime implements operational surfaces under those boundaries; it does not redefine doctrine.

Schema authoring principle:
- Typed Python models are primary; JSON Schema is generated/exported, not hand-maintained separately unless required.

Validation:
- `python -m pytest -q --basetemp .pytest-tmp -p no:cacheprovider`
- `$env:PYTHONPATH='src'; python -m ovis_operator.cli metadata validate --repo-root C:\Users\Owner\OVIS\ovis-runtime --blueprint-root C:\Users\Owner\OVIS\ovis-blueprint --migration-phase M2 --json`
- `$env:PYTHONPATH='src'; python -m ovis_operator.cli metadata reconcile --repo-root C:\Users\Owner\OVIS\ovis-runtime --repo-root C:\Users\Owner\OVIS\ovis-blueprint --blueprint-root C:\Users\Owner\OVIS\ovis-blueprint --json`
- Run blueprint metadata validation as well when blueprint continuity logs or registry files are changed.

Known issue:
- Blueprint metadata validation may return native exit code `1` while the JSON report says `complete: true`. Treat the JSON completion field as the semantic result until the validator exit-code issue is repaired in a separate job.

# References

- ovis-blueprint/REGISTRIES/entries/
