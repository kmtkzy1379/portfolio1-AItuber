AItuberは、Google Gemini APIとVOICEVOX音声合成、VTube Studio（Live2D）連携を統合したYouTubeコメント監視型のAIVtuberアプリケーションです。リアルタイムでYouTubeライブコメントを監視し、音声とLive2Dアバターで応答する対話型AI配信者です。このAIシステムは自由エネルギ原理（FEP）を基に設計されており、意識形成理論を取り入れたAIの挙動を観察する実験的アプリケーションです。

## ✨ 主な機能

- **YouTubeコメント監視**: リアルタイムでYouTubeライブコメントを取得し、AIが応答
- **音声合成**: VOICEVOXを使用した自然な日本語音声合成
- **LIVE2D連携**: VTube Studioとの連携によるLive2Dアバターの自動動作
- **記憶機能**: 会話履歴から重要な情報を抽出・記憶
- **自己フィードバック**: AI自身による会話の振り返りと改善

## 🏗️ アーキテクチャ

```
app/
├── main_app.py              # メインアプリケーション
├── random_move.py           # Live2Dアバター制御（VTube Studio連携）
├──app.py                    # メインアプリとLive2D同時起動
core/
├── ai_logic.py              # AI思考ロジック
├── voice_synthesis.py       # 音声合成
multimodal/
├── Youtube.py               # YouTubeコメント監視
├── screen_capture.py        # 画面キャプチャ
├── config_loader.py         # 設定管理
└── file_manager.py          # ファイル管理
data/
├── conversation_log.json    # 会話履歴
├── ai_memory.json           # AI記憶
└── ai_feedback_log.json     # フィードバックログ
prompt/
├── system_prompt.txt        # システムプロンプト
├── memory_extraction_prompt.txt  # 記憶抽出プロンプト
└── self_feedback_prompt.txt # 自己フィードバックプロンプト
```

## ⚙️ 必要な環境

- Python 3.9 以降
- VOICEVOX エンジン
- Google Gemini APIキー
- **VTube Studio（Live2Dモデルを動かす場合）**

## 🚀 セットアップ方法

1. **リポジトリのクローン**
    ```bash
    git clone <https://github.com/kmtkzy1379/portfolio1-AItuber.git>
    cd portfolio1-AItuber
    ```

2. **仮想環境の作成とアクティベート**
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

3. **依存関係のインストール**
    ```bash
    pip install -r requirements.txt
    ```

4. **環境変数の設定**
`.env.example`をコピーして`.env`ファイルを作成し、ご自身の環境に合わせて値を設定してください。

5. **VOICEVOXの起動**
    VOICEVOXエンジンを起動してください。

6. **VTube Studioの起動とAPI有効化**
    VTube Studioを起動し、WebSocket API（デフォルト: ws://localhost:8001）を有効にしてください。

7. **プロンプト変更(任意)**
`prompt/system_prompt.txt`をあなたのイメージするキャラの設定してください。
**おすすめの変更、注意点**
- 「AI」と記述されている部分をキャラ名に変更してください。
- 「**■ 第2部: ‹AI›の設定**」の内容をキャラの設定に変更してください。(設定が多すぎるとFEPと性能が落ちる可能性があります)

8. **アプリケーションの実行**  
      ```bash
      python app/app.py
      ```

## 🔧 技術スタック

- **AI**: Google Gemini API
会話応答の生成、画面キャプチャの画像分析、そして対話からの記憶抽出、FEPに基づいたフィードバッグといった、AIの思考の中核を担います。
- **音声合成**: VOICEVOX
AIが生成したテキストを、自然な音声に変換します。
- **YouTube監視**: pytchat
YouTube Liveのコメントをリアルタイムで取得し、視聴者のコメントをAIに読み込ませます。
- **非同期処理**: asyncio, aiohttp
複数の処理を同時に、かつ効率的に実行するための基盤技術です。よりスムーズな応答によりユーザーの体験を向上させます。
- **画面キャプチャ**: mss
AIがPC画面の状況を「見る」ために、スクリーンショットを撮影しAIに読み込ませます。
- **音声再生**: sounddevice, soundfile
VOICEVOXから受け取った音声データを実際にスピーカーから再生する役割を担います。
- **Live2D連携**: VTube Studio WebSocket API, websockets
Live2Dモデルに自動で自然な動きをさせるため、VTube Studioとリアルタイム通信を行います。

## 📝 使用方法

1. YouTubeライブストリームの動画IDを`.env`ファイルに設定
2. アプリケーションを起動
3. YouTubeライブコメントが投稿されると自動的にAIが応答
4. トリガーフレーズで画面分析機能を実行
5. VTube StudioでLive2Dモデルを起動しておくと、AIの応答やコメントに合わせてアバターが自動で動作

## 🤝 貢献

このプロジェクトは学習・ポートフォリオ目的で作成されています。改善提案やバグ報告は歓迎します。

## 📄 ライセンス

MIT License
