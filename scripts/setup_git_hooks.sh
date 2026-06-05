#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

git -C "$ROOT" config core.hooksPath .githooks
python3 "$ROOT/scripts/build_ai_package.py"
"$ROOT/scripts/update_web_manifest.sh"
"$ROOT/scripts/update_notebooklm_source.sh"
