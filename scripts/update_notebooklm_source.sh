#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

OUTPUT="notebooklm-source.txt"
TMP_OUTPUT="$(mktemp)"
trap 'rm -f "$TMP_OUTPUT"' EXIT

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

cat > "$TMP_OUTPUT" <<'HEADER'
# NotebookLM Source: AIとクリエイティブと教育

## このファイルの目的

このファイルは、NotebookLMなどのAI読解ツールに読み込ませるために、リポジトリ内の主要なテキスト資産を単一ファイルへ統合したものです。
ファイル名やディレクトリ構成だけの一覧ではありません。各ファイル名の直後に、そのファイルの具体的な本文・プロンプト・メタデータ・参考文献が続きます。

## NotebookLMへの読み方

以降の各文書は、次の形式で並んでいます。

1. ファイルパス
2. 区切り線 `---`
3. そのファイルの全文またはテキスト内容
4. 区切り線 `---`

質問に答えるときは、ファイルパスだけで判断せず、区切り線の間にある本文を根拠として読んでください。
特に教育内容、平和学習、AI活用、授業案、ワークショップ案、サービス企画について答える場合は、`reports/*.md`、`prompts/*.md`、`metadata/*.json`、`references/*` の本文を優先してください。
本文にないことは推測として扱い、根拠にしたファイルパスやレポート名を回答に含めてください。

## 含まれる主な内容

- `reports/*.md`: 各レポートの本文、参考文献、メタデータ
- `prompts/*.md`: 授業案、ワークショップ、サービス企画、比較、根拠付き回答などの具体的なプロンプト
- `metadata/*.json` と `metadata/chunks.jsonl`: レポート索引、概念スキーマ、検索用チャンク、図版メタデータ、用語集
- `references/*`: 参考文献・関連資料
- `README.md`、`llms.txt`、`llms-full.md`: プロジェクト概要とAI向け概説
- `config/*`: レポート定義や参照情報
- `scripts/*` と `.githooks/*`: この単一テキストの自動生成ルール

## 自動生成ルール

- この説明ブロックを必ず先頭に入れる。
- NotebookLMが内容を見つけやすいよう、レポート全文とプロンプト全文をREADMEや設定ファイルより前に配置する。
- Markdownコードフェンスではなく、プレーンテキストの `files-to-prompt` 標準形式で出力する。
- 画像、動画、PDF、`.git`、生成ファイル自身は含めない。
- `reports/` 配下のMarkdownファイルをレポート本文の一次ソースとして扱う。
- `prompts/` 配下のMarkdownファイルをプロンプト本文の一次ソースとして扱う。

## ここから統合本文

HEADER

python3 -m files_to_prompt \
  reports \
  prompts \
  metadata \
  references \
  README.md \
  llms.txt \
  llms-full.md \
  config \
  templates \
  assets/00-overview/project-concept-map.svg \
  scripts \
  .githooks \
  .gitignore \
  CITATION.cff \
  LICENSE \
  requirements-ai.txt \
  --include-hidden \
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
  >> "$TMP_OUTPUT"

mv "$TMP_OUTPUT" "$OUTPUT"
chmod 0644 "$OUTPUT"
