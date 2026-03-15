# OVIS Runtime

Scaffold-only Python package for the first OVIS Tool Gateway implementation boundary.

Current scope:
- package structure only
- registry module
- schema loader surface
- execution wrapper interface
- policy hook placeholders
- result-envelope structure
- shared types
- test skeletons

Out of scope for this scaffold:
- runtime implementation
- compaction implementation
- bridge implementation
- persistence wiring
- real execution dispatch
- real policy evaluation

Architectural truth remains upstream in `ovis-blueprint`, especially ADR-001 through ADR-006 and the CJ-001 scaffold task.
