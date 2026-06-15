---
type: "Prompt"
title: "レポート横断比較プロンプト"
description: "指定テーマについて複数レポートを比較し、共通点・差異・相互補完関係・教育実践への示唆を根拠付きで整理する横断比較支援"
resource: "https://github.com/wtnv-lab/AIxCreationEdu/blob/main/prompts/cross-report-comparison.md"
tags: ["prompt", "AI workflow", "education planning"]
timestamp: "2026-05-27T00:00:00Z"
aice_prompt_id: "cross-report-comparison"
aice_source_md: "prompts/cross-report-comparison.md"
---

# レポート横断比較プロンプト

指定テーマについて複数レポートを比較し、共通点・差異・相互補完関係・教育実践への示唆を根拠付きで整理する横断比較支援

# Source

* Prompt source: [prompts/cross-report-comparison.md](https://github.com/wtnv-lab/AIxCreationEdu/blob/main/prompts/cross-report-comparison.md)

# Prompt Body

# レポート横断比較プロンプト

`ai/system-instructions.md` の回答ルールに従い、`ai/rag/chunks.jsonl`、`metadata/report-sidecars/*.json`、`ai/citations.json` を使い、指定テーマについて複数レポートを比較してください。共通点、相違点、相互補完関係、未検討の論点を分け、必ずレポートID、チャンクID、`evidence_refs` を添えてください。

比較の軸には、各レポートの `concept_alignment` に含まれる `primary_stage_ids`、`literacy_ids`、`domain_tags` を含めてください。

## 出力形式

1. 比較テーマ
2. 対象レポート
3. 共通する示唆
4. レポートごとの差異
5. concept_alignment_comparison
6. 教育実践への応用
7. 追加調査が必要な点

# Citations

[1] [prompts/cross-report-comparison.md](https://github.com/wtnv-lab/AIxCreationEdu/blob/main/prompts/cross-report-comparison.md)
