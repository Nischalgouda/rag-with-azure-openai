"""Admin tool: create an API key for someone.

    python -m scripts.create_key alice

Prints the raw key ONCE. It is not stored anywhere (only its hash is), so copy it now.
Boilerplate - nothing for you to do here; it starts working when create_key() does.
"""
import sys

from app import auth

if len(sys.argv) != 2:
    sys.exit("usage: python -m scripts.create_key <name>")

raw = auth.create_key(sys.argv[1])
print(f"Key for {sys.argv[1]!r} (shown once, store it safely):\n{raw}")
