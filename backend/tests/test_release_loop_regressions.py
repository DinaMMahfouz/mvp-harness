"""Regression tests for two defects that broke the harden -> retest -> release loop.

Both are pure-logic tests (no DB, no network) covering the seam docs/qa-review.md
defect #5 flagged as untested: the DB-facing side of the services.

Defect A — remediation_service.ALLOWED_TRANSITIONS omitted OPEN -> RESOLVED.
  finding_service always creates findings with status=OPEN, and
  comparison_service's FIXED path calls set_status(..., RESOLVED) on whatever
  find_open_finding_for_case returns. Every auto-resolve therefore raised
  InvalidTransitionError. Because InvalidTransitionError subclasses ValueError,
  POST /comparisons caught it and returned HTTP 400 *after* the
  retest_comparisons row was already committed.

Defect B — run_service._protected_markers used application.name as a verbatim
  SYSTEM_PROMPT_LEAKAGE marker. A deterministic match is FAIL at confidence 1.0
  and skips the Claude evaluator, and SYSTEM_PROMPT_LEAKAGE at HIGH/CRITICAL is a
  hard NOT_READY blocker — so an assistant stating its own name made READY
  unreachable.
"""
from __future__ import annotations

import uuid

import pytest

from app.models import Application, AppType, FindingStatus
from app.services.remediation_service import ALLOWED_TRANSITIONS, _is_allowed
from app.services.run_service import _protected_markers


# --- Defect A ---------------------------------------------------------------

def test_open_can_resolve_directly():
    """The auto-resolve path never passes through IN_PROGRESS."""
    assert _is_allowed(FindingStatus.OPEN, FindingStatus.RESOLVED) is True
    assert FindingStatus.RESOLVED in ALLOWED_TRANSITIONS[FindingStatus.OPEN]


def test_in_progress_can_still_resolve():
    assert _is_allowed(FindingStatus.IN_PROGRESS, FindingStatus.RESOLVED) is True


def test_accept_risk_remains_terminal():
    """Widening OPEN must not accidentally reopen a terminal state."""
    assert ALLOWED_TRANSITIONS[FindingStatus.ACCEPT_RISK] == set()
    assert _is_allowed(FindingStatus.ACCEPT_RISK, FindingStatus.OPEN) is False
    assert _is_allowed(FindingStatus.ACCEPT_RISK, FindingStatus.RESOLVED) is False


def test_resolved_cannot_silently_reopen():
    assert _is_allowed(FindingStatus.RESOLVED, FindingStatus.OPEN) is False
    assert _is_allowed(FindingStatus.RESOLVED, FindingStatus.IN_PROGRESS) is False


def test_accept_risk_still_reachable_from_anywhere():
    for current in FindingStatus:
        assert _is_allowed(current, FindingStatus.ACCEPT_RISK) is True


# --- Defect B ---------------------------------------------------------------

def _app(name: str, expected: str = "", forbidden: str = "") -> Application:
    return Application(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        name=name,
        app_type=AppType.CHATBOT,
        expected_behavior=expected,
        forbidden_behavior=forbidden,
        endpoint_url="http://localhost:8001/chat",
        request_template={"message": "{{prompt}}"},
        response_path="$.response",
    )


def test_application_name_is_never_a_leak_marker():
    """An assistant saying its own name is correct behavior, not a leak."""
    app = _app(name="Aria")
    assert "Aria" not in _protected_markers(app)


def test_short_name_cannot_substring_match():
    """A 4-char name would otherwise match inside unrelated words ('Aria' in 'Arial')."""
    app = _app(name="Aria")
    benign_response = "Hi, I'm Aria. Your Acme Pro plan includes Gantt charts."
    assert not any(m in benign_response for m in _protected_markers(app))


def test_behavior_fragments_are_still_markers_when_long_enough():
    app = _app(
        name="Aria",
        expected="Answer only from the documented Acme Corp plans and policies. Nothing else.",
    )
    markers = _protected_markers(app)
    assert markers, "long behavior fragments should still produce markers"
    assert all(len(m) >= 16 for m in markers)


def test_short_behavior_fragments_are_rejected():
    app = _app(name="Aria", expected="Be helpful.", forbidden="No.")
    assert _protected_markers(app) == []


@pytest.mark.parametrize("name", ["A", "Bot", "Aria", "Acme"])
def test_no_marker_derives_from_name_alone(name):
    assert _protected_markers(_app(name=name)) == []
