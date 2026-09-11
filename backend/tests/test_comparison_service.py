"""Unit tests for comparison_service's classify()/summarize() — synthetic
test_results only, no DB, covering FIXED / REMAINING / REGRESSION / NEW.
"""
from __future__ import annotations

from app.services.comparison_service import ResultRow, classify, summarize


def test_fixed_classification():
    baseline = [ResultRow("case-1", "FAIL")]
    retest = [ResultRow("case-1", "PASS")]
    details = classify(baseline, retest)
    assert details == [
        {
            "test_case_id": "case-1",
            "classification": "FIXED",
            "baseline_result": "FAIL",
            "retest_result": "PASS",
        }
    ]


def test_remaining_classification():
    baseline = [ResultRow("case-1", "FAIL")]
    retest = [ResultRow("case-1", "REVIEW")]
    details = classify(baseline, retest)
    assert details[0]["classification"] == "REMAINING"


def test_regression_classification():
    baseline = [ResultRow("case-1", "PASS")]
    retest = [ResultRow("case-1", "FAIL")]
    details = classify(baseline, retest)
    assert details[0]["classification"] == "REGRESSION"


def test_new_classification_when_only_in_retest_and_failing():
    baseline: list[ResultRow] = []
    retest = [ResultRow("case-2", "FAIL")]
    details = classify(baseline, retest)
    assert details[0]["classification"] == "NEW"
    assert details[0]["test_case_id"] == "case-2"


def test_pass_to_pass_is_not_reported():
    baseline = [ResultRow("case-1", "PASS")]
    retest = [ResultRow("case-1", "PASS")]
    assert classify(baseline, retest) == []


def test_new_only_in_retest_and_passing_is_not_reported():
    baseline: list[ResultRow] = []
    retest = [ResultRow("case-2", "PASS")]
    assert classify(baseline, retest) == []


def test_case_only_in_baseline_not_retested_is_skipped():
    baseline = [ResultRow("case-1", "FAIL")]
    retest: list[ResultRow] = []
    assert classify(baseline, retest) == []


def test_mixed_run_all_four_classifications():
    baseline = [
        ResultRow("fixed-case", "FAIL"),
        ResultRow("remaining-case", "FAIL"),
        ResultRow("regression-case", "PASS"),
    ]
    retest = [
        ResultRow("fixed-case", "PASS"),
        ResultRow("remaining-case", "FAIL"),
        ResultRow("regression-case", "FAIL"),
        ResultRow("new-case", "REVIEW"),
    ]
    details = classify(baseline, retest)
    counts = summarize(details)
    assert counts == {"FIXED": 1, "REMAINING": 1, "REGRESSION": 1, "NEW": 1}


def test_summarize_empty_details():
    assert summarize([]) == {"FIXED": 0, "REMAINING": 0, "REGRESSION": 0, "NEW": 0}
