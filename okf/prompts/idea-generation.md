---
type: "Prompt"
title: "アイデア創出プロンプト"
description: "対象者やテーマに応じて、リポジトリ内の知見を横断し、新しい授業・研修・サービス企画の種を提案するためのアイデア創出支援"
resource: "https://github.com/wtnv-lab/AIxCreationEdu/blob/main/prompts/idea-generation.md"
tags: ["prompt", "AI workflow", "education planning"]
timestamp: "2026-05-27T00:00:00Z"
aice_prompt_id: "idea-generation"
aice_source_md: "prompts/idea-generation.md"
---

# アイデア創出プロンプト

対象者やテーマに応じて、リポジトリ内の知見を横断し、新しい授業・研修・サービス企画の種を提案するためのアイデア創出支援

# Source

* Prompt source: [prompts/idea-generation.md](https://github.com/wtnv-lab/AIxCreationEdu/blob/main/prompts/idea-generation.md)

# Prompt Body

# アイデア創出プロンプト

あなたは教育実践と教育ソリューション設計の専門家です。このリポジトリの `ai/system-instructions.md`、`ai/context-brief.md`、`ai/context-full.md`、`ai/rag/chunks.jsonl`、`metadata/report-sidecars/*.json`、`metadata/reports.json` を読み、次の観点で新しい企画案を提案してください。重要な根拠は `reports/*.md` の本文正本で確認してください。

提案は、各レポートの `concept_alignment.primary_stage_ids`、`supporting_stage_ids`、`literacy_ids` に沿って整理してください。

## 入力条件

- 対象: 教育機関、自治体、企業研修、EdTechサービスのいずれか
- 学習者: 小学生、中高生、大学生、教員、社会人のいずれか
- 重視するテーマ: 創造性、情報リテラシー、デジタルシティズンシップ、平和教育、未来構想、地域課題のいずれか

## 出力形式

1. 企画名
2. 背景となる課題
3. 参照したレポートと示唆
4. concept_alignment
5. 学習活動またはサービス体験
6. AIの役割
7. 人間の判断が必要な点
8. 実施上のリスクと対策
9. 90日間の実装計画

# Citations

[1] [prompts/idea-generation.md](https://github.com/wtnv-lab/AIxCreationEdu/blob/main/prompts/idea-generation.md)
