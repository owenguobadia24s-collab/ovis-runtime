from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_event_log import MemoryEventWriter  # noqa: E402
from ovis_tool_gateway import CapabilityDefinition, CapabilityDispatcher, CapabilityRegistry, ExecutionRequest  # noqa: E402


def _make_request(capability_name: str, payload: dict[str, object]) -> ExecutionRequest:
    return ExecutionRequest(
        capability_name=capability_name,
        input_payload=payload,
        correlation_id="corr_001",
        idempotency_key="idem_001",
        object_context={"work_object_id": "wo_001"},
        branch_context={"branch_id": "br_001"},
    )


def _register(registry: CapabilityRegistry, name: str, handler) -> None:
    registry.register(
        CapabilityDefinition(
            name=name,
            version="v1",
            schema_ref=f"schemas/{name}.json",
            side_effect_class="read-only",
        ),
        handler=handler,
    )


def test_dispatcher_executes_registered_capability_and_emits_success_events() -> None:
    registry = CapabilityRegistry()
    writer = MemoryEventWriter()
    _register(registry, "math.add", lambda payload: payload["a"] + payload["b"])
    dispatcher = CapabilityDispatcher(registry=registry, event_writer=writer)

    result = dispatcher.execute(_make_request("math.add", {"a": 2, "b": 3}))

    records = writer.records()
    assert result.execution_status == "success"
    assert result.policy_disposition == "defer"
    assert result.result_payload == 5
    assert result.payload_hash is not None
    assert result.branch_ref == "br_001"
    assert result.object_refs["work_object_id"] == "wo_001"
    assert len(records) == 2
    assert records[0]["event_type"] == "capability.requested"
    assert records[1]["event_type"] == "capability.completed"
    assert records[0]["correlation_id"] == "corr_001"
    assert records[0]["branch_id"] == "br_001"
    assert records[0]["payload"]["payload_inline"]["capability_name"] == "math.add"
    assert records[1]["payload"]["payload_inline"]["success"] is True


def test_dispatcher_returns_error_for_unknown_capability_and_emits_error_event() -> None:
    writer = MemoryEventWriter()
    dispatcher = CapabilityDispatcher(registry=CapabilityRegistry(), event_writer=writer)

    result = dispatcher.execute(_make_request("missing.capability", {"value": "hello"}))

    records = writer.records()
    assert result.execution_status == "error"
    assert result.policy_disposition == "defer"
    assert "Unknown capability" in result.error_details
    assert len(records) == 1
    assert records[0]["event_type"] == "capability.error"
    assert records[0]["payload"]["payload_inline"]["error_type"] == "ResolutionError"


def test_dispatcher_surfaces_capability_exceptions_and_emits_error_event() -> None:
    registry = CapabilityRegistry()
    writer = MemoryEventWriter()

    def failing_handler(payload: dict[str, object]) -> object:
        raise RuntimeError("boom")

    _register(registry, "echo.return", failing_handler)
    dispatcher = CapabilityDispatcher(registry=registry, event_writer=writer)

    result = dispatcher.execute(_make_request("echo.return", {"value": "hello"}))

    records = writer.records()
    assert result.execution_status == "error"
    assert result.policy_disposition == "defer"
    assert result.error_details == "boom"
    assert len(records) == 2
    assert records[0]["event_type"] == "capability.requested"
    assert records[1]["event_type"] == "capability.error"
    assert records[1]["payload"]["payload_inline"]["error_type"] == "RuntimeError"


def test_dispatcher_leaves_payload_hash_empty_for_non_serializable_results() -> None:
    registry = CapabilityRegistry()
    _register(registry, "echo.return", lambda payload: {"values": {1, 2, 3}})
    dispatcher = CapabilityDispatcher(registry=registry)

    result = dispatcher.execute(_make_request("echo.return", {"value": "hello"}))

    assert result.execution_status == "success"
    assert result.result_payload == {"values": {1, 2, 3}}
    assert result.payload_hash is None
