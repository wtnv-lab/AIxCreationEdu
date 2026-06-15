#!/usr/bin/env python3
"""Build AI-first package files from Markdown reports and structured config."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AI_DIR = ROOT / "ai"
RAG_DIR = AI_DIR / "rag"
SIDECAR_DIR = ROOT / "metadata" / "report-sidecars"
OKF_DIR = ROOT / "okf"
OKF_VERSION = "0.1"
OKF_LOG_DATE = "2026-06-16"
REPOSITORY_BASE_URL = "https://github.com/wtnv-lab/AIxCreationEdu/blob/main"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fp:
        return json.load(fp)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)
        fp.write("\n")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        for row in rows:
            fp.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def source_url(path: str) -> str:
    return f"{REPOSITORY_BASE_URL}/{path}"


def read_markdown(report: dict[str, Any]) -> str:
    path = ROOT / report["output_md"]
    return path.read_text(encoding="utf-8")


def extract_sections(markdown: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    current = {"heading": "", "level": 0, "text": []}
    for line in markdown.splitlines():
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if match:
            if current["heading"] or current["text"]:
                sections.append(
                    {
                        "heading": current["heading"],
                        "level": current["level"],
                        "text": "\n".join(current["text"]).strip(),
                    }
                )
            current = {
                "heading": match.group(2).strip(),
                "level": len(match.group(1)),
                "text": [],
            }
        else:
            current["text"].append(line)
    if current["heading"] or current["text"]:
        sections.append(
            {
                "heading": current["heading"],
                "level": current["level"],
                "text": "\n".join(current["text"]).strip(),
            }
        )
    return sections


def citation_numbers(text: str) -> list[int]:
    found: list[int] = []
    for match in re.finditer(r"\[([0-9,\-\s]+)\]", text):
        for part in match.group(1).split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                start, end = part.split("-", 1)
                if start.strip().isdigit() and end.strip().isdigit():
                    found.extend(range(int(start), int(end) + 1))
            elif part.isdigit():
                found.append(int(part))
    return sorted(dict.fromkeys(found))


def figure_paths(text: str) -> list[str]:
    return re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "section"


def evidence_refs(report_id: str, numbers: list[int], references: dict[str, list[str]]) -> list[str]:
    max_ref = len(references.get(report_id, []))
    return [f"{report_id}-ref-{number:02d}" for number in numbers if 1 <= number <= max_ref]


def figures_for_report(report_id: str, figures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [figure for figure in figures if figure.get("report_id") == report_id]


def figure_ids_for_paths(paths: list[str], figures: list[dict[str, Any]]) -> list[str]:
    normalized = {path.lstrip("./").replace("../", "") for path in paths}
    ids = []
    for figure in figures:
        figure_path = str(figure.get("path", "")).lstrip("./")
        if figure_path in normalized:
            ids.append(figure["id"])
    return ids


def report_claim(report: dict[str, Any], chunk: dict[str, Any]) -> str:
    if chunk.get("chunk_type") == "references":
        return f"{report['title']}で用いる参考文献・関連資料の一覧。"
    if chunk.get("summary"):
        return str(chunk["summary"])
    takeaways = report.get("key_takeaways") or []
    if takeaways:
        return takeaways[0]
    return report.get("abstract") or report["title"]


def usable_for(report: dict[str, Any], chunk: dict[str, Any]) -> list[str]:
    base = ["根拠付き回答", "横断比較"]
    chunk_type = chunk.get("chunk_type")
    if chunk_type == "references":
        return ["引用確認", "参考文献照合", "出典リスト生成"]
    if report.get("kind") == "overview":
        return base + ["全体方針整理", "研修導入", "サービス企画"]
    return base + ["授業案生成", "ワークショップ設計", "教材企画"]


def risk_notes(chunk: dict[str, Any]) -> list[str]:
    notes = [
        "本文にない事実を補う場合は推測として明示する。",
        "AIの出力は完成版ではなく、人間が本文・参考文献・図版メタデータで検証する。",
    ]
    if chunk.get("chunk_type") == "references":
        notes.append("参考文献名や固有名詞は出典表記として保持し、プロジェクト概要の表現規則とは分けて扱う。")
    if "カラー化" in chunk.get("text", ""):
        notes.append("AIカラー化は推定であり、史実の色として断定しない。")
    if "OSINT" in chunk.get("text", ""):
        notes.append("観察事実と推論を分け、確度を明示する。")
    return notes


def build_sidecar(
    report: dict[str, Any],
    references: dict[str, list[str]],
    figures: list[dict[str, Any]],
) -> dict[str, Any]:
    markdown = read_markdown(report)
    sections = extract_sections(markdown)
    report_figures = figures_for_report(report["id"], figures)
    ref_items = []
    for index, citation in enumerate(references.get(report["id"], []), start=1):
        ref_items.append(
            {
                "id": f"{report['id']}-ref-{index:02d}",
                "number": index,
                "citation": citation,
            }
        )

    return {
        "schema": "aice.report_sidecar.v1",
        "report_id": report["id"],
        "title": report["title"],
        "source_md": report["output_md"],
        "source_of_truth": True,
        "html_source_note": "HTML版はこのMarkdown本文とconfig/metadataから生成・表示する。",
        "ai_contract": {
            "read_order": [
                "abstract",
                "key_takeaways",
                "sections",
                "references",
                "figures",
                "risk_notes",
            ],
            "must_cite": True,
            "do_not_infer_beyond_sources": True,
            "human_verification_required": True,
        },
        "authors": report.get("authors", []),
        "audience": report.get("audience", []),
        "themes": report.get("themes", []),
        "keywords": report.get("keywords", []),
        "abstract": report.get("abstract", ""),
        "key_takeaways": report.get("key_takeaways", []),
        "use_cases": report.get("use_cases", []),
        "learning_activities": report.get("learning_activities", []),
        "implementation_ideas": report.get("implementation_ideas", []),
        "related_reports": report.get("related_reports", []),
        "concept_alignment": report.get("concept_alignment", {}),
        "figures": [
            {
                "id": figure["id"],
                "path": figure.get("path", ""),
                "caption": figure.get("caption", ""),
                "alt": figure.get("alt", ""),
                "license_note": figure.get("license_note", ""),
                "license_status": figure.get("license_status", ""),
                "reuse_policy": figure.get("reuse_policy", ""),
            }
            for figure in report_figures
        ],
        "references": ref_items,
        "sections": [
            {
                "id": f"{report['id']}#{slugify(section['heading'])}",
                "heading": section["heading"],
                "level": section["level"],
                "citation_numbers": citation_numbers(section["text"]),
                "evidence_refs": evidence_refs(
                    report["id"], citation_numbers(section["text"]), references
                ),
                "figure_ids": figure_ids_for_paths(figure_paths(section["text"]), report_figures),
                "text_preview": re.sub(r"\s+", " ", section["text"])[:320],
            }
            for section in sections
            if section["heading"]
        ],
        "risk_notes": [
            "このsidecarはAI用の構造化補助であり、本文の正本はsource_mdにある。",
            "引用番号はsource_md内の参考文献登場順に対応する。",
            "図版を説明するときはfigures.pathだけでなくalt/caption/license_note/license_status/reuse_policyも確認する。",
        ],
    }


def build_ai_manifest(project: dict[str, Any], reports: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": "aice.ai_package_manifest.v1",
        "project": project,
        "source_of_truth": {
            "human_markdown": "reports/*.md",
            "report_config": "config/reports.json",
            "references": "config/report_references.json",
            "figures": "metadata/figures.json",
            "okf_bundle": "okf/",
        },
        "ai_first_outputs": [
            "ai/system-instructions.md",
            "ai/context-brief.md",
            "ai/context-full.md",
            "ai/workflows.json",
            "ai/citations.json",
            "ai/rag/chunks.jsonl",
            "metadata/report-sidecars/*.json",
            "okf/",
        ],
        "reports": [
            {
                "id": report["id"],
                "title": report["title"],
                "source_md": report["output_md"],
                "sidecar": f"metadata/report-sidecars/{report['id']}.json",
                "okf_concept": f"okf/reports/{report['id']}.md",
            }
            for report in reports
        ],
        "human_verification_required": True,
    }


def build_citations(reports: list[dict[str, Any]], references: dict[str, list[str]]) -> dict[str, Any]:
    items = []
    for report in reports:
        for index, citation in enumerate(references.get(report["id"], []), start=1):
            items.append(
                {
                    "id": f"{report['id']}-ref-{index:02d}",
                    "report_id": report["id"],
                    "report_title": report["title"],
                    "number": index,
                    "citation": citation,
                    "source_md": report["output_md"],
                }
            )
    return {
        "schema": "aice.citations.v1",
        "rule": "本文中の[1]などの番号はreport_idごとのreferences[number]に対応する。",
        "items": items,
    }


def extract_markdown_list_after_heading(markdown: str, heading: str) -> list[str]:
    lines = markdown.splitlines()
    items: list[str] = []
    capture = False
    for line in lines:
        if re.match(r"^#{2,6}\s+", line):
            if capture:
                break
            capture = line.strip() == heading
            continue
        if capture:
            numbered = re.match(r"^\s*\d+\.\s+(.+)$", line)
            bulleted = re.match(r"^\s*[-*]\s+(.+)$", line)
            if numbered:
                items.append(numbered.group(1).strip())
            elif bulleted:
                items.append(bulleted.group(1).strip())
    return items


def workflow_context(prompt_id: str) -> list[str]:
    base = [
        "ai/system-instructions.md",
        "ai/context-brief.md",
        "ai/manifest.json",
    ]
    if prompt_id in {"citation-answering", "cross-report-comparison"}:
        return base + [
            "ai/rag/chunks.jsonl",
            "ai/citations.json",
            "metadata/report-sidecars/*.json",
            "metadata/figures.json",
            "reports/*.md",
        ]
    if prompt_id in {"lesson-plan-generation", "workshop-design", "service-planning", "implementation-roadmap"}:
        return base + [
            "ai/context-full.md",
            "ai/rag/chunks.jsonl",
            "metadata/report-sidecars/*.json",
            "metadata/reports.json",
            "prompts/" + prompt_id + ".md",
        ]
    return base + [
        "ai/context-full.md",
        "ai/rag/chunks.jsonl",
        "metadata/report-sidecars/*.json",
        "metadata/concept-schema.json",
        "prompts/" + prompt_id + ".md",
    ]


def build_workflows(prompts_config: dict[str, Any]) -> dict[str, Any]:
    workflows = []
    for prompt in prompts_config.get("prompts", []):
        path = ROOT / prompt["path"]
        markdown = path.read_text(encoding="utf-8")
        workflows.append(
            {
                "id": prompt["id"],
                "purpose": prompt.get("purpose", ""),
                "prompt_path": prompt["path"],
                "read_before_running": workflow_context(prompt["id"]),
                "input_contract": extract_markdown_list_after_heading(markdown, "## 入力条件"),
                "output_contract": extract_markdown_list_after_heading(markdown, "## 出力形式"),
                "evidence_policy": {
                    "prefer": [
                        "ai/rag/chunks.jsonl",
                        "metadata/report-sidecars/*.json",
                        "ai/citations.json",
                        "reports/*.md",
                    ],
                    "cite_with": [
                        "report_id",
                        "chunk_id",
                        "evidence_refs",
                        "figure_ids",
                    ],
                    "mark_unsourced_claims_as_inference": True,
                    "human_verification_required": True,
                },
            }
        )
    return {
        "schema": "aice.ai_workflows.v1",
        "description": "AIエージェントが用途別プロンプトを選び、必要資料と出力契約を確認するための機械可読ワークフロー索引。",
        "default_read_order": [
            "ai/system-instructions.md",
            "ai/manifest.json",
            "ai/context-brief.md",
            "ai/workflows.json",
        ],
        "workflows": workflows,
    }


def build_rag_chunks(
    chunks: list[dict[str, Any]],
    reports_by_id: dict[str, dict[str, Any]],
    references: dict[str, list[str]],
    figures: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for chunk in chunks:
        report = reports_by_id.get(chunk.get("report_id"))
        if not report:
            continue
        numbers = citation_numbers(chunk.get("text", ""))
        report_figures = figures_for_report(report["id"], figures)
        rows.append(
            {
                "schema": "aice.rag_chunk.v1",
                "id": chunk["id"],
                "report_id": report["id"],
                "source_md": chunk.get("source") or report["output_md"],
                "title": chunk.get("title") or report["title"],
                "section": chunk.get("section", ""),
                "chunk_type": chunk.get("chunk_type", ""),
                "claim": report_claim(report, chunk),
                "text": chunk.get("text", ""),
                "evidence_refs": evidence_refs(report["id"], numbers, references),
                "figure_ids": figure_ids_for_paths(figure_paths(chunk.get("text", "")), report_figures),
                "audience": chunk.get("audience") or report.get("audience", []),
                "themes": chunk.get("themes") or report.get("themes", []),
                "keywords": chunk.get("keywords") or report.get("keywords", []),
                "usable_for": usable_for(report, chunk),
                "risk_notes": risk_notes(chunk),
                "depends_on": report.get("related_reports", []),
                "human_verification_required": True,
            }
        )
    return rows


def markdown_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def build_system_instructions(project: dict[str, Any]) -> str:
    return f"""# AI System Instructions: {project.get("title", "AIとクリエイティブと教育")}

このファイルは、AIが本リポジトリを読むときの優先順位と禁止事項を定める。

## 読む順序

1. `ai/manifest.json` で利用可能なAI向けファイルを把握する。
2. 全体像は `ai/context-brief.md` を読む。
3. 用途別の実行手順は `ai/workflows.json` を読む。
4. 詳細な根拠は `metadata/report-sidecars/*.json` と `ai/rag/chunks.jsonl` を読む。
5. 人間向けの正本確認が必要な場合は `reports/*.md` を読む。
6. 出典確認は `ai/citations.json` と `references/references.md` を使う。
7. 他システムへ知識バンドルとして渡す場合は `okf/index.md` から始める。

## 回答ルール

- 本文・メタデータ・参考文献にないことは、推測として明示する。
- 授業案、研修案、サービス企画を出す場合は、根拠にした `report_id` と `evidence_refs` を示す。
- AI出力を完成版として扱わず、人間による検証・編集が必要であることを前提にする。
- 図版について述べる場合は、画像パスだけでなく `metadata/figures.json` の `alt`、`caption`、`license_note`、`license_status`、`reuse_policy` を確認する。
- プロジェクト概要ではAIサービスの商品名を出さず、必要な場合は「対話型生成AI」「AI読解ツール」「コード生成支援AI」などの一般名詞で述べる。
- レポート本文・参考文献に含まれる固有名詞は、出典や事例の正確性に関わるため、一般化せず出典として扱う。

## 重要な制約

- `reports/*.md` が人間向けHTML版の本文正本である。
- `metadata/report-sidecars/*.json` はAI用の構造化補助であり、本文の代替ではない。
- `ai/rag/chunks.jsonl` は検索・RAG用であり、チャンク単体で結論を断定しない。
- `ai/notebooklm-source.txt` は単一テキスト読解ツール向けの互換パッケージである。
- `okf/` はOpen Knowledge Format v0.1互換の交換用ビューであり、正本本文やsidecarから生成される。
"""


def build_context_brief(project: dict[str, Any], reports: list[dict[str, Any]]) -> str:
    lines = [
        f"# AI Context Brief: {project.get('title', 'AIとクリエイティブと教育')}",
        "",
        "## プロジェクト概要",
        "",
        "生成AI時代の創造性教育を、問い・資料読解・制作・検証・社会発信をつなぐ学びとして整理する公開プロジェクト。",
        "人間向けにはMarkdownレポートとHTML閲覧アプリを、AI向けには構造化メタデータ、RAGチャンク、引用対応、用途別プロンプトを提供する。",
        "",
        "## AIに渡すときの最短ルート",
        "",
        "1. この `ai/context-brief.md` で全体像を把握する。",
        "2. `ai/system-instructions.md` の回答ルールを守る。",
        "3. 根拠が必要な回答では `ai/rag/chunks.jsonl` と `ai/citations.json` を使う。",
        "4. 重要な判断では `reports/*.md` の本文を確認する。",
        "5. 他のエージェントや組織へ交換する場合は `okf/index.md` を入口にする。",
        "",
        "## レポート一覧",
        "",
    ]
    for report in reports:
        lines.extend(
            [
                f"### {report['id']}: {report['title']}",
                "",
                f"- 要旨: {report.get('abstract', '')}",
                f"- 著者: {', '.join(report.get('authors', []))}",
                f"- 主なテーマ: {', '.join(report.get('themes', []))}",
                f"- 想定読者: {', '.join(report.get('audience', []))}",
                f"- 正本: `{report['output_md']}`",
                f"- AI sidecar: `metadata/report-sidecars/{report['id']}.json`",
                f"- OKF concept: `okf/reports/{report['id']}.md`",
                "",
            ]
        )
    return "\n".join(lines)


def build_context_full(project: dict[str, Any], reports: list[dict[str, Any]]) -> str:
    lines = [
        f"# AI Context Full: {project.get('title', 'AIとクリエイティブと教育')}",
        "",
        "このファイルは、AIが本文へ入る前に読む構造化サマリーである。本文の正本は `reports/*.md` にある。",
        "",
        "## プロジェクト",
        "",
        f"- タイトル: {project.get('title', '')}",
        f"- 説明: {project.get('description', '')}",
        f"- ライセンス: {project.get('license', '')}",
        f"- 支援表記: {project.get('support_statement', '')}",
        "",
    ]
    for report in reports:
        lines.extend(
            [
                f"## {report['id']}: {report['title']}",
                "",
                f"- 種別: {report.get('kind', '')}",
                f"- 正本Markdown: `{report['output_md']}`",
                f"- Sidecar: `metadata/report-sidecars/{report['id']}.json`",
                f"- OKF concept: `okf/reports/{report['id']}.md`",
                f"- 要旨: {report.get('abstract', '')}",
                f"- 著者: {', '.join(report.get('authors', []))}",
                f"- 想定読者: {', '.join(report.get('audience', []))}",
                f"- テーマ: {', '.join(report.get('themes', []))}",
                f"- キーワード: {', '.join(report.get('keywords', []))}",
                "",
                "### 主要示唆",
                markdown_list(report.get("key_takeaways", [])) or "- 未設定",
                "",
                "### 活用場面",
                markdown_list(report.get("use_cases", [])) or "- 未設定",
                "",
                "### 学習活動案",
                markdown_list(report.get("learning_activities", [])) or "- 未設定",
                "",
                "### 実装アイデア",
                markdown_list(report.get("implementation_ideas", [])) or "- 未設定",
                "",
            ]
        )
    return "\n".join(lines)


def yaml_value(value: Any) -> str:
    if value is None:
        return '""'
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(yaml_value(item) for item in value) + "]"
    return json.dumps(str(value), ensure_ascii=False)


def okf_frontmatter(fields: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in fields.items():
        lines.append(f"{key}: {yaml_value(value)}")
    lines.append("---")
    return "\n".join(lines)


def unique_tags(*groups: list[str]) -> list[str]:
    tags: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for value in group:
            normalized = str(value).strip()
            if not normalized or normalized in seen:
                continue
            tags.append(normalized)
            seen.add(normalized)
    return tags


def first_heading(markdown: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    return match.group(1).strip() if match else fallback


def okf_timestamp(project: dict[str, Any]) -> str:
    date = project.get("date") or OKF_LOG_DATE
    return f"{date}T00:00:00Z"


def okf_report_filename(report: dict[str, Any]) -> str:
    return f"{report['id']}.md"


def okf_markdown_list(items: list[str]) -> str:
    return "\n".join(f"* {item}" for item in items) if items else "* 未設定"


def build_okf_root_index(project: dict[str, Any], reports: list[dict[str, Any]], prompts: list[dict[str, Any]]) -> str:
    report_count = len(reports)
    prompt_count = len(prompts)
    frontmatter = okf_frontmatter({"okf_version": OKF_VERSION})
    return f"""{frontmatter}
# Knowledge Bundle

* [Project](project.md) - {project.get("description", "プロジェクト概要")}
* [Reports](reports/) - {report_count}件のレポート概念
* [Prompts](prompts/) - {prompt_count}件のプロンプト概念
* [References](references/) - 参考文献・関連資料の入口

# Maintenance

* [Update log](log.md) - OKFバンドルの更新履歴
"""


def build_okf_log() -> str:
    return f"""# Directory Update Log

## {OKF_LOG_DATE}
* **Creation**: Added an Open Knowledge Format v{OKF_VERSION}-compatible bundle generated from `config/reports.json`, `config/prompts.json`, and the AI package metadata.
"""


def build_okf_project(project: dict[str, Any]) -> str:
    body = [
        f"# {project.get('title', 'AIとクリエイティブと教育')}",
        "",
        project.get("description", ""),
        "",
        "# Bundle Scope",
        "",
        "このOKFバンドルは、レポート、プロンプト、参考文献を、人間とAIエージェントが同じMarkdown概念としてたどれるようにした交換用ビューです。",
        "本文正本は `reports/*.md`、構造化補助は `metadata/report-sidecars/*.json` と `ai/rag/chunks.jsonl` にあります。",
        "",
        "# Entry Points",
        "",
        "* [Reports](/reports/) - レポート単位の概念",
        "* [Prompts](/prompts/) - 利用目的別プロンプト",
        "* [References](/references/project-references.md) - 参考文献・関連資料",
        "",
        "# Citations",
        "",
        f"[1] [README.md]({source_url('README.md')})",
    ]
    return "\n".join(
        [
            okf_frontmatter(
                {
                    "type": "Knowledge Bundle",
                    "title": project.get("title", "AIとクリエイティブと教育"),
                    "description": project.get("description", ""),
                    "resource": source_url("README.md"),
                    "tags": ["AI education", "creativity education", "knowledge bundle"],
                    "timestamp": okf_timestamp(project),
                    "license": project.get("license", ""),
                    "aice_source": "README.md",
                }
            ),
            "",
            "\n".join(body),
        ]
    )


def build_okf_reports_index(reports: list[dict[str, Any]]) -> str:
    lines = ["# Reports", ""]
    for report in reports:
        lines.append(
            f"* [{report['title']}]({okf_report_filename(report)}) - {report.get('abstract', '')}"
        )
    return "\n".join(lines)


def build_okf_report_concept(project: dict[str, Any], report: dict[str, Any]) -> str:
    alignment = report.get("concept_alignment") or {}
    sidecar_path = f"metadata/report-sidecars/{report['id']}.json"
    tags = unique_tags(
        [report.get("kind", "report")],
        report.get("themes", []),
        report.get("keywords", []),
        alignment.get("domain_tags", []),
    )
    related = report.get("related_reports", [])
    body = [
        f"# {report['title']}",
        "",
        report.get("abstract", ""),
        "",
        "# Source",
        "",
        f"* 正本Markdown: [{report['output_md']}]({source_url(report['output_md'])})",
        f"* AI sidecar: [{sidecar_path}]({source_url(sidecar_path)})",
        f"* RAG chunks: [ai/rag/chunks.jsonl]({source_url('ai/rag/chunks.jsonl')})",
        "",
        "# Audience",
        "",
        okf_markdown_list(report.get("audience", [])),
        "",
        "# Key Takeaways",
        "",
        okf_markdown_list(report.get("key_takeaways", [])),
        "",
        "# Use Cases",
        "",
        okf_markdown_list(report.get("use_cases", [])),
        "",
        "# Learning Activities",
        "",
        okf_markdown_list(report.get("learning_activities", [])),
        "",
        "# Implementation Ideas",
        "",
        okf_markdown_list(report.get("implementation_ideas", [])),
        "",
        "# Related Concepts",
        "",
        "\n".join(f"* [{item}](/reports/{item}.md)" for item in related) if related else "* 未設定",
        "",
        "# Concept Alignment",
        "",
        "```json",
        json.dumps(alignment, ensure_ascii=False, indent=2),
        "```",
        "",
        "# Citations",
        "",
        f"[1] [{report['output_md']}]({source_url(report['output_md'])})",
        f"[2] [{sidecar_path}]({source_url(sidecar_path)})",
    ]
    return "\n".join(
        [
            okf_frontmatter(
                {
                    "type": "Report",
                    "title": report["title"],
                    "description": report.get("abstract", ""),
                    "resource": source_url(report["output_md"]),
                    "tags": tags,
                    "timestamp": okf_timestamp(project),
                    "authors": report.get("authors", []),
                    "license": project.get("license", ""),
                    "aice_report_id": report["id"],
                    "aice_kind": report.get("kind", ""),
                    "aice_source_md": report["output_md"],
                    "aice_sidecar": sidecar_path,
                }
            ),
            "",
            "\n".join(body),
        ]
    )


def build_okf_prompts_index(prompts: list[dict[str, Any]]) -> str:
    lines = ["# Prompts", ""]
    for prompt in prompts:
        lines.append(f"* [{prompt['id']}]({prompt['id']}.md) - {prompt.get('purpose', '')}")
    return "\n".join(lines)


def build_okf_prompt_concept(project: dict[str, Any], prompt: dict[str, Any]) -> str:
    markdown = (ROOT / prompt["path"]).read_text(encoding="utf-8")
    title = first_heading(markdown, prompt["id"])
    body = [
        f"# {title}",
        "",
        prompt.get("purpose", ""),
        "",
        "# Source",
        "",
        f"* Prompt source: [{prompt['path']}]({source_url(prompt['path'])})",
        "",
        "# Prompt Body",
        "",
        markdown.strip(),
        "",
        "# Citations",
        "",
        f"[1] [{prompt['path']}]({source_url(prompt['path'])})",
    ]
    return "\n".join(
        [
            okf_frontmatter(
                {
                    "type": "Prompt",
                    "title": title,
                    "description": prompt.get("purpose", ""),
                    "resource": source_url(prompt["path"]),
                    "tags": ["prompt", "AI workflow", "education planning"],
                    "timestamp": okf_timestamp(project),
                    "aice_prompt_id": prompt["id"],
                    "aice_source_md": prompt["path"],
                }
            ),
            "",
            "\n".join(body),
        ]
    )


def build_okf_references_index() -> str:
    return """# References

* [Project references](project-references.md) - レポート別の参考文献・関連資料
"""


def build_okf_reference_concept(project: dict[str, Any], reports: list[dict[str, Any]], references: dict[str, list[str]]) -> str:
    lines = [
        "# 参考文献・関連資料",
        "",
        "この概念は、レポート本文で使われる参考文献・関連資料の束を示します。詳細な文献リストは正本ファイルを参照してください。",
        "",
        "# Report Reference Groups",
        "",
    ]
    for report in reports:
        count = len(references.get(report["id"], []))
        lines.append(f"* [{report['title']}](/reports/{report['id']}.md) - {count}件")
    lines.extend(
        [
            "",
            "# Source",
            "",
            f"* References markdown: [references/references.md]({source_url('references/references.md')})",
            f"* BibTeX: [references/references.bib]({source_url('references/references.bib')})",
            "",
            "# Citations",
            "",
            f"[1] [references/references.md]({source_url('references/references.md')})",
            f"[2] [references/references.bib]({source_url('references/references.bib')})",
        ]
    )
    return "\n".join(
        [
            okf_frontmatter(
                {
                    "type": "Reference Collection",
                    "title": "参考文献・関連資料",
                    "description": "レポート本文で使われる参考文献・関連資料の索引。",
                    "resource": source_url("references/references.md"),
                    "tags": ["references", "citations", "evidence"],
                    "timestamp": okf_timestamp(project),
                    "aice_source_md": "references/references.md",
                }
            ),
            "",
            "\n".join(lines),
        ]
    )


def write_okf_bundle(
    project: dict[str, Any],
    reports: list[dict[str, Any]],
    prompts_config: dict[str, Any],
    references: dict[str, list[str]],
) -> None:
    prompts = prompts_config.get("prompts", [])
    if OKF_DIR.exists():
        shutil.rmtree(OKF_DIR)

    write_text(OKF_DIR / "index.md", build_okf_root_index(project, reports, prompts))
    write_text(OKF_DIR / "log.md", build_okf_log())
    write_text(OKF_DIR / "project.md", build_okf_project(project))

    write_text(OKF_DIR / "reports" / "index.md", build_okf_reports_index(reports))
    for report in reports:
        write_text(
            OKF_DIR / "reports" / okf_report_filename(report),
            build_okf_report_concept(project, report),
        )

    write_text(OKF_DIR / "prompts" / "index.md", build_okf_prompts_index(prompts))
    for prompt in prompts:
        write_text(
            OKF_DIR / "prompts" / f"{prompt['id']}.md",
            build_okf_prompt_concept(project, prompt),
        )

    write_text(OKF_DIR / "references" / "index.md", build_okf_references_index())
    write_text(
        OKF_DIR / "references" / "project-references.md",
        build_okf_reference_concept(project, reports, references),
    )


def main() -> None:
    reports_config = load_json(ROOT / "config" / "reports.json")
    references = load_json(ROOT / "config" / "report_references.json")
    prompts_config = load_json(ROOT / "config" / "prompts.json")
    figures = load_json(ROOT / "metadata" / "figures.json")
    chunks = load_jsonl(ROOT / "metadata" / "chunks.jsonl")
    project = reports_config["project"]
    reports = reports_config["reports"]
    reports_by_id = {report["id"]: report for report in reports}

    AI_DIR.mkdir(exist_ok=True)
    RAG_DIR.mkdir(parents=True, exist_ok=True)
    SIDECAR_DIR.mkdir(parents=True, exist_ok=True)

    write_json(AI_DIR / "manifest.json", build_ai_manifest(project, reports))
    write_text(AI_DIR / "system-instructions.md", build_system_instructions(project))
    write_text(AI_DIR / "context-brief.md", build_context_brief(project, reports))
    write_text(AI_DIR / "context-full.md", build_context_full(project, reports))
    write_json(AI_DIR / "workflows.json", build_workflows(prompts_config))
    write_json(AI_DIR / "citations.json", build_citations(reports, references))
    write_jsonl(
        RAG_DIR / "chunks.jsonl",
        build_rag_chunks(chunks, reports_by_id, references, figures),
    )

    for report in reports:
        write_json(
            SIDECAR_DIR / f"{report['id']}.json",
            build_sidecar(report, references, figures),
        )

    write_okf_bundle(project, reports, prompts_config, references)


if __name__ == "__main__":
    main()
