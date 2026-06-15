---
type: "Prompt"
title: "根拠付き回答プロンプト"
description: "利用者の質問に対して、レポート本文・メタデータ・図表・参考文献を根拠に、出典付きで回答するための根拠確認支援"
resource: "https://github.com/wtnv-lab/AIxCreationEdu/blob/main/prompts/citation-answering.md"
tags: ["prompt", "AI workflow", "education planning"]
timestamp: "2026-05-27T00:00:00Z"
aice_prompt_id: "citation-answering"
aice_source_md: "prompts/citation-answering.md"
---

# 根拠付き回答プロンプト

利用者の質問に対して、レポート本文・メタデータ・図表・参考文献を根拠に、出典付きで回答するための根拠確認支援

# Source

* Prompt source: [prompts/citation-answering.md](https://github.com/wtnv-lab/AIxCreationEdu/blob/main/prompts/citation-answering.md)

# Prompt Body

# 根拠付き回答プロンプト

利用者の質問に対し、`ai/system-instructions.md` の回答ルールに従い、`ai/rag/chunks.jsonl`、`ai/citations.json`、`metadata/report-sidecars/*.json`、`metadata/figures.json`、`reports/*.md` を根拠に回答してください。本文にないことは推測として明示し、出典としてレポートID、チャンクID、`evidence_refs`、必要に応じて図表IDを示してください。

回答の整理に迷う場合は、`concept_alignment.primary_stage_ids`、`supporting_stage_ids`、`literacy_ids` を補助線として使ってください。

## 出力形式

1. 回答
2. 根拠
3. concept_alignment_relation
4. 関連図表・参考文献
5. 推測または未確認事項

# Citations

[1] [prompts/citation-answering.md](https://github.com/wtnv-lab/AIxCreationEdu/blob/main/prompts/citation-answering.md)
