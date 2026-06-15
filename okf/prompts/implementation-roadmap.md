---
type: "Prompt"
title: "実装ロードマップ生成プロンプト"
description: "授業・研修・企画を実行へ移すために、30日・90日・180日のロードマップと体制・評価・リスクを整理する実装計画支援"
resource: "https://github.com/wtnv-lab/AIxCreationEdu/blob/main/prompts/implementation-roadmap.md"
tags: ["prompt", "AI workflow", "education planning"]
timestamp: "2026-05-27T00:00:00Z"
aice_prompt_id: "implementation-roadmap"
aice_source_md: "prompts/implementation-roadmap.md"
---

# 実装ロードマップ生成プロンプト

授業・研修・企画を実行へ移すために、30日・90日・180日のロードマップと体制・評価・リスクを整理する実装計画支援

# Source

* Prompt source: [prompts/implementation-roadmap.md](https://github.com/wtnv-lab/AIxCreationEdu/blob/main/prompts/implementation-roadmap.md)

# Prompt Body

# 実装ロードマップ生成プロンプト

指定された組織や授業テーマに対して、`ai/system-instructions.md` の回答ルールに従い、`metadata/report-sidecars/*.json`、`ai/rag/chunks.jsonl`、`metadata/reports.json` から関連レポートの `implementation_ideas`、`learning_activities`、`concept_alignment` を参照し、30日・90日・180日の実装ロードマップを作成してください。小さく始める検証、関係者の巻き込み、評価、公開・発信まで含めてください。

ロードマップは、`primary_stage_ids` と `human_responsibility_ids` を明示し、AIに任せる部分・人間が責任を持つ部分を分けてください。

## 出力形式

1. 実装目的
2. 関連レポート
3. concept_alignment
4. 30日計画
5. 90日計画
6. 180日計画
7. 必要な体制
8. 評価指標
9. リスクと対策

# Citations

[1] [prompts/implementation-roadmap.md](https://github.com/wtnv-lab/AIxCreationEdu/blob/main/prompts/implementation-roadmap.md)
