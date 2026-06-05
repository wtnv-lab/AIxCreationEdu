# 根拠付き回答プロンプト

利用者の質問に対し、`ai/system-instructions.md` の回答ルールに従い、`ai/rag/chunks.jsonl`、`ai/citations.json`、`metadata/report-sidecars/*.json`、`metadata/figures.json`、`reports/*.md` を根拠に回答してください。本文にないことは推測として明示し、出典としてレポートID、チャンクID、`evidence_refs`、必要に応じて図表IDを示してください。

回答の整理に迷う場合は、`concept_alignment.primary_stage_ids`、`supporting_stage_ids`、`literacy_ids` を補助線として使ってください。

## 出力形式

1. 回答
2. 根拠
3. concept_alignment_relation
4. 関連図表・参考文献
5. 推測または未確認事項
