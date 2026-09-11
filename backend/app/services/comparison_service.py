"""Before/after diff between two test_runs, joined on test_case_id.

Classification (per test_case_id present in either run):
  FIXED      - present in baseline as FAIL/REVIEW, present in retest as PASS
  REMAINING  - present in baseline as FAIL/REVIEW, still FAIL/REVIEW in retest
  REGRESSION - present in baseline as PASS, now FAIL/REVIEW in retest
  NEW        - present in retest only (not exercised in baseline) as FAIL/REVIEW

Pure classification logic (`classify`) takes plain dicts so it can be unit
tested without a DB. `compare()` is the DB-facing wrapper that fetches rows,
persists a retest_comparisons row, and applies the finding side-effects
described in the plan (FIXED -> resolve finding, REGRESSION -> new finding).
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Iterable

logger = logging.getLogger("harness.comparison")

FAILING = {"FAIL", "REVIEW"}


@dataclass
class ResultRow:
    test_case_id: str
    result: str  # PASS | FAIL | REVIEW | ERROR


def classify(
    baseline_results: Iterable[ResultRow], retest_results: Iterable[ResultRow]
) -> list[dict]:
    """Return one classification dict per test_case_id touched by either run."""
    baseline_by_case = {r.test_case_id: r.result for r in baseline_results}
    retest_by_case = {r.test_case_id: r.result for r in retest_results}

    all_case_ids = set(baseline_by_case) | set(retest_by_case)
    details: list[dict] = []

    for case_id in all_case_ids:
        baseline_result = baseline_by_case.get(case_id)
        retest_result = retest_by_case.get(case_id)

        if baseline_result is None:
            # Only exercised in the retest (e.g. full_suite retest touching a
            # case that wasn't a failure in baseline but wasn't run there either).
            if retest_result in FAILING:
                classification = "NEW"
            else:
                continue  # passed and wasn't in baseline — nothing to report
        elif retest_result is None:
            # In baseline but not re-executed this retest (failed_only scope
            # that, for some reason, skipped it) — treat as still open/unknown.
            continue
        elif baseline_result in FAILING and retest_result == "PASS":
            classification = "FIXED"
        elif baseline_result in FAILING and retest_result in FAILING:
            classification = "REMAINING"
        elif baseline_result == "PASS" and retest_result in FAILING:
            classification = "REGRESSION"
        else:
            continue  # PASS -> PASS, or ERROR states: nothing to classify

        details.append(
            {
                "test_case_id": case_id,
                "classification": classification,
                "baseline_result": baseline_result,
                "retest_result": retest_result,
            }
        )

    return details


def summarize(details: list[dict]) -> dict[str, int]:
    counts = {"FIXED": 0, "REMAINING": 0, "REGRESSION": 0, "NEW": 0}
    for d in details:
        counts[d["classification"]] += 1
    return counts


def compare(session, baseline_run_id, retest_run_id):
    """Fetch results for both runs, classify, persist, and apply side-effects."""
    from sqlmodel import select

    from app.models import Application, FindingStatus, RetestComparison, TestResult, TestRun
    from app.services import finding_service, remediation_service

    baseline_run_obj: TestRun = session.get(TestRun, baseline_run_id)
    retest_run_obj: TestRun = session.get(TestRun, retest_run_id)
    if baseline_run_obj is None or retest_run_obj is None:
        raise ValueError("baseline_run_id and retest_run_id must both exist")

    baseline_rows = [
        ResultRow(str(r.test_case_id), r.result.value)
        for r in session.exec(select(TestResult).where(TestResult.test_run_id == baseline_run_id))
    ]
    retest_rows = [
        ResultRow(str(r.test_case_id), r.result.value)
        for r in session.exec(select(TestResult).where(TestResult.test_run_id == retest_run_id))
    ]
    # Map test_case_id -> latest retest TestResult row, for finding creation/lookup.
    retest_result_by_case = {
        str(r.test_case_id): r
        for r in session.exec(select(TestResult).where(TestResult.test_run_id == retest_run_id))
    }

    details = classify(baseline_rows, retest_rows)
    counts = summarize(details)

    comparison = RetestComparison(
        application_id=baseline_run_obj.application_id,
        baseline_run_id=baseline_run_id,
        retest_run_id=retest_run_id,
        fixed_count=counts["FIXED"],
        remaining_count=counts["REMAINING"],
        regression_count=counts["REGRESSION"],
        new_count=counts["NEW"],
        details=details,
    )
    session.add(comparison)
    session.commit()
    session.refresh(comparison)

    application = session.get(Application, baseline_run_obj.application_id)

    # The retest_comparisons row above is already committed. From here on, each
    # per-finding side-effect is isolated: one failure (an unexpected status
    # transition, a missing row) must not abort the remaining rows and must not
    # turn an already-persisted comparison into an HTTP error, which would leave
    # the caller believing no comparison exists when one does. Failures are
    # recorded on the returned object so they stay visible rather than silent.
    side_effect_errors: list[str] = []

    for row in details:
        case_id = row["test_case_id"]
        try:
            if row["classification"] == "FIXED":
                existing = finding_service.find_open_finding_for_case(
                    session, baseline_run_obj.application_id, uuid.UUID(case_id)
                )
                if existing is not None:
                    remediation_service.set_status(
                        session,
                        existing,
                        FindingStatus.RESOLVED,
                        note=(
                            f"Auto-resolved: retest {retest_run_id} confirmed this test case "
                            "now PASSes with the exact same prompt."
                        ),
                        changed_by="comparison_service",
                    )
            elif row["classification"] == "REGRESSION":
                retest_result = retest_result_by_case.get(case_id)
                if retest_result is not None and application is not None:
                    finding_service.upsert_finding_for_result(
                        session, application, retest_run_obj, retest_result
                    )
        except Exception as exc:  # noqa: BLE001 - per-row isolation, see comment above
            session.rollback()
            logger.exception(
                "Finding side-effect failed for test_case_id=%s (%s)",
                case_id,
                row["classification"],
            )
            side_effect_errors.append(
                f"{row['classification']} test_case_id={case_id}: "
                f"{type(exc).__name__}: {exc}"
            )

    if side_effect_errors:
        comparison.details = [
            *details,
            {"_side_effect_errors": side_effect_errors},
        ]
        session.add(comparison)
        session.commit()
        session.refresh(comparison)

    return comparison
