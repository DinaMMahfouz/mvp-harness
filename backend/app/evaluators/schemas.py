"""Shared output schema for both the deterministic and Claude evaluators.

This is the single contract both evaluator stages (deterministic.py,
semantic_claude.py) must produce, and the only thing pipeline.py and the
Backend Engineer's persistence layer need to know about. It intentionally
does NOT carry `evaluator_version` — that string is returned alongside this
model as a tuple `(EvaluatorOutput, evaluator_version)` from every evaluator
function and from `pipeline.evaluate()`, so the caller can persist it on the
`test_results` row without polluting this schema.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Severity = Literal["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
# ERROR is a first-class outcome, not an absence of one. A target that returned
# nothing usable was never actually tested, and "not tested" must never be
# representable as PASS - see run_service._unusable_response_reason and
# scoring_service.compute_release_decision.
Result = Literal["PASS", "FAIL", "REVIEW", "ERROR"]


class EvaluatorOutput(BaseModel):
    result: Result
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    evidence: list[str] = Field(default_factory=list)
    failure_type: str | None = None
    expected_behavior: str
    actual_behavior: str

    @field_validator("confidence")
    @classmethod
    def _confidence_in_range(cls, v: float) -> float:
        # Redundant with Field(ge=0.0, le=1.0) but kept explicit per spec so
        # the "0-1 validated range" requirement is unmistakable in review.
        if not (0.0 <= v <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v

    @model_validator(mode="after")
    def _failure_type_only_on_fail(self) -> "EvaluatorOutput":
        # ERROR keeps its failure_type: it carries *why* the result is unusable
        # (no_response_captured, http_4xx, ...), which is the whole diagnostic
        # value of an ERROR row.
        if self.result not in ("FAIL", "ERROR") and self.failure_type is not None:
            # Non-fatal normalization rather than a hard error: an evaluator
            # (deterministic or Claude) that sets a failure_type on a
            # PASS/REVIEW result is almost certainly confused, not malicious,
            # so we clear the field instead of rejecting a mostly-good output.
            self.failure_type = None
        return self
