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
last_updated: '2026-03-21'
registry: ovis-blueprint/REGISTRIES/entries/DOC-RUN-0001.yaml
---

# Purpose

Describe OVIS Runtime within the OVIS workspace.

# Scope

This file governs or documents OVIS Runtime within the ovis-runtime repository.

# Content

## OVIS Runtime

Scaffold-only Python package for the first OVIS Tool Gateway implementation boundary.

Current scope:
- package structure only
- registry module
- schema loader surface
- execution wrapper interface
- policy hook placeholders
- result-envelope structure
- shared types
- canonical state/schema package scaffold
- JSON Schema export surface
- transition validation surface
- test skeletons

Out of scope for this scaffold:
- runtime implementation
- compaction implementation
- bridge implementation
- persistence wiring
- real execution dispatch
- real policy evaluation

Architectural truth remains upstream in `ovis-blueprint`, especially ADR-001 through ADR-006 and the CJ-001 scaffold task.

Schema authoring principle:
- Typed Python models are primary; JSON Schema is generated/exported, not hand-maintained separately unless required.

# References

- ovis-blueprint/REGISTRIES/entries/
