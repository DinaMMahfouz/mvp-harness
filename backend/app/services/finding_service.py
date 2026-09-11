"""Create/update findings from FAIL/REVIEW test_results.

One finding is 1:1 with the test_case that produced it for a given
application — if a later run still fails the same case, we update
last_seen_run_id rather than creating a duplicate open finding. Auto-resolving
on a later PASS is explicitly NOT this module's job — that happens in
comparison_service during a retest, per the plan's ownership split.
"""
from __future__ import annotations

from sqlmodel import Session, select

from app.models import Application, Finding, FindingStatus, TestCase, TestResult, TestRun


def _title_for(category: str, severity: str) -> str:
    pretty_category = category.replace("_", " ").title()
    return f"{pretty_category} — {severity} severity finding"


def _root_cause_and_recommendation(evidence: dict) -> tuple[str, str]:
    reason = (
        evidence.get("reason")
        or "The model's response did not satisfy the expected safe behavior for this test case."
    )
    expected = evidence.get("expected_behavior") or "See the test case's expected_safe_behavior."
    actual = evidence.get("actual_behavior") or "See the recorded model_response for this test result."
    failure_type = evidence.get("failure_type") or "unspecified"

    root_cause = (
        f"Evaluator reason: {reason} Failure type: {failure_type}. "
        f"Expected behavior: {expected} Actual behavior observed: {actual}"
    )
    recommendation = (
        "Harden the application's system prompt / guardrails so that it "
        f"reliably produces: {expected} Re-run the exact same test case via "
        "retest after the fix to confirm it now passes."
    )
    return root_cause, recommendation


def find_open_finding_for_case(
    session: Session, application_id, test_case_id
) -> Finding | None:
    stmt = (
        select(Finding)
        .join(TestResult, Finding.test_result_id == TestResult.id)
        .where(
            Finding.application_id == application_id,
            TestResult.test_case_id == test_case_id,
            Finding.status.in_((FindingStatus.OPEN, FindingStatus.IN_PROGRESS)),
        )
    )
    return session.exec(stmt).first()


def upsert_finding_for_result(
    session: Session,
    application: Application,
    run: TestRun,
    test_result: TestResult,
) -> Finding:
    existing = find_open_finding_for_case(session, application.id, test_result.test_case_id)
    if existing is not None:
        existing.last_seen_run_id = run.id
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing

    case = session.get(TestCase, test_result.test_case_id)
    category = case.category.value if case else "PROMPT_INJECTION"

    root_cause, recommendation = _root_cause_and_recommendation(test_result.evidence or {})
    finding = Finding(
        application_id=application.id,
        test_result_id=test_result.id,
        category=category,
        severity=test_result.severity,
        title=_title_for(category, test_result.severity.value),
        root_cause=root_cause,
        recommendation=recommendation,
        status=FindingStatus.OPEN,
        first_seen_run_id=run.id,
        last_seen_run_id=run.id,
    )
    session.add(finding)
    session.commit()
    session.refresh(finding)
    return finding
