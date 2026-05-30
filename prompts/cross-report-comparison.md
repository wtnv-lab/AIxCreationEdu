# レポート横断比較プロンプト

`metadata/reports.json` と `metadata/chunks.jsonl` を使い、指定テーマについて複数レポートを比較してください。共通点、相違点、相互補完関係、未検討の論点を分け、必ずレポートIDとチャンクIDを添えてください。

比較の軸には、各レポートの `concept_alignment` に含まれる `primary_stage_ids`、`literacy_ids`、`domain_tags` を含めてください。

## 出力形式

1. 比較テーマ
2. 対象レポート
3. 共通する示唆
4. レポートごとの差異
5. concept_alignment_comparison
6. 教育実践への応用
7. 追加調査が必要な点
