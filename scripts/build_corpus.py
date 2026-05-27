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


def frontmatter(report: dict, project: dict) -> str:
    lines = [
        "---",
        f'id: "{report["id"]}"',
        f'title: "{report["title"]}"',
        f'project: "{project["title"]}"',
        f'date: "{project["date"]}"',
        f'version: "{project["version"]}"',
        f'kind: "{report["kind"]}"',
        "audience:",
        yaml_list(project["audience"]),
        "authors:",
    ]
    for group in project.get("authors", []):
        lines.append(f'  - affiliation: "{group["affiliation"]}"')
        lines.append("    members:")
        lines.append(yaml_list(group.get("members", []), indent=6))
    lines.extend(
        [
            "ai_collaborators:",
        ]
    )
    for tool in project.get("ai_collaborators", []):
        lines.append(f'  - name: "{tool["name"]}"')
        lines.append(f'    version: "{tool["version"]}"')
        lines.append(f'    provider: "{tool["provider"]}"')
    lines.extend(
        [
            "themes:",
            yaml_list(report["themes"]),
            "keywords:",
            yaml_list(report["keywords"]),
            f'license: "{project["license"]}"',
            f'source_docx: "../{report["source_docx"]}"',
            "---",
            "",
        ]
    )
    return "\n".join(lines)


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
    lines: list[str] = [frontmatter(report, project), f"# {report['title']}", ""]
    references: list[str] = []
    abstract_parts: list[str] = []
    saw_title = False
    in_references = False

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
            if not in_references:
                lines.extend(["## 参考文献・関連資料", ""])
            in_references = True
            continue

        stripped = re.sub(r"^[・•●○]\s*", "", normalized)
        if in_references:
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

    abstract = clean_text(" ".join(abstract_parts))
    if len(abstract) > 220:
        abstract = abstract[:220].rstrip() + "..."
    return "\n".join(lines).strip() + "\n", references, abstract


def chunk_markdown(report: dict, markdown: str, max_chars: int = 1200) -> list[dict]:
    chunks: list[dict] = []
    current_heading = report["title"]
    current_lines: list[str] = []

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
                    "themes": report["themes"],
                    "keywords": report["keywords"],
                    "text": text,
                    "source": report["output_md"],
                }
            )
        current_lines = []

    in_frontmatter = False
    for line in markdown.splitlines():
        if line == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
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


def write_readme(config: dict, abstracts: dict[str, str]) -> None:
    project = config["project"]
    report_lines = []
    for report in config["reports"]:
        report_lines.append(f"- [{report['title']}]({report['output_md']}): {abstracts.get(report['id'], '')}")

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

## Word原稿から再生成する

Word原稿は [`source-docx/`](source-docx/) に置きます。差し替えや追加をした後、[`config/reports.json`](config/reports.json) を更新し、次を実行してください。

```bash
python3 scripts/build_corpus.py
```

生成される主なファイルは次の通りです。

- `reports/*.md`: 公開用Markdownレポート
- `references/references.md`: レポート別の参考文献・関連資料リスト
- `metadata/reports.json`: レポート単位の機械可読メタデータ
- `metadata/chunks.jsonl`: AI検索・RAG向けのチャンクデータ
- `llms.txt`: AIエージェント向けの入口
- `llms-full.md`: AI投入用の統合概要

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
                lines.append(f"- [{item['id']}] [{item['title']}]({item['url']})")
                if item.get("note"):
                    lines.append(f"  - 用途: {item['note']}")
                bib_lines.extend(
                    [
                        f"@misc{{{item['id']},",
                        f"  title = {{{item['title']}}},",
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
        item = {k: report[k] for k in ["id", "title", "kind", "themes", "keywords", "output_md", "source_docx"]}
        item["abstract"] = abstracts.get(report["id"], "")
        item["authors"] = project.get("authors", [])
        item["ai_collaborators"] = project.get("ai_collaborators", [])
        reports.append(item)
    (ROOT / "metadata" / "reports.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    with (ROOT / "metadata" / "chunks.jsonl").open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")


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
        report_links.append(f"- [{report['title']}]({report['output_md']}): {abstracts.get(report['id'], '')}")
        full_sections.extend(
            [
                f"### {report['title']}",
                "",
                f"- ファイル: [`{report['output_md']}`]({report['output_md']})",
                f"- テーマ: {', '.join(report['themes'])}",
                f"- キーワード: {', '.join(report['keywords'])}",
                f"- 概要: {abstracts.get(report['id'], '')}",
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
- [References](references/references.md): Extracted references and related cases.
- [Supplemental references](references/references.md#追加推奨リファレンス): Curated references from web research covering {", ".join(supplemental_sections) if supplemental_sections else "AI education and creative learning"}.

## Optional

- [Source DOCX files](source-docx/): Editable Word originals for regeneration.
- [Build script](scripts/build_corpus.py): Converts DOCX sources into Markdown and metadata.
"""
    (ROOT / "llms.txt").write_text(llms, encoding="utf-8")
    (ROOT / "llms-full.md").write_text("\n".join(full_sections), encoding="utf-8")


def write_prompts() -> None:
    (ROOT / "prompts" / "idea-generation.md").write_text(
        textwrap.dedent(
            """\
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
            """
        ),
        encoding="utf-8",
    )
    (ROOT / "prompts" / "planning-template.md").write_text(
        textwrap.dedent(
            """\
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
            """
        ),
        encoding="utf-8",
    )


def build(config_path: Path) -> None:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    project = config["project"]
    abstracts: dict[str, str] = {}
    references: dict[str, list[str]] = {}
    all_chunks: list[dict] = []

    for folder in ["reports", "references", "metadata", "prompts", "assets"]:
        (ROOT / folder).mkdir(exist_ok=True)

    for report in config["reports"]:
        docx_path = ROOT / report["source_docx"]
        if not docx_path.exists():
            raise FileNotFoundError(f"Missing source DOCX: {docx_path}")
        blocks = parse_docx(docx_path, report["id"])
        markdown, refs, abstract = paragraph_to_markdown(blocks, report, project)
        output_path = ROOT / report["output_md"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        abstracts[report["id"]] = abstract
        references[report["id"]] = refs
        all_chunks.extend(chunk_markdown(report, markdown))

    write_readme(config, abstracts)
    write_references(config, references)
    write_metadata(config, abstracts, all_chunks)
    write_llms(config, abstracts)
    write_prompts()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Markdown and AI corpus files from DOCX reports.")
    parser.add_argument("--config", default="config/reports.json", help="Path to report configuration JSON.")
    args = parser.parse_args()
    build(ROOT / args.config)


if __name__ == "__main__":
    main()
