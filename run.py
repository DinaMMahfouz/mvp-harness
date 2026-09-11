"""HARNESS — single entrypoint. Starts the whole stack with one command.

    python run.py                 start everything (backend, both targets, frontend)
    python run.py --seed          ...then drive the full assurance loop end-to-end
    python run.py --no-frontend   backend + demo targets only
    python run.py --only-backend  backend only

Ctrl+C once shuts everything down cleanly.

Why a launcher instead of four terminals: the two demo targets are the same
app distinguished ONLY by the MODE environment variable, and MODE is read once
at import time into a module-level constant in demo-target/config.py. Setting it
by hand in the wrong shell — or letting demo-target/.env's MODE=vulnerable win —
silently gives you two identical targets and a meaningless NOT_READY -> READY
demo. Here each child process gets MODE injected explicitly, and startup is
blocked until each target confirms over HTTP that it is running the mode its
port claims.
"""
from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
DEMO = ROOT / "demo-target"
FRONTEND = ROOT / "frontend"

IS_WINDOWS = os.name == "nt"
VENV_PY = BACKEND / ".venv" / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")

BACKEND_PORT = 8000
VULNERABLE_PORT = 8001
HARDENED_PORT = 8002
FRONTEND_PORT = 5173

# ANSI colors; harmless if the terminal ignores them.
COLORS = {
    "backend": "\033[36m",
    "vulnerable": "\033[33m",
    "hardened": "\033[32m",
    "frontend": "\033[35m",
    "run.py": "\033[1m",
}
RESET = "\033[0m"

_procs: list[tuple[str, subprocess.Popen]] = []
_shutting_down = threading.Event()


def log(label: str, message: str) -> None:
    color = COLORS.get(label, "")
    print(f"{color}[{label:<10}]{RESET} {message}", flush=True)


def die(message: str) -> None:
    log("run.py", f"FAILED: {message}")
    shutdown()
    sys.exit(1)


# --------------------------------------------------------------------------
# Preflight
# --------------------------------------------------------------------------

def preflight(want_frontend: bool, want_targets: bool) -> None:
    if not VENV_PY.exists():
        die(
            f"no virtualenv at {VENV_PY}.\n"
            f"    cd backend && python -m venv .venv && "
            f".venv\\Scripts\\Activate.ps1 && pip install -r requirements.txt"
        )
    if not (BACKEND / ".env").exists():
        die(
            "backend/.env is missing. Copy backend/.env.example to backend/.env and "
            "fill in DATABASE_URL (the Supabase TRANSACTION POOLER string, not the "
            "direct db.<ref>.supabase.co host) and ANTHROPIC_API_KEY."
        )
    if want_targets and not (DEMO / ".env").exists():
        die("demo-target/.env is missing. Copy demo-target/.env.example and set ANTHROPIC_API_KEY.")
    if want_frontend:
        if shutil.which("npm") is None:
            die("npm is not on PATH. Install Node.js, or run with --no-frontend.")
        if not (FRONTEND / "node_modules").exists():
            die("frontend/node_modules is missing. Run: cd frontend && npm install")


# --------------------------------------------------------------------------
# Process management
# --------------------------------------------------------------------------

def _pump(label: str, stream) -> None:
    """Forward a child's output with a label, so four services share one terminal."""
    for raw in iter(stream.readline, ""):
        if _shutting_down.is_set():
            break
        line = raw.rstrip()
        if line:
            log(label, line)
    try:
        stream.close()
    except Exception:
        pass


def spawn(label: str, cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    child_env = {**os.environ, **(env or {})}
    # Unbuffered, so uvicorn logs appear immediately instead of in 4KB bursts.
    child_env["PYTHONUNBUFFERED"] = "1"
    log("run.py", f"starting {label}: {' '.join(cmd)}")
    kwargs: dict = {}
    if IS_WINDOWS:
        # Own process group, so our Ctrl-C handler shuts children down in order
        # rather than the console blasting SIGINT at everything simultaneously.
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        env=child_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        **kwargs,
    )
    _procs.append((label, proc))
    threading.Thread(target=_pump, args=(label, proc.stdout), daemon=True).start()


def shutdown() -> None:
    if _shutting_down.is_set():
        return
    _shutting_down.set()
    print()
    log("run.py", "shutting down...")
    for label, proc in reversed(_procs):
        if proc.poll() is not None:
            continue
        log("run.py", f"stopping {label} (pid {proc.pid})")
        try:
            proc.terminate()
        except Exception:
            pass
    deadline = time.monotonic() + 10
    for _, proc in _procs:
        remaining = max(0.0, deadline - time.monotonic())
        try:
            proc.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except Exception:
                pass
    log("run.py", "all services stopped.")


# --------------------------------------------------------------------------
# Health waiting
# --------------------------------------------------------------------------

def _get_json(url: str, timeout: float = 3.0):
    import json

    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def wait_for(label: str, url: str, timeout_s: int = 90):
    """Poll until the service answers, or the child dies, or we time out."""
    deadline = time.monotonic() + timeout_s
    last_error = ""
    while time.monotonic() < deadline:
        for name, proc in _procs:
            if name == label and proc.poll() is not None:
                die(f"{label} exited with code {proc.returncode} before becoming healthy. See its output above.")
        try:
            # 127.0.0.1, not localhost: on Windows localhost often resolves to
            # ::1 first, and uvicorn's default bind is IPv4-only.
            status, body = _get_json(url)
            return status, body
        except urllib.error.HTTPError as exc:
            try:
                import json

                return exc.code, json.loads(exc.read().decode("utf-8"))
            except Exception:
                last_error = f"HTTP {exc.code}"
        except Exception as exc:
            last_error = str(exc)
        time.sleep(0.5)
    die(f"{label} did not become healthy within {timeout_s}s at {url} (last error: {last_error})")


def wait_for_port(label: str, port: int, timeout_s: int = 120) -> None:
    """For the frontend, which serves HTML rather than a JSON health route."""
    import socket

    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        for name, proc in _procs:
            if name == label and proc.poll() is not None:
                die(f"{label} exited with code {proc.returncode}. See its output above.")
        with socket.socket() as s:
            s.settimeout(1.0)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.5)
    die(f"{label} did not open port {port} within {timeout_s}s")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Start the HARNESS stack.")
    parser.add_argument("--no-frontend", action="store_true", help="skip the Vite dev server")
    parser.add_argument("--only-backend", action="store_true", help="backend only, no demo targets or UI")
    parser.add_argument("--seed", action="store_true", help="after startup, run scripts/seed_demo.py")
    parser.add_argument("--reload", action="store_true", help="run the backend with --reload")
    args = parser.parse_args()

    want_targets = not args.only_backend
    want_frontend = not (args.no_frontend or args.only_backend)

    preflight(want_frontend, want_targets)

    def on_sigint(signum, frame):
        shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, on_sigint)

    try:
        backend_cmd = [
            str(VENV_PY), "-m", "uvicorn", "app.main:app",
            "--host", "127.0.0.1", "--port", str(BACKEND_PORT),
        ]
        if args.reload:
            backend_cmd.append("--reload")
        spawn("backend", backend_cmd, BACKEND)

        status, body = wait_for("backend", f"http://127.0.0.1:{BACKEND_PORT}/health")
        if body.get("database") != "connected":
            die(
                f"backend is up but its database is unreachable ({body}).\n"
                "    Fix DATABASE_URL in backend/.env — it must be the Supabase "
                "TRANSACTION POOLER connection string (aws-0-*.pooler.supabase.com:6543), "
                "not the direct db.<ref>.supabase.co host, which is IPv6-only."
            )
        log("run.py", f"backend healthy on :{BACKEND_PORT} (database connected)")

        if want_targets:
            for label, port in (("vulnerable", VULNERABLE_PORT), ("hardened", HARDENED_PORT)):
                spawn(
                    label,
                    [str(VENV_PY), "-m", "uvicorn", "app:app",
                     "--host", "127.0.0.1", "--port", str(port)],
                    DEMO,
                    # MODE is injected explicitly. demo-target/config.py calls
                    # load_dotenv(), which does NOT override a real environment
                    # variable, so this reliably beats demo-target/.env's
                    # MODE=vulnerable for the hardened instance.
                    env={"MODE": label, "PORT": str(port)},
                )
            for label, port in (("vulnerable", VULNERABLE_PORT), ("hardened", HARDENED_PORT)):
                _, body = wait_for(label, f"http://127.0.0.1:{port}/health")
                reported = body.get("mode")
                if reported != label:
                    die(
                        f"{label} target on :{port} reports mode={reported!r}. "
                        "Both targets running the same system prompt makes the "
                        "NOT_READY -> READY demo prove nothing."
                    )
                log("run.py", f"{label} target healthy on :{port} (mode={reported})")

        if want_frontend:
            npm = shutil.which("npm")
            spawn("frontend", [npm, "run", "dev"], FRONTEND)
            wait_for_port("frontend", FRONTEND_PORT)
            log("run.py", f"frontend healthy on :{FRONTEND_PORT}")

        print()
        log("run.py", "=" * 58)
        log("run.py", f"  API      http://localhost:{BACKEND_PORT}       docs at /docs")
        if want_targets:
            log("run.py", f"  target   http://localhost:{VULNERABLE_PORT}       mode=vulnerable")
            log("run.py", f"  target   http://localhost:{HARDENED_PORT}       mode=hardened")
        if want_frontend:
            log("run.py", f"  UI       http://localhost:{FRONTEND_PORT}")
        log("run.py", "  Ctrl+C to stop everything")
        log("run.py", "=" * 58)
        print()

        if args.seed:
            seed = BACKEND / "scripts" / "seed_demo.py"
            if not seed.exists():
                die(f"{seed} not found")
            log("run.py", "running the full assurance loop (real API calls, several minutes)...")
            rc = subprocess.call([str(VENV_PY), str(seed)], cwd=str(BACKEND))
            if rc != 0:
                log("run.py", f"seed_demo.py exited with code {rc}")
            else:
                log("run.py", "seed complete — services still running, Ctrl+C to stop")

        # Idle until Ctrl+C, or until a child dies unexpectedly.
        while True:
            time.sleep(1)
            for label, proc in _procs:
                if proc.poll() is not None:
                    log("run.py", f"{label} exited unexpectedly (code {proc.returncode}) — shutting down")
                    shutdown()
                    sys.exit(1)
    except KeyboardInterrupt:
        shutdown()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - never leave orphaned children behind
        log("run.py", f"unexpected error: {type(exc).__name__}: {exc}")
        shutdown()
        raise


if __name__ == "__main__":
    main()
