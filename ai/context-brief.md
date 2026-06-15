# AI Context Brief: AIとクリエイティブと教育

## プロジェクト概要

生成AI時代の創造性教育を、問い・資料読解・制作・検証・社会発信をつなぐ学びとして整理する公開プロジェクト。
人間向けにはMarkdownレポートとHTML閲覧アプリを、AI向けには構造化メタデータ、RAGチャンク、引用対応、用途別プロンプトを提供する。

## AIに渡すときの最短ルート

1. この `ai/context-brief.md` で全体像を把握する。
2. `ai/system-instructions.md` の回答ルールを守る。
3. 根拠が必要な回答では `ai/rag/chunks.jsonl` と `ai/citations.json` を使う。
4. 重要な判断では `reports/*.md` の本文を確認する。
5. 他のエージェントや組織へ交換する場合は `okf/index.md` を入口にする。

## レポート一覧

### 00-overview: AIとクリエイティブと教育 総括レポート

- 要旨: 生成AI時代の教育を、問い・資料読解・制作・検証・社会発信をつなぐ創造性教育として整理。
- 著者: 渡邉英徳
- 主なテーマ: 生成AI, 創造性, 教育実践, 総括
- 想定読者: 生成AI時代の教育方針を検討する学校管理職・教育委員会担当者, AI・創造性・情報リテラシーを横断するカリキュラム設計者, 教育ソリューションやEdTechサービスの企画担当者, AIと教育実践の全体像を把握したい研究者・実践者
- 正本: `reports/00-overview.md`
- AI sidecar: `metadata/report-sidecars/00-overview.json`
- OKF concept: `okf/reports/00-overview.md`

### 01-information-visualization-osint: AIと情報可視化・OSINT教育

- 要旨: GIS・データ可視化・OSINTを通じて、公開情報を観測・検証・物語化・発信・更新する情報メディア教育モデル。
- 著者: 渡邉英徳
- 主なテーマ: 生成AI, 情報可視化, OSINT, 探究学習
- 想定読者: 情報・メディア・探究学習を担当する高校・大学教員, データ可視化、GIS、デジタルアーカイブを授業に取り入れたい教育者, OSINTや調査報道の基礎を教育・研修化したい報道関係者, 公開情報の検証と社会的説明を扱う教材・サービス企画者
- 正本: `reports/01-information-visualization-osint.md`
- AI sidecar: `metadata/report-sidecars/01-information-visualization-osint.json`
- OKF concept: `okf/reports/01-information-visualization-osint.md`

### 02-photo-colorization-peace-education: AIによるモノクロ写真カラー化を活かした高校生の平和教育実践

- 要旨: AIカラー化を、写真資料・証言・地域の記憶をつなぐ平和教育と記憶継承の探究へ展開。
- 著者: 森吉蓉子, 渡邉英徳
- 主なテーマ: 生成AI, 写真カラー化, 平和教育, 歴史学習
- 想定読者: 平和教育・歴史教育・地域学習を担当する中学・高校教員, 写真資料や証言を活用する博物館・資料館・地域アーカイブ担当者, AIカラー化を探究学習や記憶継承に活かしたい教育実践者, 生徒の成果発信や社会連携型プロジェクトを支援する担当者
- 正本: `reports/02-photo-colorization-peace-education.md`
- AI sidecar: `metadata/report-sidecars/02-photo-colorization-peace-education.json`
- OKF concept: `okf/reports/02-photo-colorization-peace-education.md`

### 03-digital-citizenship: AIを活かしたデジタルシティズンシップ教育

- 要旨: AIの禁止・管理を超え、判断・参加・公共性を育てるデジタルシティズンシップ教育。
- 著者: 原田真喜子
- 主なテーマ: 生成AI, デジタルシティズンシップ, AIリテラシー, 情報モラル
- 想定読者: 小中高の情報活用能力・情報モラル・ICT活用を担当する教員, デジタルシティズンシップ教育のカリキュラム設計者, 生成AI利用ルールや校内研修を設計する学校管理職・ICT担当者, AIリテラシー教材や安全な学習環境を開発する教育サービス担当者
- 正本: `reports/03-digital-citizenship.md`
- AI sidecar: `metadata/report-sidecars/03-digital-citizenship.json`
- OKF concept: `okf/reports/03-digital-citizenship.md`

### 04-student-hackathon: AI時代の学生ハッカソン：実装の民主化と発想力への転換

- 要旨: 生成AIで実装負荷が下がる時代の学生ハッカソンを、課題設定と発想力の学びとして再定義。
- 著者: 小松尚平, 渡邉英徳
- 主なテーマ: 生成AI, ハッカソン, プロトタイピング, 実装教育
- 想定読者: 大学・高専・高校でハッカソンやPBLを運営する教職員, AIを用いたプロトタイピング教育を設計するメンター・ファシリテーター, 学生起業、地域課題解決、産学連携プログラムの企画担当者, 生成AI時代の開発教育や創造性評価に関心を持つ実践者
- 正本: `reports/04-student-hackathon.md`
- AI sidecar: `metadata/report-sidecars/04-student-hackathon.json`
- OKF concept: `okf/reports/04-student-hackathon.md`

### 05-digital-archive-ai: デジタルアーカイブとAIを活かした教育実践

- 要旨: デジタルアーカイブと生成AIを組み合わせ、一次資料を用いた探究と社会発信を支える教育実践。
- 著者: 大井将生
- 主なテーマ: 生成AI, デジタルアーカイブ, 教育実践, 資料活用
- 想定読者: 学校教育で一次資料や地域資料を活用したい教員, デジタルアーカイブの教育利用を進める図書館・博物館・自治体担当者, 探究学習、キュレーション授業、教材アーカイブを設計する教育者, AIと資料検索・要約・再編集を組み合わせた学習サービス企画者
- 正本: `reports/05-digital-archive-ai.md`
- AI sidecar: `metadata/report-sidecars/05-digital-archive-ai.json`
- OKF concept: `okf/reports/05-digital-archive-ai.md`

### 06-sf-prototyping: 生成AIを用いたSFプロトタイピング

- 要旨: 生成AIで未来シナリオを素早く仮設し、人間が批判・修正するSFプロトタイピングの教育活用。
- 著者: 楊欽, 渡邉英徳
- 主なテーマ: 生成AI, SFプロトタイピング, 未来構想, 創造性教育
- 想定読者: 未来構想・探究学習・創造性教育を担当する大学・高校教員, 産学協創、企業研修、ワークショップを設計するファシリテーター, 新規事業開発やビジョン策定にSFプロトタイピングを使いたい企画担当者, 生成AIを用いた物語生成・合意形成・アイデア創出に関心を持つ実践者
- 正本: `reports/06-sf-prototyping.md`
- AI sidecar: `metadata/report-sidecars/06-sf-prototyping.json`
- OKF concept: `okf/reports/06-sf-prototyping.md`

### 07-minecraft-ai-education: AIとMinecraft教育：遊びの空間を，記憶・創造・AIリテラシーの学びへ

- 要旨: MinecraftとAIを、記憶継承・地域学習・創造・AIリテラシーを横断する学習空間として整理。
- 著者: 片山実咲, 渡邉英徳
- 主なテーマ: 生成AI, Minecraft, ゲームベース学習, AIリテラシー, 記憶継承
- 想定読者: Minecraft Educationやゲームベース学習を授業に取り入れたい小中高・大学教員, 平和教育・地域学習・災害復興学習で仮想空間制作を活用したい教育実践者, AIリテラシー，プログラミング，デジタルシティズンシップを横断する教材設計者, Minecraftや生成AIを活用した学習サービス・ワークショップの企画担当者
- 正本: `reports/07-minecraft-ai-education.md`
- AI sidecar: `metadata/report-sidecars/07-minecraft-ai-education.json`
- OKF concept: `okf/reports/07-minecraft-ai-education.md`
