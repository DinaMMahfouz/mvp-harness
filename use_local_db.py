"""Switch backend/.env between the local SQLite database and Supabase.

    python use_local_db.py sqlite      use the local file database (no network)
    python use_local_db.py supabase    switch back to the Supabase pooler
    python use_local_db.py             show which one is active

Run from anywhere: paths resolve relative to this file, not your shell's
current directory.

Why this exists: Supabase's transaction pooler listens on port 6543 (session
mode: 5432). Corporate networks commonly allow only 443/80 outbound, so the
connection times out no matter how correct the credentials are - the packets
never leave. SQLite needs no network, so the whole app runs offline.

The inactive URL is preserved in the file as DATABASE_URL_ALT, so switching
back does not require re-entering the database password.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent / "backend" / ".env"
SQLITE_URL = "sqlite:///./harness_local.db"


def mask(url: str) -> str:
    return re.sub(r"://([^:]+):[^@]*@", r"://\1:****@", url)


def read_lines() -> list[str]:
    if not ENV_FILE.exists():
        sys.exit(f"Not found: {ENV_FILE}")
    return ENV_FILE.read_text(encoding="utf-8-sig").splitlines()


def find(lines: list[str], key: str) -> tuple[int, str] | None:
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{key}="):
            return i, line.strip().split("=", 1)[1]
    return None


def write(lines: list[str]) -> None:
    shutil.copy2(ENV_FILE, ENV_FILE.with_suffix(".env.bak"))
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    lines = read_lines()
    current = find(lines, "DATABASE_URL")
    if current is None:
        sys.exit("No DATABASE_URL line in backend/.env")
    cur_idx, cur_url = current
    alt = find(lines, "DATABASE_URL_ALT")

    mode = sys.argv[1].lower() if len(sys.argv) > 1 else None

    if mode is None:
        backend = "SQLite (local file)" if cur_url.startswith("sqlite") else "Postgres / Supabase"
        print(f"Active : {backend}")
        print(f"         {mask(cur_url)}")
        if alt:
            print(f"Standby: {mask(alt[1])}")
        print("\nUsage: python use_local_db.py [sqlite|supabase]")
        return

    if mode not in ("sqlite", "supabase"):
        sys.exit("Argument must be 'sqlite' or 'supabase'.")

    want_sqlite = mode == "sqlite"
    already = cur_url.startswith("sqlite")
    if want_sqlite == already:
        print(f"Already using {mode}: {mask(cur_url)}")
        return

    if want_sqlite:
        new_active, new_alt = SQLITE_URL, cur_url
    else:
        if not alt or alt[1].startswith("sqlite"):
            sys.exit(
                "No saved Supabase URL to switch back to.\n"
                "Run: python set_db_url.py"
            )
        new_active, new_alt = alt[1], cur_url

    lines[cur_idx] = f"DATABASE_URL={new_active}"
    alt_line = f"DATABASE_URL_ALT={new_alt}"
    if alt:
        lines[alt[0]] = alt_line
    else:
        lines.insert(cur_idx + 1, alt_line)

    write(lines)
    print(f"Switched to {mode}.")
    print(f"  active : {mask(new_active)}")
    print(f"  standby: {mask(new_alt)}")
    print("\nNext:  python run.py")


if __name__ == "__main__":
    main()
