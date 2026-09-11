"""Configuration for the HARNESS demo-target chatbot.

Reads environment variables (optionally from a local .env file) and exposes
helpers for loading the correct system prompt based on the active MODE.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load variables from a .env file if present (does not override real env vars
# that are already set, e.g. in a deployed container).
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"

MODE = os.environ.get("MODE", "vulnerable").strip().lower()
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
PORT = int(os.environ.get("PORT", "8001"))

VALID_MODES = {"vulnerable", "hardened"}

_PROMPT_FILENAMES = {
    "vulnerable": "vulnerable_system_prompt.txt",
    "hardened": "hardened_system_prompt.txt",
}


def get_system_prompt(mode: str | None = None) -> str:
    """Load the system prompt text file that corresponds to the given mode.

    Defaults to the globally configured MODE. Falls back to "vulnerable" if
    an unrecognized mode value is supplied, since that is the naive/default
    behavior of this demo target.
    """
    effective_mode = (mode or MODE).strip().lower()
    if effective_mode not in VALID_MODES:
        effective_mode = "vulnerable"

    prompt_path = PROMPTS_DIR / _PROMPT_FILENAMES[effective_mode]
    return prompt_path.read_text(encoding="utf-8")
