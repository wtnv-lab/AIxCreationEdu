#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

OUTPUT="notebooklm-source.txt"

python3 - <<'PY'
import importlib.util
import sys

if importlib.util.find_spec("files_to_prompt") is None:
    sys.stderr.write(
        "files-to-prompt is not installed.\n"
        "Install it with: python3 -m pip install --user -r requirements-ai.txt\n"
    )
    sys.exit(1)
PY

python3 -m files_to_prompt . \
  --include-hidden \
  --markdown \
  --ignore ".git" \
  --ignore ".DS_Store" \
  --ignore "__pycache__" \
  --ignore "*.pyc" \
  --ignore "notebooklm-source.txt" \
  --ignore "*.jpg" \
  --ignore "*.jpeg" \
  --ignore "*.png" \
  --ignore "*.gif" \
  --ignore "*.webp" \
  --ignore "*.mp4" \
  --ignore "*.mov" \
  --ignore "*.pdf" \
  --output "$OUTPUT"
