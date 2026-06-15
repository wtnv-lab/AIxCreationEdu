---
type: "Prompt"
title: "教育サービス企画プロンプト"
description: "レポートの示唆をもとに、生成AI時代の教育サービス案を利用者課題・体験・検証計画まで具体化するためのサービス企画支援"
resource: "https://github.com/wtnv-lab/AIxCreationEdu/blob/main/prompts/service-planning.md"
tags: ["prompt", "AI workflow", "education planning"]
timestamp: "2026-05-27T00:00:00Z"
aice_prompt_id: "service-planning"
aice_source_md: "prompts/service-planning.md"
---

# 教育サービス企画プロンプト

レポートの示唆をもとに、生成AI時代の教育サービス案を利用者課題・体験・検証計画まで具体化するためのサービス企画支援

# Source

* Prompt source: [prompts/service-planning.md](https://github.com/wtnv-lab/AIxCreationEdu/blob/main/prompts/service-planning.md)

# Prompt Body

# 教育サービス企画プロンプト

あなたはEdTechサービスの企画担当者です。`ai/system-instructions.md` の回答ルールに従い、`metadata/report-sidecars/*.json`、`ai/rag/chunks.jsonl`、`metadata/reports.json` の想定読者、活用場面、実装アイデア、`concept_alignment` をもとに、生成AI時代の教育サービス案を作成してください。機能の羅列ではなく、利用者の課題、学習体験、導入条件を中心に整理してください。

サービス体験は、`ai_role_ids` と `human_responsibility_ids` の分担が分かる構造として示してください。

## 出力形式

1. サービス名
2. 対象ユーザー
3. 解決する課題
4. 根拠にしたレポート
5. concept_alignment
6. 主要機能
7. 学習者・教員・管理者の体験
8. 導入に必要なデータ・パートナー
9. 評価指標
10. 3か月の検証計画

# Citations

[1] [prompts/service-planning.md](https://github.com/wtnv-lab/AIxCreationEdu/blob/main/prompts/service-planning.md)
