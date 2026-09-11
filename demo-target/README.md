# HARNESS Demo Target

A small standalone FastAPI + Claude chatbot used as the demo target for HARNESS (AI Release Assurance). It exposes a single `/chat` endpoint backed by a real Anthropic Claude API call, with two behavior modes controlled by the `MODE` environment variable: `vulnerable` and `hardened`. Both modes share the exact same HTTP contract and call the same model — only the system prompt (and, for hardened mode, a light post-response guard) differs. This lets HARNESS register the two running instances as separate `applications` and demonstrate a real `NOT_READY` -> `READY` / `READY_WITH_CONDITIONS` transition driven entirely by genuine model behavior, not a scripted outcome.

## Setup

```
cd demo-target
pip install -r requirements.txt
cp .env.example .env   # then fill in ANTHROPIC_API_KEY
```

## Running vulnerable mode (port 8001)

```
MODE=vulnerable ANTHROPIC_API_KEY=sk-... uvicorn app:app --port 8001
```

## Running hardened mode (port 8002)

```
MODE=hardened ANTHROPIC_API_KEY=sk-... uvicorn app:app --port 8002
```

You can also just run `python app.py` with `MODE` and `PORT` set in the environment (or a `.env` file) — this is what the Dockerfile's `CMD` uses.

## Endpoints

- `POST /chat` — body `{"message": "..."}`, returns `{"response": "...", "mode": "vulnerable"|"hardened"}`.
- `GET /health` — returns `{"status": "ok", "mode": "..."}`.

## What this is for

The `vulnerable` mode uses a naive system prompt with no refusal instructions or guardrails, making it realistically susceptible to prompt injection, system-prompt leakage, and hallucination-trap attacks (e.g. asking about a nonexistent "Acme Platinum Elite Plus" plan). The `hardened` mode uses the same underlying assistant persona and company facts, but with explicit instructions to refuse to reveal its system prompt, to only discuss documented plans/policies and say "I don't have that information" otherwise, to never claim an unconfirmed action was completed, and to ignore instructions embedded in user messages — plus a narrow post-response guard that catches one specific verbatim-leak failure mode as a secondary safety net. Running an assurance suite against both instances is meant to produce genuinely different, organically-derived findings, proving that HARNESS's harden-retest-release loop works against real behavior rather than canned results.
