# HARNESS — QA / Devil's Advocate Review

Adversarial review of the backend, evaluator pipeline, and demo-target as committed at `1ceb786`
("Phases 1-10: Supabase schema, backend core ... fix broken imports + /health crash"). Assumption
throughout: nothing works until proven otherwise. This review does **not** duplicate the two
defects the Team Lead already found/fixed during smoke-testing (broken `backend.app.evaluators.X`
imports, and the unhandled 500 on `/health` — see `docs/agent-team-decision-log.md` rows 5–6);
everything below was found independently by QA.

## Summary table

| # | Severity | Area | Description | Status |
|---|----------|------|-------------|--------|
| 1 | **CRITICAL** (primary documented defect) | `backend/app/services/scoring_service.py` | `score_run()`/`decide_release()` scoped their `Finding` query to `last_seen_run_id == run.id`, silently dropping still-OPEN findings from scoring/decision the moment a *later* run doesn't happen to re-fail the same test case. Lets a real OPEN CRITICAL finding be "laundered" out of the release decision by simply re-running the suite. | **Fixed + retested** (see narrative below) |
| 2 | **CRITICAL** (security) | repo root, `.env.txt` | A real Anthropic API key (`sk-ant-api03...`) is committed to git history in commit `adde2f6` ("Phase 0: repo scaffold") and still sits, untracked-by-`.gitignore`, in the working tree. `.gitignore` only excludes `backend/.env`, `demo-target/.env`, `frontend/.env` — not this root-level file. | **Documented — blocks GitHub push**, not fixed by QA (outside `backend/`/`demo-target/` write scope; see recommendation) |
| 3 | HIGH (spec-integrity) | `demo-target/guards.py` + `demo-target/app.py` | In `hardened` mode, `apply_guard()` post-processes the **raw model response** — stripping/replacing any verbatim echo of a system-prompt leak marker — *before* returning it over `/chat`. HARNESS's evaluators only ever see the laundered text, never the model's actual output. This is a narrower but functionally equivalent version of the exact shortcut the plan explicitly forbids ("no `if mode==hardened: return PASS` shortcuts... outcome must emerge organically from real model output"). | Documented — recommend removal (see narrative) |
| 4 | MEDIUM | `backend/app/services/scoring_service.py` | `compute_release_decision`'s READY_WITH_CONDITIONS branch checked `severity=="HIGH"` findings with status `ACCEPT_RISK`, but never checked `severity=="CRITICAL"` + `ACCEPT_RISK`. Since CRITICAL+ACCEPT_RISK is also not `OPEN/IN_PROGRESS`, it fell through the NOT_READY branch too — an explicitly-accepted CRITICAL risk could reach an unconditional `READY` with zero trace of it, contradicting `docs/release-readiness.md`'s note that "ACCEPT_RISK is still visible in the rationale trace." | **Fixed + tested** |
| 5 | LOW | `backend/tests/` | Before this review, `test_scoring_service.py`/`test_comparison_service.py` only exercised the pure, DB-free functions. The actual DB-facing wrappers (`score_run`, `decide_release`, and by extension `run_service.execute_run`, `retest_service.retest`, `comparison_service.compare`) had **zero** test coverage — which is exactly where defect #1 was hiding. | Documented — added `tests/test_scoring_db_integration.py` as a first DB-integration test; recommend the Backend Engineer extend this pattern to `run_service`/`retest_service`/`comparison_service`. |
| 6 | LOW | `backend/app/services/comparison_service.py` | `classify()` keys `baseline_by_case`/`retest_by_case` by `test_case_id` via a plain dict — if a run ever produced two `TestResult` rows for the same `(test_run_id, test_case_id)` pair (no DB unique constraint enforces one-per-case), the classification silently keeps whichever row iteration visits last, with no warning. In practice `run_service`/`retest_service` only ever insert one result per case per run, so this isn't currently reachable, but nothing in the schema prevents it. | Documented as a v2 hardening gap (add a unique constraint on `(test_run_id, test_case_id)`, or de-dupe explicitly by `evaluated_at`). |
| — | none found | Evaluator pipeline (`pipeline.py`/`deterministic.py`/`semantic_claude.py`) | Confidence<0.6 fallback fires unconditionally on whichever stage produced the result; severity clamp only ever lowers a FAIL, never raises it; a Claude JSON parse failure degrades to `REVIEW` (never crashes, never silently PASSes) via the two-attempt retry + `_fallback_review`; a non-`ValidationError`/`ValueError` SDK exception also degrades to `REVIEW`, not a crash. Traced this by hand against `docs/release-readiness.md` — matches. | No defect |
| — | none found | Retest exactness | `retest_service.retest()` resends `source.execution_prompt` verbatim (never re-templated from current `test_case` state) and freezes `source.test_case_version` onto the new result — confirmed the case object is only used to look up `category`/`severity_if_failed`/`expected_safe_behavior` for the evaluator, not to rebuild the prompt. | No defect |
| — | none found | Callback signature verification | `core/security.verify_signature` uses `hmac.compare_digest` (genuinely constant-time) and is actually wired into `automation/callback_verifier.py` → `automation_service.handle_callback` → the `/automation/callback` route, checked **before** the duplicate-event lookup. Duplicate `event_id`s correctly no-op via `AutomationEvent`. | No defect |
| — | none found | Secret exposure in API responses | `ApplicationRead`/`ApplicationUpdate` response schema deliberately omits `auth_header_value` (only `ApplicationCreate`/`ApplicationUpdate` *input* schemas carry it) — confirmed it is never echoed back on GET. No raw SQL string interpolation anywhere in `backend/app` (`text("SELECT 1")` is the only raw SQL, both call sites are static, no interpolation) — no SQL injection surface. | No defect |
| — | none found | `run_service.execute_run` error handling | Unreachable endpoint / timeout is caught as `httpx.HTTPError` and persisted as a normal `TestResult(result="ERROR", ...)` row without crashing the run; non-JSON body falls back to `{"raw_text": response.text}`. Whole-run crash (e.g. evaluator import failure) is also caught per-case and persisted as `ERROR`, not propagated. | No defect |

## Primary documented defect (assignment requirement)

### Defect

`backend/app/services/scoring_service.py`'s two DB-facing wrappers, `score_run()` and
`decide_release()`, are the only code path that actually computes `test_runs.assurance_score`
and `release_decisions.decision` in production (via `POST /runs/{run_id}/release-decision/recompute`
and at the end of every `execute_run`/`retest`). Both queried:

```python
select(Finding).where(
    Finding.application_id == application.id,
    Finding.last_seen_run_id == run.id,   # <-- the bug
)
```

`Finding.last_seen_run_id` is only updated by `finding_service.upsert_finding_for_result()`,
which is only called when a test result comes back `FAIL` or `REVIEW` (per its own docstring:
"Auto-resolving on a later PASS is explicitly NOT this module's job"). So the moment a *later*
run — a second baseline re-run of the same suite is a normal, user-triggerable operation via
`POST /runs`, not a hypothetical — happens to not re-fail a test case that has an existing OPEN
finding (flaky/non-deterministic model output, a transient network hiccup that the eval
interprets differently, etc.), that finding's `last_seen_run_id` stays pinned to the *older* run.
Every subsequent call to `score_run`/`decide_release` for the newer run then silently excludes
that finding from both the score and the NOT_READY/READY_WITH_CONDITIONS/READY logic — even
though `finding.status` is still literally `OPEN` in the database and nothing ever resolved it
(only `comparison_service`'s retest **FIXED** path is allowed to do that, per its own docstring).

**Impact**: a real, unresolved CRITICAL finding (e.g. a confirmed system-prompt leak) can be made
to disappear from a release decision — flipping it from the correct `NOT_READY` to
`READY_WITH_CONDITIONS` or even a clean `READY` — with no fix ever having been applied, just by
re-running the assurance suite. This directly undermines the product's core promise
("NOT_READY if any OPEN CRITICAL finding").

### Root cause

Conflating two different concepts that both happen to live on the `Finding` row:
1. `finding.status` — the actual source of truth for "is this still open", maintained by
   `finding_service`/`remediation_service`/`comparison_service`.
2. `finding.last_seen_run_id` — provenance/display metadata about which run most recently
   *reconfirmed* the finding, not a scoping key for "is this finding relevant to run X's
   decision". `docs/release-readiness.md`'s decision rules are written in plain
   application-scoped language ("an OPEN or IN_PROGRESS finding with severity = CRITICAL") with
   no run-scoping — the code introduced run-scoping that the spec never asked for and that
   actively contradicts the spec's own guarantee.

Compounding factor: `score_run`/`decide_release` (the DB-facing wrappers) had **zero** test
coverage before this review — only the pure, DB-free `compute_assurance_score`/
`compute_release_decision` functions were unit-tested, so this bug was invisible to the existing
test suite.

### Fix

Changed both queries in `backend/app/services/scoring_service.py` to scope by `application_id`
and `status` only, dropping the `last_seen_run_id == run.id` filter entirely — i.e. "all
currently OPEN/IN_PROGRESS findings for this application", matching the spec's plain-language
rules and matching the fact that only `comparison_service`'s FIXED path (or an explicit
remediation status change) is allowed to close a finding out of scoring. Added docstrings on
both functions explaining why, referencing this document.

### Retest

Added `backend/tests/test_scoring_db_integration.py` — a real integration test against an
in-memory SQLite engine (via `SQLModel.metadata.create_all`) standing in for Postgres, since the
models use no Postgres-specific dialect types. The test:

1. Creates a workspace/application/suite/CRITICAL test case.
2. Run 1: the case `FAIL`s at CRITICAL → `finding_service.upsert_finding_for_result` creates an
   `OPEN` finding. Confirms `decide_release(run1)` → `NOT_READY` (sanity check).
3. Run 2: a second baseline run against the same case, where this time the result is `PASS`
   (simulating flaky/non-deterministic model output) — the finding is **not** touched, and
   `finding.status` is confirmed still `OPEN` in the DB.
4. Asserts `decide_release(run2)` is still `NOT_READY` and `score_run(run2) < 100.0`.

**Before the fix**: step 4 failed — `decide_release(run2).decision == "READY_WITH_CONDITIONS"`
(actual pytest output: `assert 'READY_WITH_CONDITIONS' == 'NOT_READY'`), confirming the defect.

**After the fix**: full suite run —

```
$ ./.venv/Scripts/python.exe -m pytest tests/ -q
28 passed, 6 warnings in 0.51s
```

— including the new regression test and every pre-existing test (`test_scoring_service.py`,
`test_comparison_service.py`, etc.), confirming the fix resolves the defect without breaking any
previously-verified behavior.

## Finding #2 narrative — committed secret (blocks GitHub push)

`git log --all -- .env.txt` shows the file was added in commit `adde2f6` ("Phase 0: repo
scaffold, docs skeletons") and is still present, unmodified, in the current working tree and
`HEAD`. Its contents are a single line, `ANTHROPIC_API_KEY=sk-ant-api03...` — a real-looking,
non-placeholder Anthropic API key. `.gitignore` was written to exclude `backend/.env`,
`demo-target/.env`, and `frontend/.env` (and their `.env.*` variants) but never accounted for
this root-level `.env.txt`, so it was never caught.

No remote is configured yet (`git remote -v` is empty) and nothing has been pushed to
`https://github.com/DinaMMahfouz/mvp-harness.git`, so this is still fixable without a public
history rewrite. This is squarely inside the plan's own **Pre-push gate**: "secret scan clean —
only then push... and verify a clean clone builds." As committed today, that gate fails.

I did not remove this file myself: it lives at the repo root, outside the `backend/`/
`demo-target/` write scope QA was given for this review, and removing/rewriting git history is a
repo-wide operation the Team Lead should own and verify. **Recommended before any push**:
1. Treat the key as compromised — rotate/revoke it in the Anthropic console regardless of whether
   it's ever left this machine.
2. Delete `.env.txt` from the working tree and add it (and any other stray root-level `.env*`) to
   `.gitignore`.
3. Since history hasn't been pushed anywhere yet, rewrite local history to remove the file from
   every commit that touches it (e.g. `git filter-repo --path .env.txt --invert-paths`) rather
   than just deleting it in a new commit, which would leave the key permanently recoverable from
   `adde2f6` in the repo's history forever.
4. Re-run a secret scan across the full history (not just the working tree) before the final push.

## Finding #3 narrative — demo-target's hardened-mode guard risks masking real signal

`demo-target/app.py`'s `/chat` handler calls the real Anthropic API, then unconditionally passes
the raw completion text through `guards.apply_guard(MODE, raw_text)` before returning it as the
HTTP response body:

```python
raw_text = "".join(block.text for block in completion.content if ...)
guarded_text = apply_guard(MODE, raw_text)
return ChatResponse(response=guarded_text, mode=MODE)
```

In `hardened` mode, `apply_guard` substring-matches a distinctive system-prompt leak marker
against the model's real output and, if found, **rewrites the HTTP response** to cut the leaked
text and replace it with a canned safe refusal. `guards.py`'s own docstring is careful to say this
"is NOT responsible for making the hardened mode pass HARNESS's assurance tests" and frames it as
narrow defense-in-depth — but functionally, this is exactly the failure mode the build plan
explicitly warns against: *"Outcome must emerge organically from running the real evaluator
pipeline against real model output (no `if mode==hardened: return PASS` shortcuts)."* HARNESS's
evaluator never receives the model's actual output when the guard fires — it receives a
synthetically edited version specifically engineered to defeat the one deterministic check
(`SYSTEM_PROMPT_LEAKAGE` marker matching) most likely to catch this exact failure. Whether the
underlying model itself still leaked internally is invisible to HARNESS after this rewrite; the
demo's "hardened mode passes" result is, for this specific failure mode, partly an artifact of
response laundering rather than of the system prompt genuinely working.

I did not remove this code myself, because doing so changes the intended behavior/pass-rate of
the Phase 13 demo rehearsal (vulnerable-vs-hardened organic divergence), which is a call for the
Assurance Engineer / Team Lead, not something QA should silently alter mid-review. **Recommendation**:
remove `apply_guard`'s rewrite behavior entirely and rely solely on the hardened system prompt
(per the docstring's own admission that the guard isn't required to pass) — or, if a
defense-in-depth guard layer is genuinely wanted for production realism, log/flag when it fires
(e.g. an `X-Harness-Guard-Fired: true` response header) so HARNESS's evaluator — or a human
reviewer — can see that the safety net, not the model, caught this case, rather than have it
silently vanish from what the evaluator ever gets to inspect.

## Release-readiness verdict

**I would NOT block HARNESS MVP release readiness on defect #1** — it was found, root-caused,
fixed, and retested during this review, and the fix is minimal, well-tested, and verified not to
regress any of the 27 pre-existing tests.

**I WOULD block the final `git push` to `https://github.com/DinaMMahfouz/mvp-harness.git`** on
finding #2 (the committed Anthropic API key) — this is exactly what the plan's own pre-push gate
("secret scan clean") exists to catch, and pushing today would put a real credential in a public
GitHub history. This should be treated as a hard stop until the key is rotated and the file is
purged from history, not merely deleted going forward.

Finding #3 (demo-target guard) does not affect the correctness of the HARNESS *product* itself
(the guard lives entirely inside the standalone demo-target fixture, not in any code path a real
registered application would go through), but it does undermine the credibility of the Phase 13
demo rehearsal's "organic divergence" claim and should be resolved or explicitly re-justified
before that phase is signed off as passed.
