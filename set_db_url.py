"""Write the Supabase pooler connection string into backend/.env.

    python set_db_url.py

Run it from anywhere — it resolves backend/.env relative to this file, not to
your shell's current directory, which is what broke the earlier attempt.

It prompts for the database password (hidden, never echoed, never stored
anywhere but the .env file), URL-encodes it, and replaces ONLY the
DATABASE_URL line. Every other line in .env is left untouched.
"""
from __future__ import annotations

import getpass
import re
import shutil
import sys
import urllib.parse
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent / "backend" / ".env"

PROJECT_REF = "adzaoqmdapyvtxeayrlt"
POOLER_HOST = "aws-0-eu-central-1.pooler.supabase.com"
POOLER_PORT = 6543
DB_NAME = "postgres"


def main() -> None:
    if not ENV_FILE.exists():
        sys.exit(f"Not found: {ENV_FILE}\nRun this script from inside the harness-mvp folder.")

    print(f"Editing: {ENV_FILE}")
    print(f"Host   : {POOLER_HOST}:{POOLER_PORT}")
    print(f"User   : postgres.{PROJECT_REF}")
    print()
    print("Enter your Supabase DATABASE password (not any API key, not the")
    print("publishable key). Supabase dashboard -> Settings -> Database ->")
    print("'Reset database password' if you don't have it. Input is hidden.")
    print()

    password = getpass.getpass("Database password: ")
    if not password:
        sys.exit("No password entered — nothing changed.")

    # Supabase generates passwords containing @ # / ? and similar, all of which
    # are structural characters in a URL. Unencoded, an '@' makes psycopg parse
    # the wrong host and report a confusing DNS error instead of an auth error.
    encoded = urllib.parse.quote(password, safe="")

    new_line = (
        f"DATABASE_URL=postgresql://postgres.{PROJECT_REF}:{encoded}"
        f"@{POOLER_HOST}:{POOLER_PORT}/{DB_NAME}"
    )

    # utf-8-sig: the existing file has a BOM; this reads it and writes it back
    # without turning the BOM into stray characters on the first line.
    original = ENV_FILE.read_text(encoding="utf-8-sig")

    backup = ENV_FILE.with_suffix(".env.bak")
    shutil.copy2(ENV_FILE, backup)

    lines = original.splitlines()
    replaced = False
    for i, line in enumerate(lines):
        if line.strip().startswith("DATABASE_URL="):
            lines[i] = new_line
            replaced = True
            break
    if not replaced:
        lines.insert(0, new_line)

    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")

    masked = re.sub(r":([^:@]+)@", ":****@", new_line)
    print()
    print("Written. DATABASE_URL is now:")
    print(f"  {masked}")
    print(f"(backup of the previous file: {backup.name})")
    print()
    print("Next:  python run.py")


if __name__ == "__main__":
    main()
