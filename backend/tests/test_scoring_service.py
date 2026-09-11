"""Unit tests for scoring_service — all three release-decision branches,
plus the assurance_score formula, exercised against synthetic data only
(no DB / no network), per the plan's verification requirements.
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace

from app.services.scoring_service import compute_assurance_score, compute_release_decision


def _finding(severity="MEDIUM", status="OPEN", category="PROMPT_INJECTION", fid=None):
    return SimpleNamespace(id=fid or uuid.uuid4(), severity=severity, status=status, category=category)


def _review(result="REVIEW", confidence=0.9):
    return SimpleNamespace(result=result, confidence=confidence)


def _case(severity_if_failed="MEDIUM"):
    return SimpleNamespace(severity_if_failed=severity_if_failed)


# ---------------------------------------------------------------------------
# compute_assurance_score
# ---------------------------------------------------------------------------


def test_assurance_score_no_findings_is_100():
    score = compute_assurance_score([], [_case("HIGH"), _case("CRITICAL")])
    assert score == 100.0


def test_assurance_score_empty_suite_is_100():
    score = compute_assurance_score([_finding("CRITICAL")], [])
    assert score == 100.0


def test_assurance_score_partial_open_weight():
    # max_weight = HIGH(4) + CRITICAL(6) = 10; open_weight = HIGH(4) -> score = 100*(1-4/10) = 60
    score = compute_assurance_score([_finding("HIGH")], [_case("HIGH"), _case("CRITICAL")])
    assert score == 60.0


def test_assurance_score_clamped_at_zero():
    # open_weight can exceed max_weight if RESOLVED/ACCEPT_RISK findings aren't
    # filtered by the caller before this function — guard against negative scores.
    score = compute_assurance_score(
        [_finding("CRITICAL"), _finding("CRITICAL")], [_case("LOW")]
    )
    assert score == 0.0


# ---------------------------------------------------------------------------
# compute_release_decision — NOT_READY branch
# ---------------------------------------------------------------------------


def test_not_ready_on_open_critical_finding():
    result = compute_release_decision(
        app_type="CHATBOT",
        all_findings=[_finding(severity="CRITICAL", status="OPEN", category="SYSTEM_PROMPT_LEAKAGE")],
        review_results=[],
        executed_categories={"PROMPT_INJECTION", "SYSTEM_PROMPT_LEAKAGE", "SCOPE_ESCAPE", "HALLUCINATION_TRAP", "UNSUPPORTED_CLAIMS"},
        regression_count=0,
        assurance_score=40.0,
    )
    assert result.decision == "NOT_READY"
    assert result.blocking_findings_count == 1
    assert "CRITICAL" in result.rationale


def test_not_ready_on_unauthorized_tool_request():
    result = compute_release_decision(
        app_type="AGENT",
        all_findings=[_finding(severity="MEDIUM", status="IN_PROGRESS", category="UNAUTHORIZED_TOOL_REQUEST")],
        review_results=[],
        executed_categories={"PROMPT_INJECTION", "SCOPE_ESCAPE", "UNAUTHORIZED_TOOL_REQUEST", "UNSAFE_PARAMETERS"},
        regression_count=0,
        assurance_score=90.0,
    )
    assert result.decision == "NOT_READY"


def test_not_ready_on_protected_data_exposure_high_or_above():
    result = compute_release_decision(
        app_type="CHATBOT",
        all_findings=[_finding(severity="HIGH", status="OPEN", category="SYSTEM_PROMPT_LEAKAGE")],
        review_results=[],
        executed_categories={"PROMPT_INJECTION", "SYSTEM_PROMPT_LEAKAGE", "SCOPE_ESCAPE", "HALLUCINATION_TRAP", "UNSUPPORTED_CLAIMS"},
        regression_count=0,
        assurance_score=80.0,
    )
    assert result.decision == "NOT_READY"


def test_system_prompt_leakage_below_high_does_not_trigger_not_ready_alone():
    # MEDIUM severity SYSTEM_PROMPT_LEAKAGE isn't a NOT_READY blocker by itself.
    result = compute_release_decision(
        app_type="CHATBOT",
        all_findings=[_finding(severity="MEDIUM", status="OPEN", category="SYSTEM_PROMPT_LEAKAGE")],
        review_results=[],
        executed_categories={"PROMPT_INJECTION", "SYSTEM_PROMPT_LEAKAGE", "SCOPE_ESCAPE", "HALLUCINATION_TRAP", "UNSUPPORTED_CLAIMS"},
        regression_count=0,
        assurance_score=95.0,
    )
    assert result.decision != "NOT_READY"


# ---------------------------------------------------------------------------
# compute_release_decision — READY_WITH_CONDITIONS branch
# ---------------------------------------------------------------------------


def test_ready_with_conditions_on_open_high_finding():
    result = compute_release_decision(
        app_type="RAG",
        all_findings=[_finding(severity="HIGH", status="OPEN", category="HALLUCINATION_TRAP")],
        review_results=[],
        executed_categories={"PROMPT_INJECTION", "SYSTEM_PROMPT_LEAKAGE", "HALLUCINATION_TRAP", "UNSUPPORTED_CLAIMS"},
        regression_count=0,
        assurance_score=70.0,
    )
    assert result.decision == "READY_WITH_CONDITIONS"
    assert result.conditions


def test_ready_with_conditions_on_accept_risk_critical_finding():
    # QA regression (docs/qa-review.md defect #2): an ACCEPT_RISK CRITICAL
    # finding is not OPEN/IN_PROGRESS so it must not trigger NOT_READY, but it
    # must not silently disappear into an unconditional READY either -- the
    # accepted risk must stay visible in the rationale trace.
    result = compute_release_decision(
        app_type="CHATBOT",
        all_findings=[_finding(severity="CRITICAL", status="ACCEPT_RISK", category="SYSTEM_PROMPT_LEAKAGE")],
        review_results=[],
        executed_categories={"PROMPT_INJECTION", "SYSTEM_PROMPT_LEAKAGE", "SCOPE_ESCAPE", "HALLUCINATION_TRAP", "UNSUPPORTED_CLAIMS"},
        regression_count=0,
        assurance_score=100.0,
    )
    assert result.decision == "READY_WITH_CONDITIONS"
    assert any("ACCEPT_RISK" in c for c in result.conditions)


def test_ready_with_conditions_on_accept_risk_high_finding():
    result = compute_release_decision(
        app_type="RAG",
        all_findings=[_finding(severity="HIGH", status="ACCEPT_RISK", category="HALLUCINATION_TRAP")],
        review_results=[],
        executed_categories={"PROMPT_INJECTION", "SYSTEM_PROMPT_LEAKAGE", "HALLUCINATION_TRAP", "UNSUPPORTED_CLAIMS"},
        regression_count=0,
        assurance_score=70.0,
    )
    assert result.decision == "READY_WITH_CONDITIONS"


def test_ready_with_conditions_on_low_confidence_review():
    result = compute_release_decision(
        app_type="RAG",
        all_findings=[],
        review_results=[_review(confidence=0.4)],
        executed_categories={"PROMPT_INJECTION", "SYSTEM_PROMPT_LEAKAGE", "HALLUCINATION_TRAP", "UNSUPPORTED_CLAIMS"},
        regression_count=0,
        assurance_score=90.0,
    )
    assert result.decision == "READY_WITH_CONDITIONS"


def test_high_confidence_review_does_not_trigger_conditions():
    result = compute_release_decision(
        app_type="RAG",
        all_findings=[],
        review_results=[_review(confidence=0.8)],
        executed_categories={"PROMPT_INJECTION", "SYSTEM_PROMPT_LEAKAGE", "HALLUCINATION_TRAP", "UNSUPPORTED_CLAIMS"},
        regression_count=0,
        assurance_score=95.0,
    )
    assert result.decision == "READY"


# ---------------------------------------------------------------------------
# compute_release_decision — READY branch
# ---------------------------------------------------------------------------


def test_ready_when_clean_and_all_categories_executed():
    result = compute_release_decision(
        app_type="CHATBOT",
        all_findings=[],
        review_results=[],
        executed_categories={"PROMPT_INJECTION", "SYSTEM_PROMPT_LEAKAGE", "SCOPE_ESCAPE", "HALLUCINATION_TRAP", "UNSUPPORTED_CLAIMS"},
        regression_count=0,
        assurance_score=100.0,
    )
    assert result.decision == "READY"
    assert result.blocking_findings_count == 0
    assert result.conditions == []


def test_ready_downgrades_to_conditions_when_required_category_missing():
    result = compute_release_decision(
        app_type="CHATBOT",
        all_findings=[],
        review_results=[],
        executed_categories={"PROMPT_INJECTION"},  # missing 4 required categories
        regression_count=0,
        assurance_score=100.0,
    )
    assert result.decision == "READY_WITH_CONDITIONS"


def test_ready_downgrades_to_conditions_on_regression():
    result = compute_release_decision(
        app_type="CHATBOT",
        all_findings=[],
        review_results=[],
        executed_categories={"PROMPT_INJECTION", "SYSTEM_PROMPT_LEAKAGE", "SCOPE_ESCAPE", "HALLUCINATION_TRAP", "UNSUPPORTED_CLAIMS"},
        regression_count=2,
        assurance_score=90.0,
        has_retest=True,
    )
    assert result.decision == "READY_WITH_CONDITIONS"
    assert "regression" in result.rationale.lower()


def test_ready_ignores_regression_count_when_no_retest_exists():
    # regression_count would only be nonzero if a comparison exists; has_retest=False
    # models "no retest_comparisons row for this run" explicitly.
    result = compute_release_decision(
        app_type="CHATBOT",
        all_findings=[],
        review_results=[],
        executed_categories={"PROMPT_INJECTION", "SYSTEM_PROMPT_LEAKAGE", "SCOPE_ESCAPE", "HALLUCINATION_TRAP", "UNSUPPORTED_CLAIMS"},
        regression_count=0,
        assurance_score=100.0,
        has_retest=False,
    )
    assert result.decision == "READY"


def test_resolved_findings_do_not_block_ready():
    result = compute_release_decision(
        app_type="CHATBOT",
        all_findings=[_finding(severity="CRITICAL", status="RESOLVED")],
        review_results=[],
        executed_categories={"PROMPT_INJECTION", "SYSTEM_PROMPT_LEAKAGE", "SCOPE_ESCAPE", "HALLUCINATION_TRAP", "UNSUPPORTED_CLAIMS"},
        regression_count=0,
        assurance_score=100.0,
    )
    assert result.decision == "READY"
