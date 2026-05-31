#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

OUTPUT="config/web_content.json"
TMP_OUTPUT="$(mktemp)"
trap 'rm -f "$TMP_OUTPUT"' EXIT
mkdir -p "$(dirname "$OUTPUT")"

python3 - <<'PY' > "$TMP_OUTPUT"
import json
import pathlib
import re
import subprocess
from datetime import date

root = pathlib.Path(".")
reports_config_path = root / "config" / "reports.json"
prompts_config_path = root / "config" / "prompts.json"

with reports_config_path.open(encoding="utf-8") as fp:
    reports_config = json.load(fp)

with prompts_config_path.open(encoding="utf-8") as fp:
    prompts_config = json.load(fp)

content = []


def run_git(args):
    try:
        result = subprocess.run(
            ["git", *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""
    return result.stdout.strip()


def last_updated(path_value):
    path = root / path_value
    if run_git(["status", "--porcelain", "--", path_value]):
        return date.today().isoformat()

    updated = run_git(["log", "-1", "--format=%cs", "--", path_value])
    if updated:
        return updated

    if path.exists():
        return date.fromtimestamp(path.stat().st_mtime).isoformat()

    return ""

for index, report in enumerate(reports_config.get("reports", []), start=1):
    path = report.get("output_md")
    if not path or not (root / path).exists():
        continue

    content.append(
        {
            "section": "reports",
            "order": index,
            "id": report.get("id") or pathlib.Path(path).stem,
            "title": report.get("title") or pathlib.Path(path).stem,
            "path": path,
            "summary": report.get("abstract", ""),
            "last_updated": last_updated(path),
            "authors": report.get("authors", []),
            "themes": report.get("themes", []),
            "keywords": report.get("keywords", []),
        }
    )

def title_from_markdown(path: pathlib.Path):
    text = path.read_text(encoding="utf-8")
    title_match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    return title_match.group(1).strip() if title_match else path.stem


for index, prompt in enumerate(prompts_config.get("prompts", []), start=1):
    path_value = prompt.get("path")
    if not path_value:
        continue
    path = root / path_value
    if not path.exists():
        continue

    title = prompt.get("title") or title_from_markdown(path)
    purpose = prompt.get("purpose", "")
    content.append(
        {
            "section": "prompts",
            "order": prompt.get("order") or index,
            "id": prompt.get("id") or path.stem,
            "title": title,
            "path": path_value,
            "summary": purpose,
            "purpose": purpose,
            "last_updated": last_updated(path_value),
            "authors": [],
            "themes": ["プロンプト"],
            "keywords": [],
        }
    )

manifest = {
    "schema": "aice.web_content.v1",
    "project": reports_config.get("project", {}),
    "source_roots": ["reports", "prompts"],
    "content": content,
}

print(json.dumps(manifest, ensure_ascii=False, indent=2))
PY

mv "$TMP_OUTPUT" "$OUTPUT"
chmod 0644 "$OUTPUT"
