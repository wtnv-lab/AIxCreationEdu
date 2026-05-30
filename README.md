# AIとクリエイティブと教育

> 生成AI時代の創造性、表現、情報リテラシー、教育実践を横断的に検討する公開レポート集。

このリポジトリは、教育関係者、研究者、自治体、教育ソリューション提供企業が、生成AI時代の教育実践を検討・設計・説明するための資料集です。人間が読みやすいレポート本文と、AIエージェント、NotebookLM、RAGで扱いやすいメタデータ、チャンク、プロンプトを併置しています。

このREADMEは、リポジトリ内のファイルを利用する人が目的に合うリソースを見つけやすくし、リポジトリごと読み込んだAIが構造、内容、利用法を理解しやすくするための入口です。

![AIとクリエイティブと教育の概念図](assets/00-overview/project-concept-map.svg)

*AIとクリエイティブと教育の概念図*

## レポート一覧

各レポートの一次ソースは [`reports/`](reports/) 配下のMarkdownファイルです。

| レポート | 主なテーマ | 使いどころ |
| --- | --- | --- |
| [AIとクリエイティブと教育 総括レポート](reports/00-overview.md) | 生成AI、創造性、教育実践、総括 | 全体方針、研修導入、横断的な論点整理 |
| [AIと情報可視化・OSINT教育](reports/01-information-visualization-osint.md) | 情報可視化、OSINT、探究学習、メディアリテラシー | 公開情報検証、データ可視化、調査型授業 |
| [AIによるモノクロ写真カラー化を活かした高校生の平和教育実践](reports/02-photo-colorization-peace-education.md) | 写真カラー化、平和教育、歴史学習、記憶継承 | 平和学習、資料批判、社会発信型プロジェクト |
| [AIを活かしたデジタルシティズンシップ教育](reports/03-digital-citizenship.md) | デジタルシティズンシップ、AIリテラシー、公共性 | AI利用ルール、情報倫理、市民性教育 |
| [AI時代の学生ハッカソン：実装の民主化と発想力への転換](reports/04-student-hackathon.md) | ハッカソン、プロトタイピング、発想力、実装支援 | 学生開発、PBL、アイデア実装型教育 |
| [デジタルアーカイブとAIを活かした教育実践](reports/05-digital-archive-ai.md) | デジタルアーカイブ、一次資料、教材共創 | アーカイブ活用、地域学習、教材開発 |
| [生成AIを用いたSFプロトタイピング](reports/06-sf-prototyping.md) | 未来構想、SFプロトタイピング、合意形成 | 未来ワークショップ、企業研修、政策構想 |
| [AIとMinecraft教育：遊びの空間を，記憶・創造・AIリテラシーの学びへ](reports/07-minecraft-ai-education.md) | Minecraft、記憶継承、創造、AIリテラシー | 仮想空間学習、地域再現、防災・平和教育 |

## まず使うファイル

| 目的 | 使うファイル | 内容 |
| --- | --- | --- |
| 人間が全体像を把握する | [`README.md`](README.md) | このリポジトリの構造、利用法、主要リソースの案内 |
| AIに短く全体像を渡す | [`ai/llms.txt`](ai/llms.txt) | AI向けの短い索引と重要ファイル一覧 |
| AIにレポート群の要約を渡す | [`ai/llms-full.md`](ai/llms-full.md) | 各レポートの要約、テーマ、利用想定、メタデータの統合版 |
| NotebookLMなどに丸ごと読ませる | [`ai/notebooklm-source.txt`](ai/notebooklm-source.txt) | レポート本文、プロンプト、メタデータ、参考文献をまとめた単一テキスト |
| レポート本文を読む、編集する | [`reports/`](reports/) | 各レポートの一次ソース。今後の本文更新はここを直接編集 |
| 授業案や企画案を生成する | [`prompts/`](prompts/) | 利用目的別のプロンプト例 |
| RAGや検索に使う | [`metadata/chunks.jsonl`](metadata/chunks.jsonl) | 見出し単位に分割した検索用チャンク |

## ディレクトリ構成

| パス | 役割 |
| --- | --- |
| [`ai/`](ai/) | AIやNotebookLMに渡す入口ファイル、統合テキスト、AI向け概説 |
| [`reports/`](reports/) | レポート本文の一次ソース |
| [`prompts/`](prompts/) | 授業案、企画案、比較、根拠付き回答などのプロンプト例 |
| [`metadata/`](metadata/) | 検索、RAG、AIエージェント向けの構造化データ |
| [`references/`](references/) | 参考文献・関連資料 |
| [`assets/`](assets/) | 図版・画像などの視覚資料 |
| [`config/`](config/) | レポート定義、参照情報、補助設定 |
| [`templates/`](templates/) | レポート作成時のテンプレート |
| [`scripts/`](scripts/) | NotebookLM向け単一テキストなどの更新スクリプト |
| [`.githooks/`](.githooks/) | 自動更新用のGitフック |
| [`requirements/`](requirements/) | AI向け生成処理に必要な依存関係 |

## このリポジトリでできること

- 生成AIが教育、創造性、平和学習、情報リテラシー、デジタルアーカイブ、未来構想に与える影響を横断的に理解する。
- 授業、探究学習、ワークショップ、教員研修、教育サービス企画の材料として使う。
- NotebookLMやChatGPTに読み込ませ、レポートに根拠を置いた授業案、企画案、比較表、ロードマップを作る。
- `metadata/chunks.jsonl`、`metadata/reports.json`、`metadata/concept-schema.json` を使って、検索、RAG、AIエージェント向けの知識ベースを組む。
- `prompts/` のプロンプトをそのまま使い、出典付き回答、授業案、サービス企画、アイデア発想を行う。

## プロンプト例

各プロンプトは [`prompts/`](prompts/) にあります。NotebookLMやChatGPTなどに `ai/notebooklm-source.txt`、`ai/llms.txt`、`metadata/`、`reports/` を読み込ませたうえで、目的に近いプロンプトを貼り付けて使ってください。

| プロンプト | 用途 |
| --- | --- |
| [授業案生成プロンプト](prompts/lesson-plan-generation.md) | 学年、教科、時間数に合わせた授業案を作成する |
| [ワークショップ設計プロンプト](prompts/workshop-design.md) | 学校、自治体、企業研修向けの半日または1日のワークショップを設計する |
| [教育サービス企画プロンプト](prompts/service-planning.md) | EdTechや教育ソリューションのサービス案を整理する |
| [アイデア創出プロンプト](prompts/idea-generation.md) | レポート群をもとに新しい授業、教材、サービス、活動案を発想する |
| [エクスカーション法アイデア創出プロンプト](prompts/excursion-ideation.md) | 遠い領域の特徴を借りて発想を広げる |
| [実装ロードマップ生成プロンプト](prompts/implementation-roadmap.md) | 30日、90日、180日の導入計画を作る |
| [レポート横断比較プロンプト](prompts/cross-report-comparison.md) | 複数レポートの共通点、差異、補完関係を比較する |
| [根拠付き回答プロンプト](prompts/citation-answering.md) | `metadata/chunks.jsonl` などを根拠に、出典付きで回答する |
| [計画立案テンプレート](prompts/planning-template.md) | 授業、研修、企画を手早く構造化するための空欄テンプレート |

## AIに読ませる場合

AIにリポジトリを読ませるときは、用途に応じて次の順で渡すと扱いやすくなります。

1. 全体像だけ必要な場合: [`ai/llms.txt`](ai/llms.txt)
2. レポート群の要約とテーマも必要な場合: [`ai/llms-full.md`](ai/llms-full.md)
3. NotebookLMなどで全文検索・質問応答をしたい場合: [`ai/notebooklm-source.txt`](ai/notebooklm-source.txt)
4. RAGや検索システムに組み込む場合: [`metadata/chunks.jsonl`](metadata/chunks.jsonl)
5. 出典や図版も扱う場合: [`references/references.md`](references/references.md)、[`metadata/figures.json`](metadata/figures.json)

AIには、たとえば次のように指示してください。

```text
この資料群は「AIとクリエイティブと教育」に関するレポート集です。
回答では reports/ の本文、metadata/chunks.jsonl、references/ を根拠にし、本文にないことは推測として明示してください。
授業案や企画案を作る場合は prompts/ の該当プロンプトの形式に従ってください。
```

## メタデータと検索用データ

| ファイル | 役割 |
| --- | --- |
| [`metadata/reports.json`](metadata/reports.json) | レポートID、タイトル、概要、著者、想定読者、テーマ、活用場面などの機械可読索引 |
| [`metadata/chunks.jsonl`](metadata/chunks.jsonl) | レポート本文を見出し単位に分割した検索・RAG用データ |
| [`metadata/concept-schema.json`](metadata/concept-schema.json) | `concept_alignment` の固定語彙と分類軸 |
| [`metadata/glossary.json`](metadata/glossary.json) | 用語の揺れを抑えるための用語集 |
| [`metadata/figures.json`](metadata/figures.json) | 図版のキャプション、代替テキスト、出典メモ |
| [`references/references.md`](references/references.md) | レポート別の参考文献・関連資料 |
| [`references/references.bib`](references/references.bib) | BibTeX形式の参考文献 |

## NotebookLM向け単一テキスト

[`ai/notebooklm-source.txt`](ai/notebooklm-source.txt) は、NotebookLMなどにリポジトリ全体を読み込ませるための単一テキストです。画像、動画、PDF、`.git`、生成ファイル自身を除外し、レポート本文、プロンプト、メタデータ、参考文献をまとめています。

NotebookLMが内容を見つけやすいよう、生成時には次のルールを維持します。

- 冒頭に、このファイルの目的と読み方を説明する。
- `reports/` のレポート本文を前方に配置する。
- `prompts/` の具体的なプロンプト本文を前方に配置する。
- `files-to-prompt` の標準形式で、ファイルパス、区切り線、本文の順に出力する。
- ファイル構成だけの一覧にならないよう、各ファイル本文を必ず含める。

更新する場合は次を実行します。

```sh
python3 -m pip install --user -r requirements/ai.txt
scripts/update_notebooklm_source.sh
```

このリポジトリでは Git フックを `.githooks/` に置いています。次のコマンドを一度実行すると、コミット前、マージ後、ブランチ切り替え後に `ai/notebooklm-source.txt` が自動更新されます。

```sh
scripts/setup_git_hooks.sh
```

## 編集と更新のルール

- レポート本文は [`reports/`](reports/) 配下の `.md` を直接編集します。
- プロンプト例は [`prompts/`](prompts/) 配下の `.md` を直接編集します。
- Wordファイルからレポートを再生成する仕組みは使いません。
- READMEを更新したら、必要に応じて `scripts/update_notebooklm_source.sh` を実行し、`ai/notebooklm-source.txt` に反映してください。
- 図版やメタデータを追加した場合は、`metadata/figures.json`、`metadata/reports.json`、`metadata/chunks.jsonl` との整合を確認してください。

## ライセンス

本文とメタデータは、特記がない限り `CC BY 4.0` で公開します。利用時は著者・出典を表示してください。

## 著者・クレジット

### 東京大学 大学院情報学環・学際情報学府

- 教授 [渡邉英徳](https://researchmap.jp/hwtnv)
- 特任准教授 [原田真喜子](https://researchmap.jp/kokima)（都留文科大学 地域交流研究センター 特任講師）
- 博士後期課程 [小松尚平](https://researchmap.jp/komanbe)
- 博士後期課程 [片山実咲](https://researchmap.jp/misaki_katayama)
- 博士後期課程 [楊欽](https://researchmap.jp/kevinyang)
- 博士後期課程 [森吉蓉子](https://researchmap.jp/ymoriyos)

### 同志社大学 文化情報学府

- 准教授 [大井将生](https://researchmap.jp/m-oi)

### AI協働ツール

- ChatGPT（OpenAI）: GPT-5.5
- Gemini（Google）: Gemini 3.1 Pro
- Codex（OpenAI）: GPT-5.5
- GitHub Copilot（GitHub）: GPT-5.5
