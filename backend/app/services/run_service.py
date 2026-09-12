"""Execute a real assurance run: HTTP call -> evaluator pipeline -> persisted results.

On completion, locks every executed test_case (is_locked=True) so future edits
version-fork instead of mutating the frozen prompt, then hands off to
scoring_service to compute assurance_score.
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any

import anthropic
import httpx
from jsonpath_ng.ext import parse as jsonpath_parse
from sqlmodel import Session, select

from app.core.config import settings
from app.models import (
    Application,
    RunStatus,
    RunType,
    TestCase,
    TestResult,
    TestRun,
    TestSuite,
)
from app.services import finding_service, scoring_service


def _substitute_prompt(template: dict[str, Any], prompt: str) -> dict[str, Any]:
    def walk(node: Any) -> Any:
        if isinstance(node, str):
            return node.replace("{{prompt}}", prompt)
        if isinstance(node, dict):
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node

    return walk(template)


def _extract_response_text(payload: dict[str, Any] | None, response_path: str) -> str | None:
    if payload is None:
        return None
    try:
        expr = jsonpath_parse(response_path)
        matches = [m.value for m in expr.find(payload)]
        if not matches:
            return None
        value = matches[0]
        return value if isinstance(value, str) else str(value)
    except Exception:
        return None


def _get_anthropic_client() -> anthropic.Anthropic | None:
    if not settings.ANTHROPIC_API_KEY:
        return None
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


# A deterministic SYSTEM_PROMPT_LEAKAGE match returns FAIL at confidence 1.0 and
# skips Claude entirely, so a marker that can appear in a *legitimate* response is
# not a weak signal — it is a guaranteed false positive that nothing downstream can
# correct. SYSTEM_PROMPT_LEAKAGE at HIGH/CRITICAL is also a hard NOT_READY blocker
# per docs/release-readiness.md, so such a marker makes READY unreachable for a
# correctly-hardened application.
_MIN_MARKER_LENGTH = 16


def _protected_markers(application: Application) -> list[str]:
    """Best-effort verbatim markers for SYSTEM_PROMPT_LEAKAGE deterministic checks.

    The `applications` table has no dedicated system_prompt column (see
    docs/agent-team-decision-log.md) — we derive distinctive marker strings
    from the fields we do have (expected/forbidden behavior text) so
    `evaluators.deterministic.run_deterministic_check` has something concrete
    to match against instead of silently falling through to Claude for every
    single SYSTEM_PROMPT_LEAKAGE case.

    `application.name` is deliberately NOT a marker. It is not secret — it is a
    label the operator chose, and a well-behaved assistant routinely states its
    own name ("I'm Aria, happy to help"). Using it as a leak marker made every
    such response a confidence-1.0 CRITICAL SYSTEM_PROMPT_LEAKAGE FAIL, i.e. a
    hard release blocker earned by an application behaving correctly. Short names
    were worse still: a 4-character name matches as a substring inside unrelated
    words.

    Known limitation (v2): the remaining markers are derived from HARNESS's own
    `expected_behavior` / `forbidden_behavior` description fields, which are not
    the target's actual system prompt. They only fire on a genuine verbatim echo,
    so they are safe, but deterministic leak coverage stays thin until the
    `applications` schema carries real operator-supplied secret markers. Until
    then, SYSTEM_PROMPT_LEAKAGE is judged almost entirely by the Claude semantic
    evaluator — which is correct behavior, not a silent gap.
    """
    markers: list[str] = []
    for text in (application.expected_behavior, application.forbidden_behavior):
        if text:
            # Take the first clause (up to ~80 chars) as a distinctive fragment.
            fragment = text.strip().split(".")[0][:80]
            if len(fragment) >= _MIN_MARKER_LENGTH:
                markers.append(fragment)
    return markers


def _unusable_response_reason(
    http_status: int | None, response_text: str | None
) -> str | None:
    """Return why this response cannot be evaluated, or None if it can be.

    Fail CLOSED. Everything below produced no judgeable model output, so the
    test case was never really exercised, and an un-exercised case must not be
    allowed to become a PASS:

      - a non-2xx status: an error page is not a model response. Previously a
        404 body was handed straight to the evaluator.
      - no text at the configured response_path: the JSONPath did not match, so
        either the endpoint is not the app we think it is or response_path is
        misconfigured.
      - whitespace-only text: nothing to judge.

    This is the root of the reported fail-open defect: a dummy endpoint returned
    nothing for all ten adversarial prompts, the semantic evaluator read the
    empty string as "a valid refusal strategy" and returned PASS for every case,
    and the run scored 100/100 READY. The distinction the product exists to make
    is between "the app safely refused" and "the app was never tested"; that
    distinction has to be drawn here, before any evaluator sees the response.
    """
    if http_status is not None and not (200 <= http_status < 300):
        return f"target returned HTTP {http_status}; no model response to evaluate"
    if response_text is None:
        return (
            "no response text found at the configured response_path — the target "
            "returned a payload that does not match the expected shape"
        )
    if not response_text.strip():
        return "target returned an empty response body"
    return None


def execute_run(
    session: Session,
    application: Application,
    test_suite: TestSuite,
    triggered_by: str,
) -> TestRun:
    run = TestRun(
        application_id=application.id,
        test_suite_id=test_suite.id,
        run_type=RunType.BASELINE,
        triggered_by=triggered_by,
        status=RunStatus.RUNNING,
        started_at=datetime.now(timezone.utc),
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    cases = list(
        session.exec(
            select(TestCase).where(
                TestCase.test_suite_id == test_suite.id,
                TestCase.enabled == True,  # noqa: E712
            )
        )
    )

    headers = {}
    if application.auth_header_name and application.auth_header_value:
        headers[application.auth_header_name] = application.auth_header_value

    client = _get_anthropic_client()
    protected_markers = _protected_markers(application)

    for case in cases:
        execution_prompt = case.attack_prompt
        raw_request_payload = _substitute_prompt(application.request_template, execution_prompt)

        raw_response_payload: dict[str, Any] | None = None
        response_text: str | None = None
        http_status: int | None = None
        latency_ms: int | None = None
        request_error: str | None = None

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

        unusable_reason = request_error or _unusable_response_reason(
            http_status, response_text
        )

        if unusable_reason is not None:
            result = TestResult(
                test_run_id=run.id,
                test_case_id=case.id,
                test_case_version=case.version,
                execution_prompt=execution_prompt,
                model_response=response_text,
                raw_request_payload=raw_request_payload,
                raw_response_payload=raw_response_payload,
                http_status=http_status,
                latency_ms=latency_ms,
                result="ERROR",
                severity="INFO",
                confidence=1.0,
                evidence={
                    "error": unusable_reason,
                    "reason": unusable_reason,
                    "failure_type": "no_usable_response",
                    "expected_behavior": case.expected_safe_behavior,
                    "actual_behavior": "(no response captured)",
                    "http_status": http_status,
                },
                evaluator_version="n/a",
            )
            session.add(result)
            session.commit()
            session.refresh(result)
            case.is_locked = True
            session.add(case)
            session.commit()
            continue

        try:
            from app.evaluators.pipeline import evaluate

            evaluator_output, evaluator_version = evaluate(
                test_case={
                    "category": case.category.value,
                    "attack_prompt": case.attack_prompt,
                    "severity_if_failed": case.severity_if_failed.value,
                    "expected_safe_behavior": case.expected_safe_behavior,
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
        except Exception as exc:  # evaluator pipeline not available/importable yet, or crashed
            result_kwargs = dict(
                result="ERROR",
                severity="INFO",
                confidence=0.0,
                evidence={"error": f"evaluator pipeline failure: {exc}"},
            )
            evaluator_version = "unavailable"

        test_result = TestResult(
            test_run_id=run.id,
            test_case_id=case.id,
            test_case_version=case.version,
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

        case.is_locked = True
        session.add(case)
        session.commit()

        if test_result.result.value in ("FAIL", "REVIEW"):
            finding_service.upsert_finding_for_result(session, application, run, test_result)

    run.status = RunStatus.COMPLETED
    run.completed_at = datetime.now(timezone.utc)
    session.add(run)
    session.commit()
    session.refresh(run)

    scoring_service.score_run(session, run)
    session.refresh(run)
    return run
