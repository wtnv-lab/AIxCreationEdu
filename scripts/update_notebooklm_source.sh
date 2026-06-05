#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

OUTPUT="ai/notebooklm-source.txt"
TMP_OUTPUT="$(mktemp)"
trap 'rm -f "$TMP_OUTPUT"' EXIT
mkdir -p "$(dirname "$OUTPUT")"

python3 - <<'PY'
import importlib.util
import sys

if importlib.util.find_spec("files_to_prompt") is None:
    sys.stderr.write(
        "files-to-prompt is not installed.\n"
        "Install it with: python3 -m pip install --user -r requirements/ai.txt\n"
    )
    sys.exit(1)
PY

cat > "$TMP_OUTPUT" <<'HEADER'
# AI Source Package: AIとクリエイティブと教育

## このファイルの目的

このファイルは、AI読解ツールや対話型生成AIに読み込ませるために、リポジトリ内の主要なテキスト資産を単一ファイルへ統合したものです。
ファイル名やディレクトリ構成だけの一覧ではありません。各ファイル名の直後に、そのファイルの具体的な本文・プロンプト・メタデータ・参考文献が続きます。

## AI読解ツールへの読み方

以降の各文書は、次の形式で並んでいます。

1. ファイルパス
2. 区切り線 `---`
3. そのファイルの全文またはテキスト内容
4. 区切り線 `---`

質問に答えるときは、ファイルパスだけで判断せず、区切り線の間にある本文を根拠として読んでください。
特に教育内容、平和学習、AI活用、授業案、ワークショップ案、サービス企画について答える場合は、`ai/system-instructions.md`、`ai/rag/chunks.jsonl`、`metadata/report-sidecars/*.json`、`reports/*.md`、`prompts/*.md`、`references/*` の本文を優先してください。
本文にないことは推測として扱い、根拠にしたファイルパスやレポート名を回答に含めてください。

## 含まれる主な内容

- `reports/*.md`: 各レポートの本文、参考文献、メタデータ
- `prompts/*.md`: 授業案、ワークショップ、サービス企画、比較、根拠付き回答などの具体的なプロンプト
- `ai/manifest.json`: AI向けパッケージ全体の索引
- `ai/system-instructions.md`: AIが読む順序、回答ルール、引用・推測の扱い
- `ai/context-brief.md` と `ai/context-full.md`: AI向けの短い概要と詳しい概要
- `ai/citations.json` と `ai/rag/chunks.jsonl`: 引用索引、根拠付きRAGチャンク
- `metadata/*.json`、`metadata/chunks.jsonl`、`metadata/report-sidecars/*.json`: レポート索引、概念スキーマ、検索用チャンク、図版メタデータ、用語集、レポート別sidecar
- `references/*`: 参考文献・関連資料
- `index.html` と `web/*`: ヒト向け閲覧アプリのHTML、CSS、JavaScript
- `README.md`、`ai/llms.txt`、`ai/llms-full.md`: プロジェクト概要とAI向け概説
- `config/*`: レポート定義や参照情報。過去の置換ログなど、読解用資料として紛らわしい補助ファイルは除外する。
- `scripts/*` と `.githooks/*`: この単一テキストの自動生成ルール

## 自動生成ルール

- この説明ブロックを必ず先頭に入れる。
- AI読解ツールが内容を見つけやすいよう、レポート全文とプロンプト全文をREADMEや設定ファイルより前に配置する。
- Markdownコードフェンスではなく、プレーンテキストの `files-to-prompt` 標準形式で出力する。
- 画像、動画、PDF、`.git`、生成ファイル自身は含めない。
- `reports/` 配下のMarkdownファイルをレポート本文の一次ソースとして扱う。
- `prompts/` 配下のMarkdownファイルをプロンプト本文の一次ソースとして扱う。
- `metadata/report-sidecars/` と `ai/rag/chunks.jsonl` はAI用の構造化補助として扱い、正本本文の代替にしない。

## ここから統合本文

HEADER

python3 -m files_to_prompt \
  reports \
  prompts \
  index.html \
  web \
  metadata \
  references \
  README.md \
  ai/manifest.json \
  ai/system-instructions.md \
  ai/context-brief.md \
  ai/context-full.md \
  ai/citations.json \
  ai/rag \
  ai/llms.txt \
  ai/llms-full.md \
  config \
  templates \
  assets/00-overview/project-concept-map.svg \
  assets/00-overview/data-package-flow.svg \
  scripts \
  .githooks \
  .gitignore \
  CITATION.cff \
  LICENSE \
  requirements/ai.txt \
  --include-hidden \
  --ignore ".git" \
  --ignore ".DS_Store" \
  --ignore "__pycache__" \
  --ignore "*.pyc" \
  --ignore "ai/notebooklm-source.txt" \
  --ignore "config/report_replacements.json" \
  --ignore "report_replacements.json" \
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
