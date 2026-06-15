---
type: "Prompt"
title: "ワークショップ設計プロンプト"
description: "学校・自治体・企業研修向けに、半日または1日のワークショップをタイムテーブルや成果物まで整理するための設計支援"
resource: "https://github.com/wtnv-lab/AIxCreationEdu/blob/main/prompts/workshop-design.md"
tags: ["prompt", "AI workflow", "education planning"]
timestamp: "2026-05-27T00:00:00Z"
aice_prompt_id: "workshop-design"
aice_source_md: "prompts/workshop-design.md"
---

# ワークショップ設計プロンプト

学校・自治体・企業研修向けに、半日または1日のワークショップをタイムテーブルや成果物まで整理するための設計支援

# Source

* Prompt source: [prompts/workshop-design.md](https://github.com/wtnv-lab/AIxCreationEdu/blob/main/prompts/workshop-design.md)

# Prompt Body

# ワークショップ設計プロンプト

`ai/system-instructions.md` の回答ルールに従い、`metadata/report-sidecars/*.json`、`ai/rag/chunks.jsonl` の `use_cases`、`learning_activities`、`implementation_ideas`、`concept_alignment` を参照し、学校・自治体・企業研修のいずれかに向けた半日または1日のワークショップを設計してください。参加者の前提知識、必要な資料、ファシリテーション上の注意を含めてください。

タイムテーブルは、`stage_id` 単位で対応が分かるようにしてください。

## 出力形式

1. ワークショップ名
2. 対象者
3. ねらい
4. 使用するレポート
5. concept_alignment
6. タイムテーブル
7. 個人活動・グループ活動
8. 成果物
9. リスクと対策

# Citations

[1] [prompts/workshop-design.md](https://github.com/wtnv-lab/AIxCreationEdu/blob/main/prompts/workshop-design.md)
