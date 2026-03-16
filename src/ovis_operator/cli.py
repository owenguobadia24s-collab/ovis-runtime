"""Thin operator CLI over canonical OVIS subsystems."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback
from typing import Any, Mapping

from ovis_branch import BranchLifecycleManager, JsonFileBranchStore
from ovis_branch_compaction import BranchCompactionExecutor, CompactionHooks, CompactionTriggerClass
from ovis_event_log import FileEventWriter
from ovis_loop import LoopApprovalInput, LoopExecutionMode, LoopRequest, LoopSignalInput, RecursiveLoopRunner
from ovis_responses_runtime import (
    OpenAIResponsesProviderAdapter,
    RuntimeAdapterConfig,
    RuntimeModelConfig,
    RuntimeSessionConfig,
    SessionMode,
)
from ovis_state_models import PolicyProfile, RiskClass
from ovis_tool_gateway import DEFAULT_CAPABILITY_REGISTRY

from .formatting import render_error, render_json, render_pretty


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
        return args.func(args)
    except SystemExit:
        raise
    except Exception as exc:
        debug = False
        as_json = False
        if "args" in locals():
            debug = bool(getattr(args, "debug", False))
            as_json = bool(getattr(args, "json", False))
        if debug:
            traceback.print_exc()
        else:
            message = _exception_message(exc)
            sys.stderr.write(render_error(type(exc).__name__, message, as_json=as_json))
        return 1


def _build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=".", help="Operator data root. Defaults to the current directory.")
    common.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    common.add_argument("--debug", action="store_true", help="Print tracebacks on failure.")

    parser = argparse.ArgumentParser(prog="ovis")
    subparsers = parser.add_subparsers(dest="command", required=True)

    signal_parser = subparsers.add_parser("signal")
    signal_subparsers = signal_parser.add_subparsers(dest="signal_command", required=True)
    signal_create = signal_subparsers.add_parser("create", parents=[common])
    signal_create.add_argument("--text", required=True)
    signal_create.add_argument("--correlation-id")
    signal_create.add_argument("--execution-mode-hint", choices=[mode.value for mode in LoopExecutionMode])
    signal_create.set_defaults(func=_handle_signal_create)

    branch_parser = subparsers.add_parser("branch")
    branch_subparsers = branch_parser.add_subparsers(dest="branch_command", required=True)
    branch_inspect = branch_subparsers.add_parser("inspect", parents=[common])
    branch_inspect.add_argument("--branch-id", required=True)
    branch_inspect.set_defaults(func=_handle_branch_inspect)

    event_parser = subparsers.add_parser("event")
    event_subparsers = event_parser.add_subparsers(dest="event_command", required=True)
    event_tail = event_subparsers.add_parser("tail", parents=[common])
    event_tail.add_argument("--date")
    event_tail.add_argument("--count", type=int, default=20)
    event_tail.set_defaults(func=_handle_event_tail)

    compact = subparsers.add_parser("compact", parents=[common])
    compact.add_argument("--branch-id", required=True)
    compact.add_argument("--correlation-id")
    compact.set_defaults(func=_handle_compact)

    run = subparsers.add_parser("run", parents=[common])
    run.add_argument("--objective", required=True)
    run.add_argument("--mode", choices=[mode.value for mode in LoopExecutionMode])
    run.add_argument("--branch-id")
    run.add_argument("--correlation-id")
    signal_group = run.add_mutually_exclusive_group()
    signal_group.add_argument("--signal-json")
    signal_group.add_argument("--signal-text")
    run.add_argument("--compact-after-run", action="store_true")
    run.add_argument("--close-branch-after-run", action="store_true")
    approval_group = run.add_mutually_exclusive_group()
    approval_group.add_argument("--approve", action="store_true")
    approval_group.add_argument("--deny", action="store_true")
    run.add_argument("--model")
    run.add_argument("--runtime-input-json")
    run.add_argument("--capability-name")
    run.add_argument("--capability-payload-json")
    run.set_defaults(func=_handle_run)

    return parser


def _handle_signal_create(args: argparse.Namespace) -> int:
    correlation_id = _validate_optional_correlation_id(args.correlation_id)
    artifact = _build_signal_artifact(
        text=args.text,
        correlation_id=correlation_id,
        execution_mode_hint=args.execution_mode_hint,
        source_ref="operator://signal/create",
    )
    _write_output(artifact, as_json=args.json)
    return 0


def _handle_branch_inspect(args: argparse.Namespace) -> int:
    branch_lifecycle = _build_branch_lifecycle(_root_path(args.root))
    state = branch_lifecycle.get_branch(args.branch_id)
    if args.json:
        _write_output(state, as_json=True)
        return 0

    summary = {
        "branch_id": str(state.branch.branch_id),
        "status": str(state.branch.status),
        "created_at": state.branch.created_at,
        "updated_at": state.branch.updated_at,
        "correlation_id": state.correlation_id,
        "event_ref_count": len(state.event_refs),
        "latest_event": state.latest_event,
        "latest_compaction_id": state.branch.latest_compaction_id,
        "current_state_ref": state.branch.current_state_ref,
        "recent_event_refs": state.event_refs[-10:],
    }
    _write_output(summary, as_json=False)
    return 0


def _handle_event_tail(args: argparse.Namespace) -> int:
    if args.count <= 0:
        raise ValueError("--count must be greater than zero.")
    target_date = args.date or datetime.now().date().isoformat()
    event_path = _root_path(args.root) / "events" / f"{target_date}.jsonl"
    if not event_path.exists():
        _write_output([], as_json=args.json)
        return 0

    records = [
        json.loads(line)
        for line in event_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    recent_records = list(reversed(records[-args.count :]))
    if args.json:
        _write_output(recent_records, as_json=True)
        return 0

    summaries = [
        {
            "sequence": record["sequence"],
            "event_type": record["event_type"],
            "event_id": record["event_id"],
            "branch_id": record["branch_id"],
            "correlation_id": record["correlation_id"],
            "timestamp": record["timestamp"],
        }
        for record in recent_records
    ]
    _write_output(summaries, as_json=False)
    return 0


def _handle_compact(args: argparse.Namespace) -> int:
    correlation_id = _validate_optional_correlation_id(args.correlation_id)
    executor = _build_compaction_executor(_root_path(args.root))
    response = executor.compact_branch(
        branch_id=args.branch_id,
        correlation_id=correlation_id,
        trigger=CompactionTriggerClass.OPERATOR_REQUEST,
    )
    artifact_payload = _load_json_file(Path(response.output.compacted_state_ref))
    summary = {
        "compaction_id": str(response.record.compaction_id),
        "branch_id": str(response.record.branch_id),
        "artifact_path": response.output.compacted_state_ref,
        "source_event_count": artifact_payload["source_event_count"],
        "source_range": response.output.source_range,
    }
    _write_output(summary, as_json=args.json)
    return 0


def _handle_run(args: argparse.Namespace) -> int:
    signal_input, signal_metadata = _resolve_signal_input(args)
    mode = _resolve_execution_mode(args.mode, signal_metadata.get("execution_mode_hint"))
    correlation_id = _resolve_correlation_id(args.correlation_id, signal_metadata.get("correlation_id"))
    model_name = _resolve_model_name(explicit_model=args.model, execution_mode=mode)

    runner = _build_loop_runner(_root_path(args.root), model_name=model_name)
    request = LoopRequest(
        signal=signal_input,
        objective=args.objective,
        branch_id=args.branch_id,
        correlation_id=correlation_id,
        execution_mode=mode,
        runtime_input=_resolve_runtime_input(args, mode),
        capability_name=args.capability_name,
        capability_payload=_resolve_capability_payload(args, mode),
        approval=_build_approval_input(args),
        compact_after_run=bool(args.compact_after_run),
        close_branch_after_run=bool(args.close_branch_after_run),
    )
    result = runner.run(request)
    summary = {
        "branch_id": result.branch_id,
        "correlation_id": result.correlation_id,
        "execution_mode": str(result.execution_mode),
        "approval_decision": str(result.approval.decision),
        "success": result.success,
        "execution_succeeded": result.execution_succeeded,
        "runtime_output_text": result.runtime_response.output_text if result.runtime_response else None,
        "capability_result": result.capability_result.result_payload if result.capability_result else None,
        "compaction_id": (
            str(result.compaction_response.record.compaction_id)
            if result.compaction_response is not None
            else None
        ),
        "branch_status": str(result.branch_state.branch.status),
        "error_stage": str(result.error_stage) if result.error_stage is not None else None,
        "error_message": result.error_message,
    }
    _write_output(summary, as_json=args.json)
    return 0 if result.success else 1


def _build_branch_lifecycle(root: Path) -> BranchLifecycleManager:
    return BranchLifecycleManager(
        store=JsonFileBranchStore(root / "branches"),
        event_writer=FileEventWriter(root),
    )


def _build_compaction_executor(root: Path) -> BranchCompactionExecutor:
    branch_lifecycle = _build_branch_lifecycle(root)
    return BranchCompactionExecutor(
        branch_lifecycle=branch_lifecycle,
        artifact_root=root / "compactions",
        hooks=CompactionHooks(event_writer=FileEventWriter(root)),
    )


def _build_provider_adapter() -> OpenAIResponsesProviderAdapter:
    return OpenAIResponsesProviderAdapter()


def _build_runtime_config(model_name: str) -> RuntimeAdapterConfig:
    return RuntimeAdapterConfig(
        model=RuntimeModelConfig(model_name=model_name),
        session=RuntimeSessionConfig(
            session_mode=SessionMode.ZDR_FIRST,
            store_enabled=False,
            durable_state_allowed=False,
        ),
    )


def _build_loop_runner(root: Path, *, model_name: str) -> RecursiveLoopRunner:
    return RecursiveLoopRunner(
        event_writer=FileEventWriter(root),
        runtime_config=_build_runtime_config(model_name),
        capability_registry=DEFAULT_CAPABILITY_REGISTRY,
        runtime_provider_adapter=_build_provider_adapter(),
        branch_store=JsonFileBranchStore(root / "branches"),
        compaction_artifact_root=root / "compactions",
    )


def _resolve_signal_input(args: argparse.Namespace) -> tuple[LoopSignalInput, dict[str, Any]]:
    if args.signal_json:
        payload = _parse_json_object("--signal-json", args.signal_json)
        signal_input = LoopSignalInput(
            source_type=str(payload["source_type"]),
            source_ref=str(payload["source_ref"]),
            raw_input_ref=_optional_string(payload.get("raw_input_ref")),
            raw_input_hash=_optional_string(payload.get("raw_input_hash")),
            compressed_summary=str(payload["compressed_summary"]),
            extracted_signals=tuple(str(item) for item in payload.get("extracted_signals", ())),
            nuance=_optional_string(payload.get("nuance")),
            created_by=str(payload.get("created_by", "ovis_operator")),
        )
        return signal_input, {
            "correlation_id": payload.get("correlation_id"),
            "execution_mode_hint": payload.get("execution_mode_hint"),
        }

    signal_text = args.signal_text or args.objective
    signal_input = LoopSignalInput(
        source_type="operator",
        source_ref="operator://run",
        raw_input_ref=None,
        raw_input_hash=_sha256_text(signal_text),
        compressed_summary=signal_text,
        extracted_signals=(),
        nuance=None,
        created_by="ovis_operator",
    )
    return signal_input, {}


def _resolve_execution_mode(explicit_mode: str | None, hinted_mode: object) -> LoopExecutionMode:
    resolved = explicit_mode or _optional_string(hinted_mode) or LoopExecutionMode.RUNTIME.value
    return LoopExecutionMode(resolved)


def _resolve_correlation_id(explicit_correlation_id: str | None, hinted_correlation_id: object) -> str | None:
    return _validate_optional_correlation_id(explicit_correlation_id or _optional_string(hinted_correlation_id))


def _resolve_model_name(*, explicit_model: str | None, execution_mode: LoopExecutionMode) -> str:
    if explicit_model:
        return explicit_model
    env_model = os.getenv("OVIS_MODEL")
    if env_model:
        return env_model
    if execution_mode == LoopExecutionMode.RUNTIME:
        raise ValueError("Runtime mode requires --model or OVIS_MODEL.")
    return "__unused_capability_mode__"


def _resolve_runtime_input(args: argparse.Namespace, mode: LoopExecutionMode) -> Mapping[str, Any] | None:
    if mode != LoopExecutionMode.RUNTIME:
        return None
    if args.runtime_input_json:
        return _parse_json_object("--runtime-input-json", args.runtime_input_json)
    return {"prompt": args.objective}


def _resolve_capability_payload(args: argparse.Namespace, mode: LoopExecutionMode) -> Mapping[str, Any] | None:
    if mode != LoopExecutionMode.CAPABILITY:
        return None
    raw_payload = args.capability_payload_json or "{}"
    return _parse_json_object("--capability-payload-json", raw_payload)


def _build_approval_input(args: argparse.Namespace) -> LoopApprovalInput:
    approved = not bool(args.deny)
    rationale = "operator-approved" if approved else "operator-denied"
    return LoopApprovalInput(
        approved=approved,
        reviewer_id="operator",
        rationale=rationale,
        risk_class=RiskClass.R1,
        policy_profile=PolicyProfile.HUMAN_APPROVED,
        approval_scope="operator-cli",
    )


def _build_signal_artifact(
    *,
    text: str,
    correlation_id: str | None,
    execution_mode_hint: str | None,
    source_ref: str,
) -> dict[str, object]:
    artifact: dict[str, object] = {
        "source_type": "operator",
        "source_ref": source_ref,
        "raw_input_ref": None,
        "raw_input_hash": _sha256_text(text),
        "compressed_summary": text,
        "extracted_signals": [],
        "nuance": None,
        "created_by": "ovis_operator",
    }
    if correlation_id is not None:
        artifact["correlation_id"] = correlation_id
    if execution_mode_hint is not None:
        artifact["execution_mode_hint"] = execution_mode_hint
    return artifact


def _parse_json_object(argument_name: str, raw_json: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{argument_name} must be valid JSON.") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{argument_name} must decode to a JSON object.")
    return payload


def _load_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_optional_correlation_id(correlation_id: str | None) -> str | None:
    if correlation_id is None:
        return None
    if not correlation_id.startswith("corr_"):
        raise ValueError("correlation_id must use the canonical corr_ prefix.")
    return correlation_id


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _root_path(raw_root: str) -> Path:
    return Path(raw_root).resolve()


def _exception_message(exc: Exception) -> str:
    if isinstance(exc, KeyError) and exc.args:
        return str(exc.args[0])
    return str(exc)


def _write_output(payload: Any, *, as_json: bool) -> None:
    rendered = render_json(payload) if as_json else render_pretty(payload)
    sys.stdout.write(rendered)


if __name__ == "__main__":
    raise SystemExit(main())
