"""Finding status state machine, backed by an append-only remediations history."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Session

from app.models import Finding, FindingStatus, Remediation

# OPEN -> RESOLVED is deliberately allowed, not just OPEN -> IN_PROGRESS -> RESOLVED.
# IN_PROGRESS models a human picking a finding up; the auto-resolve path in
# comparison_service (a retest re-sending the byte-identical execution_prompt and
# getting a PASS) is evidence-backed resolution that never passes through a human
# triage step. Findings are always created OPEN by finding_service, so requiring
# IN_PROGRESS first made every FIXED classification raise InvalidTransitionError,
# which surfaced as an HTTP 400 from POST /comparisons *after* the
# retest_comparisons row had already been committed - breaking the
# harden -> retest -> resolve loop and leaving inconsistent state behind.
ALLOWED_TRANSITIONS: dict[FindingStatus, set[FindingStatus]] = {
    FindingStatus.OPEN: {
        FindingStatus.IN_PROGRESS,
        FindingStatus.RESOLVED,
        FindingStatus.ACCEPT_RISK,
    },
    FindingStatus.IN_PROGRESS: {FindingStatus.RESOLVED, FindingStatus.ACCEPT_RISK},
    FindingStatus.RESOLVED: {FindingStatus.ACCEPT_RISK},
    FindingStatus.ACCEPT_RISK: set(),
}


class InvalidTransitionError(ValueError):
    pass


def _is_allowed(current: FindingStatus, target: FindingStatus) -> bool:
    if target == FindingStatus.ACCEPT_RISK:
        return True  # ACCEPT_RISK is reachable from any state, per the plan.
    if current == target:
        return True  # idempotent no-op re-set (e.g. re-noting the same status)
    return target in ALLOWED_TRANSITIONS.get(current, set())


def set_status(
    session: Session,
    finding: Finding,
    new_status: FindingStatus,
    note: str | None,
    changed_by: str,
) -> Finding:
    if not _is_allowed(finding.status, new_status):
        raise InvalidTransitionError(
            f"Cannot transition finding {finding.id} from {finding.status.value} "
            f"to {new_status.value}. Allowed transitions: OPEN->IN_PROGRESS->RESOLVED "
            "(OPEN->RESOLVED directly is also permitted, for evidence-backed retest "
            "auto-resolution), or ->ACCEPT_RISK from any state."
        )

    remediation = Remediation(
        finding_id=finding.id,
        status=new_status,
        note=note,
        changed_by=changed_by,
    )
    session.add(remediation)

    finding.status = new_status
    finding.updated_at = datetime.now(timezone.utc)
    if new_status == FindingStatus.RESOLVED:
        finding.resolved_at = datetime.now(timezone.utc)
    session.add(finding)
    session.commit()
    session.refresh(finding)
    return finding
