"""Deterministic local operating hub dashboard rendering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .models import HubNextAction, HubStatus, ProjectStatus, ReviewSummary


DAILY_DASHBOARD_RENDERER_VERSION = "daily-dashboard-renderer-v0"
DAILY_OPERATING_RHYTHM = (
    "Check active bundle and CJ before starting work.",
    "Review blockers and missing evidence before promotion.",
    "List pending review candidates and route one explicit operator decision at a time.",
    "Promote only already-approved candidates to local output references.",
    "Run validation and stop for operator review before advancing.",
)


def load_hub_status_json(path: str | Path) -> HubStatus:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("hub status JSON must decode to an object")
    return hub_status_from_dict(payload)


def hub_status_from_dict(data: Mapping[str, Any]) -> HubStatus:
    summary_data = dict(data["review_summary"])
    review_summary = ReviewSummary(
        **{
            **summary_data,
            "source_queue_refs": tuple(summary_data.get("source_queue_refs", ())),
        }
    )
    project_statuses = tuple(_project_status_from_dict(item) for item in data.get("project_statuses", ()))
    return HubStatus(
        hub_version=str(data["hub_version"]),
        generated_from=tuple(data.get("generated_from", ())),
        project_statuses=project_statuses,
        review_summary=review_summary,
        active_bundle=_optional_string(data.get("active_bundle")),
        active_cj=_optional_string(data.get("active_cj")),
        validation_posture=str(data["validation_posture"]),
        external_side_effects=str(data["external_side_effects"]),
        next_action=str(data["next_action"]),
        source_refs=tuple(data.get("source_refs", ())),
        created_at=_optional_string(data.get("created_at")),
    )


def build_next_action(status: HubStatus) -> HubNextAction:
    return HubNextAction(
        action=status.next_action,
        reason=_next_action_reason(status),
        source_refs=_next_action_source_refs(status),
    )


def render_dashboard_markdown(status: HubStatus) -> str:
    next_action = build_next_action(status)
    lines = [
        "# OVIS First Surface Daily Session Dashboard",
        "",
        f"- Renderer: `{DAILY_DASHBOARD_RENDERER_VERSION}`",
        f"- Hub version: `{status.hub_version}`",
        f"- Active bundle: {status.active_bundle or 'None'}",
        f"- Active CJ: {status.active_cj or 'None'}",
        f"- Validation posture: {status.validation_posture}",
        f"- External side effects: {status.external_side_effects}",
        "",
        "## Next Action",
        "",
        f"- Action: {next_action.action}",
        f"- Reason: {next_action.reason}",
        f"- Source refs: {_format_refs(next_action.source_refs)}",
        "",
        "## Review Summary",
        "",
        f"- Total candidates: {status.review_summary.total_candidates}",
        f"- Pending review: {status.review_summary.pending_count}",
        f"- Approved: {status.review_summary.approved_count}",
        f"- Archived: {status.review_summary.archived_count}",
        f"- Discarded: {status.review_summary.discarded_count}",
        f"- Review later: {status.review_summary.review_later_count}",
        f"- Blocked: {status.review_summary.blocked_count}",
        f"- Promoted local: {status.review_summary.promoted_local_count}",
        f"- Queue refs: {_format_refs(status.review_summary.source_queue_refs)}",
        "",
        "## Project Status By Boundary",
        "",
        "| Boundary | Classified | Pending | Approved | Blocked | Promoted Local | Open CJs | Next Hint |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for project in status.project_statuses:
        lines.append(
            " | ".join(
                (
                    f"| {project.boundary}",
                    str(project.classified_count),
                    str(project.pending_review_count),
                    str(project.approved_count),
                    str(project.blocked_count),
                    str(project.promoted_local_count),
                    str(project.open_cj_count),
                    f"{project.next_action_hint} |",
                )
            )
        )

    blockers = tuple(project for project in status.project_statuses if project.blocked_count)
    pending = tuple(project for project in status.project_statuses if project.pending_review_count)
    lines.extend(
        [
            "",
            "## Blockers And Pending Reviews",
            "",
            f"- Blocked boundaries: {_format_boundary_counts(blockers, 'blocked_count')}",
            f"- Pending boundaries: {_format_boundary_counts(pending, 'pending_review_count')}",
            "",
            "## Daily Operating Rhythm",
            "",
        ]
    )
    lines.extend(f"{index}. {step}" for index, step in enumerate(DAILY_OPERATING_RHYTHM, start=1))
    lines.extend(
        [
            "",
            "## Source Refs",
            "",
        ]
    )
    lines.extend(f"- `{ref}`" for ref in status.source_refs)
    return "\n".join(lines).rstrip() + "\n"


def render_next_action_text(status: HubStatus) -> str:
    next_action = build_next_action(status)
    return "\n".join(
        (
            f"action: {next_action.action}",
            f"reason: {next_action.reason}",
            f"source_refs: {_format_refs(next_action.source_refs)}",
            "",
        )
    )


def write_dashboard_markdown(status: HubStatus, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_dashboard_markdown(status), encoding="utf-8")
    return path


def _next_action_reason(status: HubStatus) -> str:
    for project in status.project_statuses:
        if project.blocked_count and status.next_action.startswith(project.boundary):
            return "Blocked evidence takes priority before local promotion or CJ advancement."
    for project in status.project_statuses:
        if project.pending_review_count and status.next_action.startswith(project.boundary):
            return "Pending review candidates are the next local operator decision surface."
    for project in status.project_statuses:
        if project.approved_count > project.promoted_local_count and status.next_action.startswith(project.boundary):
            return "Approved candidates remain available for local promotion output."
    for project in status.project_statuses:
        if project.open_cj_count and status.next_action.startswith(project.boundary):
            return "Open CJ work remains after review and promotion queues are clear."
    return "No local blocker, review, promotion, or open CJ action was found."


def _next_action_source_refs(status: HubStatus) -> tuple[str, ...]:
    action_boundary = status.next_action.split(":", 1)[0]
    for project in status.project_statuses:
        if project.boundary == action_boundary:
            return project.source_refs
    return status.source_refs


def _format_refs(refs: tuple[str, ...]) -> str:
    if not refs:
        return "None"
    return ", ".join(f"`{ref}`" for ref in refs)


def _format_boundary_counts(projects: tuple[ProjectStatus, ...], count_attr: str) -> str:
    if not projects:
        return "None"
    return ", ".join(f"{project.boundary}={getattr(project, count_attr)}" for project in projects)


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _project_status_from_dict(data: Mapping[str, Any]) -> ProjectStatus:
    return ProjectStatus(
        **{
            **dict(data),
            "source_refs": tuple(data.get("source_refs", ())),
        }
    )
