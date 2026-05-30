# 授業案生成プロンプト

`metadata/reports.json` と `metadata/chunks.jsonl` を根拠に、指定された学年・教科・時間数に合わせた授業案を作成してください。出典として利用したレポートID、チャンクID、図表IDを明記し、AIの利用場面と人間が判断する場面を分けてください。

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
