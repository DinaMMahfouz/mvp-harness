"""Live DB queries backing the Excel export — no cached/fake data."""
from __future__ import annotations

import uuid

from sqlmodel import Session, select

from app.models import (
    Application,
    Finding,
    Remediation,
    RetestComparison,
    TestCase,
    TestResult,
    TestRun,
)


def findings_for_application(session: Session, application_id: uuid.UUID) -> list[Finding]:
    return list(
        session.exec(
            select(Finding)
            .where(Finding.application_id == application_id)
            .order_by(Finding.created_at.desc())
        )
    )


def runs_for_application(session: Session, application_id: uuid.UUID) -> list[TestRun]:
    return list(
        session.exec(
            select(TestRun)
            .where(TestRun.application_id == application_id)
            .order_by(TestRun.created_at.desc())
        )
    )


def results_for_run(session: Session, run_id: uuid.UUID) -> list[TestResult]:
    return list(session.exec(select(TestResult).where(TestResult.test_run_id == run_id)))


def remediations_for_finding(session: Session, finding_id: uuid.UUID) -> list[Remediation]:
    return list(
        session.exec(
            select(Remediation)
            .where(Remediation.finding_id == finding_id)
            .order_by(Remediation.changed_at.asc())
        )
    )


def comparisons_for_application(
    session: Session, application_id: uuid.UUID
) -> list[RetestComparison]:
    return list(
        session.exec(
            select(RetestComparison)
            .where(RetestComparison.application_id == application_id)
            .order_by(RetestComparison.created_at.desc())
        )
    )


def test_case(session: Session, test_case_id: uuid.UUID) -> TestCase | None:
    return session.get(TestCase, test_case_id)
