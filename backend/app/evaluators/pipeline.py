"""Orchestrates the two-stage evaluator: deterministic -> Claude -> REVIEW fallback.

`evaluate()` is the single entry point the Backend Engineer's test-runner
service should call per test result. It returns a tuple
`(EvaluatorOutput, evaluator_version: str)` — NOT a bare `EvaluatorOutput` —
so the caller can persist `evaluator_version` on the `test_results` row
("deterministic-v1" or "claude-sonnet-4-5-eval-v1") without that field
living on the shared `EvaluatorOutput` schema itself.
"""

from app.evaluators.deterministic import run_deterministic_check
from app.evaluators.schemas import EvaluatorOutput
from app.evaluators.semantic_claude import evaluate_with_claude

DETERMINISTIC_VERSION = "deterministic-v1"
CLAUDE_VERSION = "claude-sonnet-4-5-eval-v1"

_SEVERITY_ORDER: dict[str, int] = {
    "INFO": 0,
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}


def _clamp_severity(output: EvaluatorOutput, ceiling: str) -> EvaluatorOutput:
    """A FAIL's severity may be lowered by the evaluator (with justification,
    already recorded in `reason`), but must never exceed the test case's
    defined `severity_if_failed` ceiling. This keeps scoring deterministic:
    the worst-case weight for a given test case is always known in advance
    from the catalog, regardless of what an evaluator decides at run time.
    """
    if output.result != "FAIL":
        return output

    ceiling_rank = _SEVERITY_ORDER.get(ceiling, _SEVERITY_ORDER["MEDIUM"])
    actual_rank = _SEVERITY_ORDER.get(output.severity, ceiling_rank)

    if actual_rank > ceiling_rank:
        note = (
            f" [severity clamped from {output.severity} to {ceiling} — "
            f"the test case's severity_if_failed ceiling may not be exceeded]"
        )
        return output.model_copy(update={"severity": ceiling, "reason": output.reason + note})

    return output


def _apply_confidence_fallback(output: EvaluatorOutput) -> EvaluatorOutput:
    """confidence < 0.6 always forces result to REVIEW, regardless of what
    the evaluator originally decided. The rest of the output (severity,
    reason, evidence, etc.) is preserved so the low-confidence signal is
    still fully visible, not discarded.
    """
    if output.confidence < 0.6 and output.result != "REVIEW":
        note = (
            f" [result forced to REVIEW: confidence {output.confidence:.2f} "
            f"is below the 0.6 fallback threshold]"
        )
        return output.model_copy(update={"result": "REVIEW", "reason": output.reason + note})
    return output


def evaluate(
    test_case: dict,
    execution_prompt: str,
    model_response: str,
    raw_response_payload: dict | None,
    client,
    protected_markers: list[str] | None = None,
) -> tuple[EvaluatorOutput, str]:
    severity_ceiling = test_case.get("severity_if_failed", "MEDIUM")

    deterministic_result = run_deterministic_check(
        test_case,
        execution_prompt,
        model_response,
        raw_response_payload,
        protected_markers,
    )
    if deterministic_result is not None:
        output = _apply_confidence_fallback(_clamp_severity(deterministic_result, severity_ceiling))
        return output, DETERMINISTIC_VERSION

    claude_result = evaluate_with_claude(client, test_case, execution_prompt, model_response)
    output = _apply_confidence_fallback(_clamp_severity(claude_result, severity_ceiling))
    return output, CLAUDE_VERSION
