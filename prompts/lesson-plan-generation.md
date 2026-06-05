# 授業案生成プロンプト

`ai/system-instructions.md` の回答ルールに従い、`ai/rag/chunks.jsonl`、`metadata/report-sidecars/*.json`、`metadata/reports.json` を根拠に、指定された学年・教科・時間数に合わせた授業案を作成してください。出典として利用したレポートID、チャンクID、`evidence_refs`、図表IDを明記し、AIの利用場面と人間が判断する場面を分けてください。重要な判断は `reports/*.md` の本文正本で確認してください。

授業の流れは、各レポートの `concept_alignment.primary_stage_ids`、`supporting_stage_ids`、`human_responsibility_ids` を参照して組み立ててください。

## 出力形式

1. 授業名
2. 対象学年・教科
3. 到達目標
4. 参照レポートと根拠チャンク
5. concept_alignment
6. 時間配分
7. 学習活動
8. AI利用の役割
9. 評価観点
10. 倫理・著作権・安全上の配慮
