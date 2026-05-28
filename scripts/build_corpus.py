#!/usr/bin/env python3
"""Build Markdown reports and AI-readable corpus files from DOCX sources.

This script intentionally uses only Python's standard library so the repository
can be rebuilt on a plain macOS/Linux environment without pandoc or npm.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from zipfile import ZipFile
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
}


@dataclass
class Paragraph:
    text: str
    style: str | None = None
    is_list: bool = False
    image_markdown: list[str] | None = None


def qn(prefix: str, name: str) -> str:
    return f"{{{NS[prefix]}}}{name}"


def clean_text(value: str) -> str:
    value = value.replace("\u3000", " ")
    value = re.sub(r"[ \t]+", " ", value)
    return value.strip()


def yaml_list(values: Iterable[str], indent: int = 2) -> str:
    pad = " " * indent
    return "\n".join(f"{pad}- {json.dumps(v, ensure_ascii=False)}" for v in values)


def author_markdown(project: dict) -> str:
    lines: list[str] = []
    for group in project.get("authors", []):
        lines.append(f"### {group['affiliation']}")
        lines.append("")
        for member in group.get("members", []):
            lines.append(f"- {member}")
        lines.append("")
    return "\n".join(lines).strip()


def ai_collaborator_markdown(project: dict) -> str:
    lines: list[str] = []
    for tool in project.get("ai_collaborators", []):
        note = f"。{tool['note']}" if tool.get("note") else ""
        lines.append(f"- {tool['name']}（{tool['provider']}）: {tool['version']}{note}")
    return "\n".join(lines)


def report_audience(report: dict, project: dict) -> list[str]:
    return report.get("audience") or project["audience"]


def report_authors(report: dict, project: dict) -> list[str]:
    return report.get("authors") or author_plain_list(project)


AI_REPORT_LIST_FIELDS = [
    "key_takeaways",
    "use_cases",
    "learning_activities",
    "implementation_ideas",
    "related_reports",
]


def report_metadata_markdown(report: dict, project: dict) -> str:
    lines = [
        "## メタデータ",
        "",
        f"- ID: `{report['id']}`",
        f"- プロジェクト: {project['title']}",
        f"- 日付: {project['date']}",
        f"- バージョン: {project['version']}",
        f"- 種別: {report['kind']}",
        f"- 概要: {report.get('abstract', '')}",
        f"- 著者: {', '.join(report_authors(report, project))}",
        "",
        "### 想定読者",
        "",
        *[f"- {audience}" for audience in report_audience(report, project)],
    ]
    metadata_labels = {
        "key_takeaways": "主要示唆",
        "use_cases": "活用場面",
        "learning_activities": "学習活動案",
        "implementation_ideas": "実装アイデア",
        "related_reports": "関連レポート",
    }
    for field in AI_REPORT_LIST_FIELDS:
        values = report.get(field, [])
        if values:
            lines.extend(["", f"### {metadata_labels[field]}", "", *[f"- {value}" for value in values]])
    if report.get("citation_note"):
        lines.extend(["", "### 引用メモ", "", report["citation_note"]])
    lines.extend(
        [
            "",
            "### テーマ",
            "",
            *[f"- {theme}" for theme in report["themes"]],
            "",
            "### キーワード",
            "",
            *[f"- {keyword}" for keyword in report["keywords"]],
            "",
            "### ライセンス",
            "",
            project["license"],
        ]
    )
    return "\n".join(lines)


def report_ai_fields(report: dict) -> dict[str, list[str] | str]:
    fields: dict[str, list[str] | str] = {}
    for field in AI_REPORT_LIST_FIELDS:
        fields[field] = report.get(field, [])
    fields["citation_note"] = report.get("citation_note", "")
    return fields


def author_plain_list(project: dict) -> list[str]:
    authors: list[str] = []
    for group in project.get("authors", []):
        for member in group.get("members", []):
            authors.append(f"{group['affiliation']} {member}")
    return authors


def read_relationships(zf: ZipFile) -> dict[str, str]:
    rels_path = "word/_rels/document.xml.rels"
    if rels_path not in zf.namelist():
        return {}
    root = ET.fromstring(zf.read(rels_path))
    rels = {}
    for rel in root:
        rid = rel.attrib.get("Id")
        target = rel.attrib.get("Target")
        if rid and target:
            rels[rid] = target
    return rels


def style_id(paragraph: ET.Element) -> str | None:
    pstyle = paragraph.find("./w:pPr/w:pStyle", NS)
    if pstyle is None:
        return None
    return pstyle.attrib.get(qn("w", "val"))


def is_list_item(paragraph: ET.Element) -> bool:
    return paragraph.find("./w:pPr/w:numPr", NS) is not None


def collect_run_text(node: ET.Element, rels: dict[str, str], zf: ZipFile, assets_dir: Path, report_id: str) -> tuple[str, list[str]]:
    text_parts: list[str] = []
    images: list[str] = []

    if node.tag == qn("w", "hyperlink"):
        rid = node.attrib.get(qn("r", "id"))
        label = "".join(t.text or "" for t in node.findall(".//w:t", NS))
        target = rels.get(rid or "")
        if label and target:
            text_parts.append(f"[{label}]({target})")
        else:
            text_parts.append(label)
        return "".join(text_parts), images

    if node.tag == qn("w", "t"):
        text_parts.append(node.text or "")
    elif node.tag == qn("w", "tab"):
        text_parts.append(" ")
    elif node.tag == qn("w", "br"):
        text_parts.append("\n")

    for blip in node.findall(".//a:blip", NS):
        rid = blip.attrib.get(qn("r", "embed"))
        target = rels.get(rid or "")
        if target.startswith("media/"):
            source = f"word/{target}"
            if source in zf.namelist():
                assets_dir.mkdir(parents=True, exist_ok=True)
                filename = Path(target).name
                out_path = assets_dir / filename
                out_path.write_bytes(zf.read(source))
                rel_path = Path("..") / "assets" / report_id / filename
                images.append(f"![{report_id} image]({rel_path.as_posix()})")

    for child in list(node):
        child_text, child_images = collect_run_text(child, rels, zf, assets_dir, report_id)
        text_parts.append(child_text)
        images.extend(child_images)

    return "".join(text_parts), images


def parse_table(table: ET.Element, rels: dict[str, str], zf: ZipFile, assets_dir: Path, report_id: str) -> str:
    rows: list[list[str]] = []
    for tr in table.findall("./w:tr", NS):
        cells = []
        for tc in tr.findall("./w:tc", NS):
            parts = []
            for p in tc.findall(".//w:p", NS):
                text, _ = collect_run_text(p, rels, zf, assets_dir, report_id)
                text = clean_text(text)
                if text:
                    parts.append(text)
            cells.append("<br>".join(parts))
        if cells:
            rows.append(cells)

    if not rows:
        return ""
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    header = "| " + " | ".join(rows[0]) + " |"
    sep = "| " + " | ".join(["---"] * width) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rows[1:]]
    return "\n".join([header, sep, *body])


def parse_docx(docx_path: Path, report_id: str) -> list[Paragraph | str]:
    assets_dir = ROOT / "assets" / report_id
    if assets_dir.exists():
        shutil.rmtree(assets_dir)

    blocks: list[Paragraph | str] = []
    with ZipFile(docx_path) as zf:
        rels = read_relationships(zf)
        root = ET.fromstring(zf.read("word/document.xml"))
        body = root.find("./w:body", NS)
        if body is None:
            return []
        for child in list(body):
            if child.tag == qn("w", "p"):
                text, images = collect_run_text(child, rels, zf, assets_dir, report_id)
                text = clean_text(text)
                if text or images:
                    blocks.append(
                        Paragraph(
                            text=text,
                            style=style_id(child),
                            is_list=is_list_item(child),
                            image_markdown=images,
                        )
                    )
            elif child.tag == qn("w", "tbl"):
                md_table = parse_table(child, rels, zf, assets_dir, report_id)
                if md_table:
                    blocks.append(md_table)
    return blocks


def paragraph_to_markdown(blocks: list[Paragraph | str], report: dict, project: dict) -> tuple[str, list[str], str]:
    lines: list[str] = [f"# {report['title']}", ""]
    references: list[str] = report.get("references", [])
    abstract_parts: list[str] = []
    saw_title = False
    in_references = False
    has_reference_overrides = bool(references)

    for block in blocks:
        if isinstance(block, str):
            lines.extend([block, ""])
            continue

        text = block.text
        if not text and block.image_markdown:
            lines.extend(block.image_markdown + [""])
            continue

        normalized = clean_text(text)
        if not normalized:
            continue

        if normalized == report["title"] or normalized.replace(" ", "") == report["title"].replace(" ", ""):
            saw_title = True
            continue

        if not saw_title and normalized.startswith(report["title"][:8]):
            saw_title = True
            continue

        if re.search(r"参考文献|関連研究|参考資料|参照資料", normalized):
            if not in_references and not has_reference_overrides:
                lines.extend(["## 参考文献・関連資料", ""])
            in_references = True
            continue

        stripped = re.sub(r"^[・•●○]\s*", "", normalized)
        if in_references:
            if not has_reference_overrides:
                references.append(stripped)
                lines.extend([f"- {stripped}", ""])
            continue

        heading_level = None
        style = (block.style or "").lower()
        if "heading1" in style or "1" == style:
            heading_level = 2
        elif "heading2" in style or "2" == style:
            heading_level = 3
        elif re.fullmatch(r"[0-9０-９]+[.．、]\s*.+", normalized) and len(normalized) < 60:
            heading_level = 2

        if heading_level:
            lines.extend([f"{'#' * heading_level} {normalized}", ""])
        elif block.is_list or normalized.startswith(("・", "•", "●", "○")):
            lines.append(f"- {stripped}")
        else:
            if len(abstract_parts) < 2 and len(normalized) >= 80:
                abstract_parts.append(normalized)
            lines.extend([normalized, ""])

        if block.image_markdown:
            lines.extend(block.image_markdown + [""])

    if has_reference_overrides:
        lines.extend(["## 参考文献・関連資料", ""])
        lines.extend([f"- {ref}" for ref in references])
        lines.append("")

    abstract = clean_text(report.get("abstract") or " ".join(abstract_parts))
    if len(abstract) > 220:
        abstract = abstract[:220].rstrip() + "..."
    lines.extend(["", report_metadata_markdown(report | {"abstract": abstract}, project), ""])
    return "\n".join(lines).strip() + "\n", references, abstract


def chunk_markdown(report: dict, markdown: str, max_chars: int = 1200) -> list[dict]:
    chunks: list[dict] = []
    current_heading = report["title"]
    current_lines: list[str] = []

    def chunk_type_for(section: str) -> str:
        if re.search(r"参考文献|関連資料", section):
            return "references"
        if report.get("kind") == "overview":
            return "overview"
        return "body"

    def chunk_summary(section: str, text: str) -> str:
        kind = chunk_type_for(section)
        if kind == "references":
            return f"{report['title']}の参考文献・関連資料を示すチャンク。"
        note = report.get("citation_note") or report.get("abstract", "")
        if not note:
            note = text[:120]
        note = clean_text(note)
        if len(note) > 140:
            note = note[:140].rstrip() + "..."
        return note

    def flush() -> None:
        nonlocal current_lines
        text = clean_text(" ".join(line for line in current_lines if not line.startswith("---")))
        if text:
            chunk_id = f"{report['id']}:{len(chunks) + 1:03d}"
            chunks.append(
                {
                    "id": chunk_id,
                    "report_id": report["id"],
                    "title": report["title"],
                    "section": current_heading,
                    "authors": report.get("authors", []),
                    "audience": report.get("audience", []),
                    "chunk_type": chunk_type_for(current_heading),
                    "summary": chunk_summary(current_heading, text),
                    "themes": report["themes"],
                    "keywords": report["keywords"],
                    "text": text,
                    "source": report["output_md"],
                }
            )
        current_lines = []

    in_frontmatter = False
    in_report_metadata = False
    for line in markdown.splitlines():
        if line == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        if line.startswith("## メタデータ"):
            flush()
            in_report_metadata = True
            continue
        if in_report_metadata:
            continue
        if line.startswith("## "):
            flush()
            current_heading = line[3:].strip()
        elif line.startswith("# "):
            continue
        elif not line.strip():
            if sum(len(item) for item in current_lines) >= max_chars:
                flush()
        else:
            current_lines.append(line)
            if sum(len(item) for item in current_lines) >= max_chars:
                flush()
    flush()
    return chunks


def supplemental_citation(item: dict) -> str:
    if item.get("citation"):
        return item["citation"]

    title = item["title"].rstrip(".")
    url = item["url"]
    org_match = re.match(r"^([^,]+),\s*(.+),\s*(\d{4})$", title)
    if org_match:
        org, work, year = org_match.groups()
        return f"{org}. {year}. {work}. Retrieved May 27, 2026 from {url}"

    jp_match = re.match(r"^([^『]+)『(.+)』(\d{4})年$", title)
    if jp_match:
        org, work, year = jp_match.groups()
        return f"{org}. {year}. {work}. Retrieved May 27, 2026 from {url}"

    if title.startswith("文化庁『") and title.endswith("』"):
        return f"文化庁. n.d. {title[4:-1]}. Retrieved May 27, 2026 from {url}"

    if title.startswith("MIT RAISE, "):
        return f"MIT RAISE. n.d. {title.removeprefix('MIT RAISE, ')}. Retrieved May 27, 2026 from {url}"
    if title.startswith("Raspberry Pi Foundation and Google DeepMind, "):
        return f"Raspberry Pi Foundation and Google DeepMind. n.d. {title.removeprefix('Raspberry Pi Foundation and Google DeepMind, ')}. Retrieved May 27, 2026 from {url}"
    if title.startswith("Harvard University, "):
        return f"Harvard University. n.d. {title.removeprefix('Harvard University, ')}. Retrieved May 27, 2026 from {url}"
    if title.startswith("Harvard metaLAB, "):
        return f"Harvard metaLAB. 2023. {title.removeprefix('Harvard metaLAB, ').removesuffix(', 2023')}. Retrieved May 27, 2026 from {url}"
    if title.startswith("Khan Academy, "):
        return f"Khan Academy. n.d. {title.removeprefix('Khan Academy, ')}. Retrieved May 27, 2026 from {url}"
    if title.startswith("Bellingcat, "):
        return f"Bellingcat. n.d. {title.removeprefix('Bellingcat, ')}. Retrieved May 27, 2026 from {url}"
    if title.startswith("Stanford HAI, "):
        return f"Stanford HAI. 2025. {title.removeprefix('Stanford HAI, ').removesuffix(', 2025')}. Retrieved May 27, 2026 from {url}"
    if title.startswith("OpenAI, "):
        return f"OpenAI. 2026. {title.removeprefix('OpenAI, ').removesuffix(', 2026')}. Retrieved May 27, 2026 from {url}"
    if title.startswith("Google, "):
        return f"Google. 2026. {title.removeprefix('Google, ').removesuffix(', 2026')}. Retrieved May 27, 2026 from {url}"
    if title.startswith("GitHub Changelog, "):
        return f"GitHub. 2026. {title.removeprefix('GitHub Changelog, ').removesuffix(', 2026')}. GitHub Changelog. Retrieved May 27, 2026 from {url}"

    return f"{title}. Retrieved May 27, 2026 from {url}"


def write_readme(config: dict, abstracts: dict[str, str]) -> None:
    project = config["project"]
    report_lines = []
    for report in config["reports"]:
        report_lines.append(
            f"- [{report['title']}]({report['output_md']}): {abstracts.get(report['id'], '')}"
        )

    readme = f"""# {project['title']}

> {project['description']}

このリポジトリは、教育関係者および教育ソリューション提供企業が、生成AI時代の教育実践を検討するための公開資料集です。人間が読みやすいMarkdown本文と、AIエージェントやRAGで扱いやすいメタデータを併置しています。

## 著者

{author_markdown(project)}

## AI協働ツール

{ai_collaborator_markdown(project)}

## レポート一覧

{chr(10).join(report_lines)}

## AIに読ませる場合

- まず [`llms.txt`](llms.txt) を読ませると、資料群の全体像と重要ファイルを短く把握できます。
- 続いて [`llms-full.md`](llms-full.md) を読ませると、各レポートの要約、テーマ、参照先をまとめて利用できます。
- 検索・RAG用途では [`metadata/chunks.jsonl`](metadata/chunks.jsonl) を使うと、見出し単位の分割済みテキストとして扱えます。
- 用語の揺れを抑えるには [`metadata/glossary.json`](metadata/glossary.json) を、図版を根拠付きで扱うには [`metadata/figures.json`](metadata/figures.json) を併用してください。
- 授業案、ワークショップ、サービス企画、根拠付き回答には [`prompts/`](prompts/) のプロンプトを利用できます。

## ライセンス

本文とメタデータは、特記がない限り `{project['license']}` で公開します。利用時は著者・出典を表示してください。
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")


def write_references(config: dict, references: dict[str, list[str]]) -> None:
    lines = ["# 参考文献・関連資料", ""]
    bib_lines = ["% References for AIとクリエイティブと教育", ""]
    for report in config["reports"]:
        refs = references.get(report["id"], [])
        lines.extend([f"## {report['title']}", ""])
        if not refs:
            lines.extend(["- 参考文献・関連資料は未抽出です。", ""])
            continue
        for idx, ref in enumerate(refs, 1):
            ref_id = f"{report['id']}-ref-{idx:02d}"
            lines.append(f"- [{ref_id}] {ref}")
            bib_lines.extend(
                [
                    f"@misc{{{ref_id},",
                    f"  title = {{{ref}}},",
                    f"  note = {{Extracted from {report['title']}}}",
                    "}",
                    "",
                ]
            )
        lines.append("")

    supplemental_path = ROOT / "config" / "supplemental_references.json"
    if supplemental_path.exists():
        supplemental = json.loads(supplemental_path.read_text(encoding="utf-8"))
        lines.extend([f"# {supplemental['title']}", ""])
        if supplemental.get("description"):
            lines.extend([supplemental["description"], ""])
        if supplemental.get("accessed"):
            lines.extend([f"調査日: {supplemental['accessed']}", ""])

        for section in supplemental.get("sections", []):
            lines.extend([f"## {section['title']}", ""])
            for item in section.get("items", []):
                citation = supplemental_citation(item)
                lines.append(f"- [{item['id']}] {citation}")
                if item.get("note"):
                    lines.append(f"  - 用途: {item['note']}")
                bib_lines.extend(
                    [
                        f"@misc{{{item['id']},",
                        f"  title = {{{citation}}},",
                        f"  url = {{{item['url']}}},",
                        f"  note = {{{item.get('note', '')}}}",
                        "}",
                        "",
                    ]
                )
            lines.append("")
    (ROOT / "references" / "references.md").write_text("\n".join(lines), encoding="utf-8")
    (ROOT / "references" / "references.bib").write_text("\n".join(bib_lines), encoding="utf-8")


def write_metadata(config: dict, abstracts: dict[str, str], chunks: list[dict]) -> None:
    project = config["project"]
    reports = []
    for report in config["reports"]:
        item = {k: report[k] for k in ["id", "title", "kind", "themes", "keywords", "output_md"]}
        item["authors"] = report_authors(report, project)
        item["audience"] = report_audience(report, project)
        item.update(report_ai_fields(report))
        item["abstract"] = abstracts.get(report["id"], "")
        reports.append(item)
    (ROOT / "metadata" / "reports.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    with (ROOT / "metadata" / "chunks.jsonl").open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")


def write_glossary() -> None:
    glossary = [
        {
            "term": "生成AI",
            "reading": "せいせいAI",
            "definition": "テキスト、画像、コードなどを生成するAI。各レポートでは、学習者の構想、検証、編集を支援する伴走者として位置づける。",
            "related_reports": ["00-overview", "03-digital-citizenship", "04-student-hackathon", "06-sf-prototyping"],
        },
        {
            "term": "情報可視化",
            "reading": "じょうほうかしか",
            "definition": "データや公開情報を地図、図表、タイムラインなどに変換し、関係性や偏りを読み解けるようにする方法。",
            "related_reports": ["01-information-visualization-osint", "05-digital-archive-ai"],
        },
        {
            "term": "OSINT",
            "reading": "おーしんと",
            "definition": "公開情報を収集、照合、検証して分析する手法。教育では根拠に基づく推論と説明責任を学ぶ題材になる。",
            "related_reports": ["01-information-visualization-osint", "03-digital-citizenship"],
        },
        {
            "term": "GIS",
            "reading": "じーあいえす",
            "definition": "地理情報を扱うシステムや方法。地域課題、災害、都市、文化資源などを空間的に分析する学習に使える。",
            "related_reports": ["01-information-visualization-osint"],
        },
        {
            "term": "AIカラー化",
            "reading": "えーあいからーか",
            "definition": "白黒写真にAIで色を付ける処理。平和教育では、復元の正確さだけでなく資料批判と記憶継承の対話を促す入口になる。",
            "related_reports": ["02-photo-colorization-peace-education", "05-digital-archive-ai"],
        },
        {
            "term": "デジタルシティズンシップ",
            "reading": "でじたるしてぃずんしっぷ",
            "definition": "デジタル技術のある社会で、情報を判断し、他者や公共性を考えながら参加する力。",
            "related_reports": ["03-digital-citizenship"],
        },
        {
            "term": "デジタルアーカイブ",
            "reading": "でじたるあーかいぶ",
            "definition": "資料をデジタル化して保存・公開・活用する仕組み。各レポートでは探究学習や資料再編集の基盤として扱う。",
            "related_reports": ["02-photo-colorization-peace-education", "05-digital-archive-ai"],
        },
        {
            "term": "ハッカソン",
            "reading": "はっかそん",
            "definition": "短期間で課題発見、アイデア創出、プロトタイプ制作、発表を行う実践形式。生成AI時代には発想と検証の比重が高まる。",
            "related_reports": ["04-student-hackathon", "06-sf-prototyping"],
        },
        {
            "term": "SFプロトタイピング",
            "reading": "えすえふぷろとたいぴんぐ",
            "definition": "未来社会の物語や世界観を作り、それを批判・修正しながら現在の選択肢を考える手法。",
            "related_reports": ["06-sf-prototyping", "04-student-hackathon"],
        },
        {
            "term": "RAG",
            "reading": "らぐ",
            "definition": "検索で取得した資料を根拠にAIが回答する仕組み。このリポジトリではmetadata/chunks.jsonlを主な検索単位として想定する。",
            "related_reports": ["00-overview"],
        },
    ]
    (ROOT / "metadata" / "glossary.json").write_text(json.dumps(glossary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_figures_metadata() -> None:
    figures = [
        {
            "id": "01-gis-education-examples",
            "report_id": "01-information-visualization-osint",
            "path": "assets/01-information-visualization-osint/gis-education-examples.jpg",
            "alt": "GIS・データ可視化を用いた学生作品例のコラージュ",
            "caption": "GIS・データ可視化を用いた学生作品例",
            "source": "ユーザー提供画像 GIS.jpg",
            "license_note": "出典・利用条件はプロジェクト管理者が確認する。",
            "related_sections": ["AIと情報可視化・OSINT教育"],
        },
        {
            "id": "02-the-day-color-returned",
            "report_id": "02-photo-colorization-peace-education",
            "path": "assets/02-photo-colorization-peace-education/the-day-color-returned.png",
            "alt": "写真集「あの日に色がさすとき」の表紙",
            "caption": "写真集「あの日に色がさすとき」表紙",
            "source": "ユーザー提供Wordファイルから抽出",
            "license_note": "出典・利用条件はプロジェクト管理者が確認する。",
            "related_sections": ["AIによるモノクロ写真カラー化を活かした高校生の平和教育実践"],
        },
        {
            "id": "02-presentation-scene",
            "report_id": "02-photo-colorization-peace-education",
            "path": "assets/02-photo-colorization-peace-education/presentation-scene.jpg",
            "alt": "長崎東高校の生徒による発表風景",
            "caption": "長崎東高校の生徒による発表風景",
            "source": "ユーザー提供Wordファイルから抽出",
            "license_note": "出典・利用条件はプロジェクト管理者が確認する。",
            "related_sections": ["AI時代の平和教育に向けて"],
        },
    ]
    (ROOT / "metadata" / "figures.json").write_text(json.dumps(figures, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_llms(config: dict, abstracts: dict[str, str]) -> None:
    project = config["project"]
    report_links = []
    supplemental_path = ROOT / "config" / "supplemental_references.json"
    supplemental_sections: list[str] = []
    if supplemental_path.exists():
        supplemental = json.loads(supplemental_path.read_text(encoding="utf-8"))
        supplemental_sections = [section["title"] for section in supplemental.get("sections", [])]
    full_sections = [
        f"# {project['title']}",
        "",
        f"> {project['description']}",
        "",
        "## 著者",
        "",
        author_markdown(project),
        "",
        "## AI協働ツール",
        "",
        ai_collaborator_markdown(project),
        "",
        "## 利用想定",
        "",
        *[f"- {aud}" for aud in project["audience"]],
        "",
        "## レポート概要",
        "",
    ]
    for report in config["reports"]:
        report_links.append(
            f"- [{report['title']}]({report['output_md']})（著者: {', '.join(report_authors(report, project))}）: {abstracts.get(report['id'], '')}"
        )
        full_sections.extend(
            [
                f"### {report['title']}",
                "",
                f"- ファイル: [`{report['output_md']}`]({report['output_md']})",
                f"- 著者: {', '.join(report_authors(report, project))}",
                f"- 想定読者: {', '.join(report_audience(report, project))}",
                f"- テーマ: {', '.join(report['themes'])}",
                f"- キーワード: {', '.join(report['keywords'])}",
                f"- 概要: {abstracts.get(report['id'], '')}",
                f"- 主要示唆: {' / '.join(report.get('key_takeaways', []))}",
                f"- 活用場面: {' / '.join(report.get('use_cases', []))}",
                f"- 学習活動案: {' / '.join(report.get('learning_activities', []))}",
                f"- 実装アイデア: {' / '.join(report.get('implementation_ideas', []))}",
                f"- 関連レポート: {', '.join(report.get('related_reports', []))}",
                f"- 引用メモ: {report.get('citation_note', '')}",
                "",
            ]
        )

    llms = f"""# {project['title']}

> {project['description']}

This repository publishes Markdown reports and AI-readable metadata for planning education practices and solutions around AI, creativity, information literacy, archives, prototyping, and digital citizenship.

## Authors

{author_markdown(project)}

## AI Collaborators

{ai_collaborator_markdown(project)}

## Core Reports

{chr(10).join(report_links)}

## AI Metadata

- [Full AI context](llms-full.md): Consolidated overview of all reports.
- [Report metadata](metadata/reports.json): Machine-readable report index.
- [Chunked corpus](metadata/chunks.jsonl): Section-level JSONL for retrieval and analysis.
- [Glossary](metadata/glossary.json): Terms and short definitions for AI/RAG grounding.
- [Figure metadata](metadata/figures.json): Captions, alt text, and source notes for visual assets.
- [References](references/references.md): Extracted references and related cases.
- [Supplemental references](references/references.md#追加推奨リファレンス): Curated references from web research covering {", ".join(supplemental_sections) if supplemental_sections else "AI education and creative learning"}.

## Optional

- [Build script](scripts/build_corpus.py): Converts local DOCX sources into Markdown and metadata.
- [Prompts](prompts/): Reusable prompts for lesson planning, service design, comparison, citation-aware answering, and implementation roadmaps.
"""
    (ROOT / "llms.txt").write_text(llms, encoding="utf-8")
    (ROOT / "llms-full.md").write_text("\n".join(full_sections), encoding="utf-8")


def write_prompts() -> None:
    prompts = {
        "idea-generation.md": """\
            # アイデア創出プロンプト

            あなたは教育実践と教育ソリューション設計の専門家です。このリポジトリの `llms.txt`、`llms-full.md`、`reports/`、`metadata/chunks.jsonl` を読み、次の観点で新しい企画案を提案してください。

            ## 入力条件

            - 対象: 教育機関、自治体、企業研修、EdTechサービスのいずれか
            - 学習者: 小学生、中高生、大学生、教員、社会人のいずれか
            - 重視するテーマ: 創造性、情報リテラシー、デジタルシティズンシップ、平和教育、未来構想、地域課題のいずれか

            ## 出力形式

            1. 企画名
            2. 背景となる課題
            3. 参照したレポートと示唆
            4. 学習活動またはサービス体験
            5. AIの役割
            6. 人間の判断が必要な点
            7. 実施上のリスクと対策
            8. 90日間の実装計画
            """,
        "planning-template.md": """\
            # 計画立案テンプレート

            ## 目的

            ## 対象者

            ## 参照するレポート

            ## 教育的価値

            ## 使用するAI・デジタル技術

            ## 実践またはサービスの流れ

            ## 評価方法

            ## 倫理・安全・著作権上の配慮

            ## 実装ロードマップ

            ## 必要なパートナー・資料・データ
            """,
        "lesson-plan-generation.md": """\
            # 授業案生成プロンプト

            `metadata/reports.json` と `metadata/chunks.jsonl` を根拠に、指定された学年・教科・時間数に合わせた授業案を作成してください。出典として利用したレポートID、チャンクID、図表IDを明記し、AIの利用場面と人間が判断する場面を分けてください。

            ## 出力形式

            1. 授業名
            2. 対象学年・教科
            3. 到達目標
            4. 参照レポートと根拠チャンク
            5. 時間配分
            6. 学習活動
            7. AI利用の役割
            8. 評価観点
            9. 倫理・著作権・安全上の配慮
            """,
        "workshop-design.md": """\
            # ワークショップ設計プロンプト

            `use_cases`、`learning_activities`、`implementation_ideas` を参照し、学校・自治体・企業研修のいずれかに向けた半日または1日のワークショップを設計してください。参加者の前提知識、必要な資料、ファシリテーション上の注意を含めてください。

            ## 出力形式

            1. ワークショップ名
            2. 対象者
            3. ねらい
            4. 使用するレポート
            5. タイムテーブル
            6. 個人活動・グループ活動
            7. 成果物
            8. リスクと対策
            """,
        "service-planning.md": """\
            # 教育サービス企画プロンプト

            あなたはEdTechサービスの企画担当者です。`metadata/reports.json` の想定読者、活用場面、実装アイデアをもとに、生成AI時代の教育サービス案を作成してください。機能の羅列ではなく、利用者の課題、学習体験、導入条件を中心に整理してください。

            ## 出力形式

            1. サービス名
            2. 対象ユーザー
            3. 解決する課題
            4. 根拠にしたレポート
            5. 主要機能
            6. 学習者・教員・管理者の体験
            7. 導入に必要なデータ・パートナー
            8. 評価指標
            9. 3か月の検証計画
            """,
        "cross-report-comparison.md": """\
            # レポート横断比較プロンプト

            `metadata/reports.json` と `metadata/chunks.jsonl` を使い、指定テーマについて複数レポートを比較してください。共通点、相違点、相互補完関係、未検討の論点を分け、必ずレポートIDとチャンクIDを添えてください。

            ## 出力形式

            1. 比較テーマ
            2. 対象レポート
            3. 共通する示唆
            4. レポートごとの差異
            5. 教育実践への応用
            6. 追加調査が必要な点
            """,
        "citation-answering.md": """\
            # 根拠付き回答プロンプト

            利用者の質問に対し、`metadata/chunks.jsonl`、`metadata/reports.json`、`metadata/figures.json`、`references/references.md` を根拠に回答してください。本文にないことは推測として明示し、出典としてレポートID、チャンクID、必要に応じて図表IDを示してください。

            ## 出力形式

            1. 回答
            2. 根拠
            3. 関連図表・参考文献
            4. 推測または未確認事項
            """,
        "implementation-roadmap.md": """\
            # 実装ロードマップ生成プロンプト

            指定された組織や授業テーマに対して、関連レポートの `implementation_ideas` と `learning_activities` を参照し、30日・90日・180日の実装ロードマップを作成してください。小さく始める検証、関係者の巻き込み、評価、公開・発信まで含めてください。

            ## 出力形式

            1. 実装目的
            2. 関連レポート
            3. 30日計画
            4. 90日計画
            5. 180日計画
            6. 必要な体制
            7. 評価指標
            8. リスクと対策
            """,
    }
    for filename, body in prompts.items():
        (ROOT / "prompts" / filename).write_text(textwrap.dedent(body), encoding="utf-8")


def build(config_path: Path) -> None:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    report_references_path = ROOT / "config" / "report_references.json"
    report_references = {}
    if report_references_path.exists():
        report_references = json.loads(report_references_path.read_text(encoding="utf-8"))
    report_replacements_path = ROOT / "config" / "report_replacements.json"
    report_replacements = {}
    if report_replacements_path.exists():
        report_replacements = json.loads(report_replacements_path.read_text(encoding="utf-8"))
    project = config["project"]
    abstracts: dict[str, str] = {}
    references: dict[str, list[str]] = {}
    all_chunks: list[dict] = []

    for folder in ["reports", "references", "metadata", "prompts", "assets"]:
        (ROOT / folder).mkdir(exist_ok=True)

    for report in config["reports"]:
        report["authors"] = report_authors(report, project)
        report["audience"] = report_audience(report, project)
        report["references"] = report_references.get(report["id"], [])
        source_docx = report.get("source_docx", f"source-docx/{report['id']}.docx")
        docx_path = ROOT / source_docx
        if not docx_path.exists():
            raise FileNotFoundError(f"Missing source DOCX: {docx_path}")
        blocks = parse_docx(docx_path, report["id"])
        markdown, refs, abstract = paragraph_to_markdown(blocks, report, project)
        for replacement in report_replacements.get(report["id"], []):
            markdown = markdown.replace(replacement["from"], replacement["to"])
        output_path = ROOT / report["output_md"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        abstracts[report["id"]] = abstract
        references[report["id"]] = refs
        all_chunks.extend(chunk_markdown(report, markdown))

    write_readme(config, abstracts)
    write_references(config, references)
    write_metadata(config, abstracts, all_chunks)
    write_glossary()
    write_figures_metadata()
    write_llms(config, abstracts)
    write_prompts()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Markdown and AI corpus files from DOCX reports.")
    parser.add_argument("--config", default="config/reports.json", help="Path to report configuration JSON.")
    args = parser.parse_args()
    build(ROOT / args.config)


if __name__ == "__main__":
    main()
