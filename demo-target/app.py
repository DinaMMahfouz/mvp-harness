"""HARNESS demo-target: a small FastAPI + Claude chatbot with two real
behavior modes (vulnerable / hardened), controlled by the MODE env var.

Both modes issue the same real Anthropic API call over the same /chat HTTP
contract. The only difference is which system prompt is loaded (see
config.get_system_prompt) and, in hardened mode, a light post-response guard
(see guards.apply_guard). There is no mode-based shortcut that fabricates the
outcome — HARNESS's own evaluators are expected to produce a real pass/fail
divergence by actually calling this API and inspecting real model output.
"""

import anthropic
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from config import ANTHROPIC_API_KEY, MODE, PORT, get_system_prompt
from guards import apply_guard

MODEL_ID = "claude-sonnet-4-5"

app = FastAPI(title="HARNESS Demo Target", version="1.0.0")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    mode: str


@app.get("/")
def root() -> dict:
    """Liveness/identity route.

    Exists so that hitting the base URL in a browser identifies the service
    and its active mode instead of returning a bare 404. Deliberately exposes
    nothing beyond what /health already does.
    """
    return {"service": "harness-demo-target", "status": "running", "mode": MODE}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "mode": MODE}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=422, detail="message must not be empty")

    if not ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY is not configured on this server",
        )

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    try:
        completion = client.messages.create(
            model=MODEL_ID,
            max_tokens=1024,
            system=get_system_prompt(),
            messages=[{"role": "user", "content": request.message}],
        )
    except anthropic.APIError as exc:
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {exc}") from exc

    raw_text = "".join(
        block.text for block in completion.content if getattr(block, "type", None) == "text"
    )

    guarded_text = apply_guard(MODE, raw_text)

    return ChatResponse(response=guarded_text, mode=MODE)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
