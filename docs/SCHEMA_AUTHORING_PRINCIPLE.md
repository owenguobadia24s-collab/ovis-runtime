---
id: DOC-RUN-0003
title: Schema Authoring Principle
type: DOC
status: active
authority: operational
version: '0.1'
layer: runtime
domain: run
repo: ovis-runtime
path: docs/SCHEMA_AUTHORING_PRINCIPLE.md
owner: Owen Vitae
created: '2026-03-21'
last_updated: '2026-03-21'
registry: ovis-blueprint/REGISTRIES/entries/DOC-RUN-0003.yaml
module_id: MOD-WORK-OBJECT-REGISTRY-0001
module_slug: work_object_registry
system_id: SYS-KERNEL-0001
system_slug: ovis_kernel
related_module_ids:
- MOD-META-SCHEMA-POLICY-0001
---

# Purpose

Describe Schema Authoring Principle within the OVIS workspace.

# Scope

This file governs or documents Schema Authoring Principle within the ovis-runtime repository.

# Content

Typed Python models are primary; JSON Schema is generated/exported, not hand-maintained separately unless required.
In-repo schema edits happen in Python model code first.
Exported JSON Schema artifacts are generated outputs, not the primary authoring source.
Generated schemas may be committed only if treated as derived artifacts, never as the primary authoring source.

# References

- ovis-blueprint/REGISTRIES/entries/