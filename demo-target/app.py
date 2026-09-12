"""HARNESS demo-target: a small FastAPI + Claude chatbot with two real
behavior modes (vulnerable / hardened).

Both modes issue the same real Anthropic API call over the same /chat HTTP
contract. The only difference is which system prompt is loaded (see
config.get_system_prompt) and, in hardened mode, a light post-response guard
(see guards.apply_guard). There is no mode-based shortcut that fabricates the
outcome - HARNESS's own evaluators are expected to produce a real pass/fail
divergence by actually calling this API and inspecting real model output.

MODE SELECTION
--------------
Mode comes from the request body when present, and falls back to the MODE
environment variable otherwise.

Locally, two processes on two ports with different MODE values is the natural
setup. That does not survive deployment: on a serverless host a service is
built once from one root, so running the same code twice under two different
env values would mean two separately-configured deployments of one folder.
Accepting mode per request instead lets ONE deployed instance back both
registered applications, which HARNESS distinguishes by request_template:

    vulnerable  {"message": "{{prompt}}", "mode": "vulnerable"}
    hardened    {"message": "{{prompt}}", "mode": "hardened"}

This does not weaken the demo. Each request still loads the corresponding real
system prompt and calls the real model; the divergence between the two
applications is still produced by model behavior, not by branching on a flag
to fake a result.
"""

import anthropic
from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel

from config import ANTHROPIC_API_KEY, MODE, PORT, VALID_MODES, get_system_prompt
from guards import apply_guard

MODEL_ID = "claude-sonnet-4-5"

app = FastAPI(title="HARNESS Demo Target", version="1.1.0")

# Routes are defined on a router and mounted at BOTH "" and "/demo" so the
# service works whether or not the platform's rewrite strips a path prefix
# before the request reaches this app. Locally, "/chat" is unchanged.
router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    mode: str | None = None


class ChatResponse(BaseModel):
    response: str
    mode: str


def _resolve_mode(requested: str | None) -> str:
    """Per-request mode, falling back to the process-wide MODE env var.

    An unrecognized value falls back to 'vulnerable' rather than erroring:
    that is this demo target's naive default, and silently hardening on a
    typo would make an assurance run look better than the app really is -
    the exact failure direction this whole project exists to catch.
    """
    candidate = (requested or MODE or "vulnerable").strip().lower()
    return candidate if candidate in VALID_MODES else "vulnerable"


@router.get("/")
def root() -> dict:
    """Liveness/identity route. Exposes nothing beyond /health."""
    return {"service": "harness-demo-target", "status": "running", "default_mode": MODE}


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "mode": MODE, "modes_supported": sorted(VALID_MODES)}


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=422, detail="message must not be empty")

    if not ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY is not configured on this server",
        )

    effective_mode = _resolve_mode(request.mode)
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    try:
        completion = client.messages.create(
            model=MODEL_ID,
            max_tokens=1024,
            system=get_system_prompt(effective_mode),
            messages=[{"role": "user", "content": request.message}],
        )
    except anthropic.APIError as exc:
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {exc}") from exc

    raw_text = "".join(
        block.text for block in completion.content if getattr(block, "type", None) == "text"
    )

    guarded_text = apply_guard(effective_mode, raw_text)

    return ChatResponse(response=guarded_text, mode=effective_mode)


app.include_router(router)
app.include_router(router, prefix="/demo")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
