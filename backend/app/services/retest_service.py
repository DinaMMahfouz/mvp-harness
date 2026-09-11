"""Exact retest: resend the byte-identical stored execution_prompt, never re-templated.

This is what makes the before/after comparison defensible — a retest_run's
test_results reference the SAME test_case_id and its ORIGINAL
test_case_version (frozen at the time the source result was created), even if
the test_case has since been edited/re-versioned.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Literal

import anthropic
import httpx
from sqlmodel import Session, select

from app.core.config import settings
from app.models import Application, RunStatus, RunType, TestResult, TestRun
from app.services import finding_service, scoring_service
from app.services.run_service import _extract_response_text, _protected_markers


def _get_anthropic_client() -> anthropic.Anthropic | None:
    if not settings.ANTHROPIC_API_KEY:
        return None
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def retest(
    session: Session,
    application: Application,
    based_on_run_id,
    scope: Literal["failed_only", "full_suite"] = "failed_only",
    triggered_by: str = "manual",
) -> TestRun:
    baseline_run = session.get(TestRun, based_on_run_id)
    if baseline_run is None:
        raise ValueError(f"No test_run found for id={based_on_run_id}")

    source_results = list(
        session.exec(select(TestResult).where(TestResult.test_run_id == baseline_run.id))
    )
    if scope == "failed_only":
        source_results = [r for r in source_results if r.result.value in ("FAIL", "REVIEW")]

    retest_run = TestRun(
        application_id=application.id,
        test_suite_id=baseline_run.test_suite_id,
        run_type=RunType.RETEST,
        triggered_by=triggered_by,
        status=RunStatus.RUNNING,
        started_at=datetime.now(timezone.utc),
    )
    session.add(retest_run)
    session.commit()
    session.refresh(retest_run)

    headers = {}
    if application.auth_header_name and application.auth_header_value:
        headers[application.auth_header_name] = application.auth_header_value

    client = _get_anthropic_client()
    protected_markers = _protected_markers(application)

    for source in source_results:
        execution_prompt = source.execution_prompt  # verbatim, never re-templated
        raw_request_payload = source.raw_request_payload

        raw_response_payload = None
        response_text = None
        http_status = None
        latency_ms = None
        request_error = None

        start = time.monotonic()
        try:
            with httpx.Client(timeout=application.timeout_seconds) as http_client:
                response = http_client.post(
                    application.endpoint_url, json=raw_request_payload, headers=headers
                )
            latency_ms = int((time.monotonic() - start) * 1000)
            http_status = response.status_code
            try:
                raw_response_payload = response.json()
            except ValueError:
                raw_response_payload = {"raw_text": response.text}
            response_text = _extract_response_text(raw_response_payload, application.response_path)
        except httpx.HTTPError as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            request_error = str(exc)

        if request_error is not None:
            result = TestResult(
                test_run_id=retest_run.id,
                test_case_id=source.test_case_id,
                test_case_version=source.test_case_version,
                execution_prompt=execution_prompt,
                raw_request_payload=raw_request_payload,
                http_status=http_status,
                latency_ms=latency_ms,
                result="ERROR",
                severity="INFO",
                confidence=1.0,
                evidence={"error": request_error},
                evaluator_version="n/a",
            )
            session.add(result)
            session.commit()
            continue

        try:
            from app.evaluators.pipeline import evaluate

            case = None
            from app.models import TestCase

            case = session.get(TestCase, source.test_case_id)
            evaluator_output, evaluator_version = evaluate(
                test_case={
                    "category": case.category.value if case else "PROMPT_INJECTION",
                    "attack_prompt": execution_prompt,
                    "severity_if_failed": case.severity_if_failed.value if case else "MEDIUM",
                    "expected_safe_behavior": case.expected_safe_behavior if case else "",
                },
                execution_prompt=execution_prompt,
                model_response=response_text or "",
                raw_response_payload=raw_response_payload,
                client=client,
                protected_markers=protected_markers,
            )
            result_kwargs = dict(
                result=evaluator_output.result,
                severity=evaluator_output.severity,
                confidence=evaluator_output.confidence,
                evidence={
                    "reason": evaluator_output.reason,
                    "evidence": evaluator_output.evidence,
                    "failure_type": evaluator_output.failure_type,
                    "expected_behavior": evaluator_output.expected_behavior,
                    "actual_behavior": evaluator_output.actual_behavior,
                },
            )
        except Exception as exc:
            result_kwargs = dict(
                result="ERROR",
                severity="INFO",
                confidence=0.0,
                evidence={"error": f"evaluator pipeline failure: {exc}"},
            )
            evaluator_version = "unavailable"

        test_result = TestResult(
            test_run_id=retest_run.id,
            test_case_id=source.test_case_id,
            test_case_version=source.test_case_version,
            execution_prompt=execution_prompt,
            model_response=response_text,
            raw_request_payload=raw_request_payload,
            raw_response_payload=raw_response_payload,
            http_status=http_status,
            latency_ms=latency_ms,
            evaluator_version=evaluator_version,
            **result_kwargs,
        )
        session.add(test_result)
        session.commit()
        session.refresh(test_result)

        if test_result.result.value in ("FAIL", "REVIEW"):
            finding_service.upsert_finding_for_result(session, application, retest_run, test_result)

    retest_run.status = RunStatus.COMPLETED
    retest_run.completed_at = datetime.now(timezone.utc)
    session.add(retest_run)
    session.commit()
    session.refresh(retest_run)

    scoring_service.score_run(session, retest_run)
    session.refresh(retest_run)
    return retest_run
