# AI System Instructions: AIとクリエイティブと教育

このファイルは、AIが本リポジトリを読むときの優先順位と禁止事項を定める。

## 読む順序

1. `ai/manifest.json` で利用可能なAI向けファイルを把握する。
2. 全体像は `ai/context-brief.md` を読む。
3. 詳細な根拠は `metadata/report-sidecars/*.json` と `ai/rag/chunks.jsonl` を読む。
4. 人間向けの正本確認が必要な場合は `reports/*.md` を読む。
5. 出典確認は `ai/citations.json` と `references/references.md` を使う。

## 回答ルール

- 本文・メタデータ・参考文献にないことは、推測として明示する。
- 授業案、研修案、サービス企画を出す場合は、根拠にした `report_id` と `evidence_refs` を示す。
- AI出力を完成版として扱わず、人間による検証・編集が必要であることを前提にする。
- 図版について述べる場合は、画像パスだけでなく `metadata/figures.json` の `alt`、`caption`、`license_note` を確認する。
- プロジェクト概要ではAIサービスの商品名を出さず、必要な場合は「対話型生成AI」「AI読解ツール」「コード生成支援AI」などの一般名詞で述べる。
- レポート本文・参考文献に含まれる固有名詞は、出典や事例の正確性に関わるため、一般化せず出典として扱う。

## 重要な制約

- `reports/*.md` が人間向けHTML版の本文正本である。
- `metadata/report-sidecars/*.json` はAI用の構造化補助であり、本文の代替ではない。
- `ai/rag/chunks.jsonl` は検索・RAG用であり、チャンク単体で結論を断定しない。
- `ai/notebooklm-source.txt` は単一テキスト読解ツール向けの互換パッケージである。
