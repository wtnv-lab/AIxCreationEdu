#!/usr/bin/env python3
"""Validate repository structure and AI-facing metadata consistency."""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_LICENSE_STATUSES = {
    "cc_by_4_0",
    "needs_rights_review",
    "permission_granted",
    "external_citation_only",
}

errors: list[str] = []
warnings: list[str] = []


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def error(message: str) -> None:
    errors.append(message)


def warn(message: str) -> None:
    warnings.append(message)


def load_json(path: str) -> Any:
    with (ROOT / path).open(encoding="utf-8") as fp:
        return json.load(fp)


def load_jsonl(path: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    file_path = ROOT / path
    with file_path.open(encoding="utf-8") as fp:
        for line_number, line in enumerate(fp, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                error(f"{path}:{line_number}: invalid JSONL: {exc}")
                continue
            if not isinstance(row, dict):
                error(f"{path}:{line_number}: JSONL row must be an object")
                continue
            rows.append(row)
    return rows


def validate_json_files() -> None:
    for path in sorted(ROOT.rglob("*.json")):
        if ".git" in path.parts:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            error(f"{rel(path)}: invalid JSON: {exc}")


def validate_existing_paths(
    reports: list[dict[str, Any]],
    prompts: list[dict[str, Any]],
    figures: list[dict[str, Any]],
) -> None:
    for report in reports:
        path = report.get("output_md")
        if not path or not (ROOT / path).is_file():
            error(f"Report {report.get('id', '<unknown>')} points to missing output_md: {path}")

    for prompt in prompts:
        path = prompt.get("path")
        if not path or not (ROOT / path).is_file():
            error(f"Prompt {prompt.get('id', '<unknown>')} points to missing path: {path}")

    for figure in figures:
        path = figure.get("path")
        if not path or not (ROOT / path).is_file():
            error(f"Figure {figure.get('id', '<unknown>')} points to missing path: {path}")


def validate_markdown_links() -> None:
    link_pattern = re.compile(r"!\[[^\]]*]\(([^)]+)\)|(?<!!)\[[^\]]+]\(([^)]+)\)")
    for path in sorted(ROOT.rglob("*.md")):
        if ".git" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for match in link_pattern.finditer(text):
            href = (match.group(1) or match.group(2)).strip().strip("<>")
            if re.match(r"^(https?:|mailto:|tel:|#)", href):
                continue
            href = href.split("#", 1)[0].split("?", 1)[0]
            if not href:
                continue
            target = (path.parent / urllib.parse.unquote(href)).resolve()
            try:
                target.relative_to(ROOT)
            except ValueError:
                continue
            if not target.exists():
                error(f"{rel(path)} links to missing local target: {href}")


def unique_values(items: list[dict[str, Any]], key: str, label: str) -> None:
    seen: set[str] = set()
    for item in items:
        value = str(item.get(key, "")).strip()
        if not value:
            error(f"{label} entry is missing {key}")
            continue
        if value in seen:
            error(f"Duplicate {label} {key}: {value}")
        seen.add(value)


def validate_figures(figures: list[dict[str, Any]]) -> None:
    unique_values(figures, "id", "figure")
    required = ["id", "report_id", "path", "alt", "caption", "source", "license_note", "license_status", "reuse_policy"]
    for figure in figures:
        figure_id = figure.get("id", "<unknown>")
        for key in required:
            if not str(figure.get(key, "")).strip():
                error(f"Figure {figure_id} is missing {key}")
        status = figure.get("license_status")
        if status not in ALLOWED_LICENSE_STATUSES:
            error(f"Figure {figure_id} has unknown license_status: {status}")
        if status == "needs_rights_review":
            warn(f"Figure {figure_id} still needs rights review before secondary reuse")


def validate_report_indexes(reports_config: dict[str, Any], metadata_reports: list[dict[str, Any]]) -> None:
    reports = reports_config.get("reports", [])
    config_ids = [report.get("id") for report in reports]
    metadata_ids = [report.get("id") for report in metadata_reports]
    if config_ids != metadata_ids:
        error("metadata/reports.json report order or IDs differ from config/reports.json")
    if reports != metadata_reports:
        error("metadata/reports.json is not synchronized with config/reports.json reports")


def validate_concept_alignment(reports: list[dict[str, Any]], schema: dict[str, Any]) -> None:
    process_ids = {item["id"] for item in schema.get("process_stages", [])}
    literacy_ids = {item["id"] for item in schema.get("literacies", [])}
    ai_role_ids = {item["id"] for item in schema.get("ai_roles", [])}
    responsibility_ids = {item["id"] for item in schema.get("human_responsibilities", [])}
    domain_tags = set(schema.get("domain_tags", []))

    for report in reports:
        report_id = report.get("id", "<unknown>")
        alignment = report.get("concept_alignment") or {}
        for key in ["primary_stage_ids", "supporting_stage_ids"]:
            for value in alignment.get(key, []):
                if value not in process_ids:
                    error(f"{report_id}: unknown {key} value: {value}")
        for value in alignment.get("literacy_ids", []):
            if value not in literacy_ids:
                error(f"{report_id}: unknown literacy_ids value: {value}")
        for value in alignment.get("ai_role_ids", []):
            if value not in ai_role_ids:
                error(f"{report_id}: unknown ai_role_ids value: {value}")
        for value in alignment.get("human_responsibility_ids", []):
            if value not in responsibility_ids:
                error(f"{report_id}: unknown human_responsibility_ids value: {value}")
        for value in alignment.get("domain_tags", []):
            if value not in domain_tags:
                error(f"{report_id}: unknown domain_tags value: {value}")


def validate_chunks(path: str, report_ids: set[str]) -> None:
    required = ["id", "report_id", "title", "section", "text"]
    for row in load_jsonl(path):
        chunk_id = row.get("id", "<unknown>")
        for key in required:
            if not str(row.get(key, "")).strip():
                error(f"{path}: chunk {chunk_id} is missing {key}")
        if row.get("report_id") not in report_ids:
            error(f"{path}: chunk {chunk_id} has unknown report_id: {row.get('report_id')}")
        source = row.get("source") or row.get("source_md")
        if not source:
            error(f"{path}: chunk {chunk_id} is missing source/source_md")
        elif not (ROOT / source).exists():
            error(f"{path}: chunk {chunk_id} points to missing source: {source}")


def validate_ai_package(reports: list[dict[str, Any]]) -> None:
    manifest = load_json("ai/manifest.json")
    manifest_ids = [report.get("id") for report in manifest.get("reports", [])]
    report_ids = [report.get("id") for report in reports]
    if manifest_ids != report_ids:
        error("ai/manifest.json report IDs differ from config/reports.json")

    for report in reports:
        report_id = report["id"]
        sidecar_path = ROOT / "metadata" / "report-sidecars" / f"{report_id}.json"
        if not sidecar_path.is_file():
            error(f"Missing sidecar for report: {report_id}")
            continue
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        if sidecar.get("source_md") != report.get("output_md"):
            error(f"Sidecar {rel(sidecar_path)} has stale source_md")
        for figure in sidecar.get("figures", []):
            if not figure.get("license_status") or not figure.get("reuse_policy"):
                error(f"Sidecar {rel(sidecar_path)} figure {figure.get('id')} lacks reuse metadata")

    source_text = (ROOT / "ai" / "notebooklm-source.txt").read_text(encoding="utf-8")
    web_prefix = (ROOT / "web" / "app.js").read_text(encoding="utf-8")[:240]
    if f"web/app.js\n---\n{web_prefix}" not in source_text:
        error("ai/notebooklm-source.txt does not contain the current web/app.js content")
    for required_path in [
        "ai/manifest.json",
        "ai/system-instructions.md",
        "ai/rag/chunks.jsonl",
        "metadata/report-sidecars/00-overview.json",
    ]:
        if required_path not in source_text:
            error(f"ai/notebooklm-source.txt is missing {required_path}")


def main() -> int:
    validate_json_files()

    reports_config = load_json("config/reports.json")
    prompts_config = load_json("config/prompts.json")
    metadata_reports = load_json("metadata/reports.json")
    figures = load_json("metadata/figures.json")
    schema = load_json("metadata/concept-schema.json")
    reports = reports_config.get("reports", [])
    prompts = prompts_config.get("prompts", [])
    report_ids = {report["id"] for report in reports}

    validate_existing_paths(reports, prompts, figures)
    validate_markdown_links()
    validate_figures(figures)
    validate_report_indexes(reports_config, metadata_reports)
    validate_concept_alignment(reports, schema)
    validate_chunks("metadata/chunks.jsonl", report_ids)
    validate_chunks("ai/rag/chunks.jsonl", report_ids)
    validate_ai_package(reports)

    for message in warnings:
        print(f"WARNING: {message}", file=sys.stderr)
    if errors:
        for message in errors:
            print(f"ERROR: {message}", file=sys.stderr)
        return 1
    print("Repository validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
