# OVIS Runtime

OVIS Runtime is the execution layer of the OVIS system.

It is responsible for:
- loading approved executable work
- validating runtime readiness
- scheduling and executing jobs
- emitting canonical runtime events
- recording run state and outcomes
- dispatching downstream bridge updates

It is not the source of architectural truth.
Architecture, policy, and canonical contracts are defined upstream in `ovis-blueprint`.