AItuberは、Google Gemini APIとVOICEVOX音声合成、VTube Studio（Live2D）連携を統合したYouTubeコメント監視型のAIVtuberアプリケーションです。リアルタイムでYouTubeライブコメントを監視し、音声とLive2Dアバターで応答する対話型システムです。このAIシステムは自由エネルギ原理（FEP）を基に設計されており、意識形成理論を取り入れたAIの挙動を観察する実験的アプリケーションです。

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
- YouTube API（pytchat使用）
- **VTube Studio（Live2Dモデルを動かす場合）**

## 🚀 セットアップ方法

1. **リポジトリのクローン**
    ```bash
    git clone <https://github.com/kmtkzy1379/portfolio1-AItuber.git>
    cd portfolio1-AItuber
    ```

2. **仮想環境の作成とアクティベート**
    ```bash
    python -m venv evenv
    evenv\Scripts\activate
    ```

3. **依存関係のインストール**
    ```bash
    pip install -r requirements.txt
    ```

4. **環境変数の設定**
    `.env`ファイルを作成し、以下の設定を追加：
    ```env
    GEMINI_API_KEY=your_gemini_api_key
    YOUTUBE_VIDEO_ID=your_youtube_video_id
    VOICEVOX_URL=http://127.0.0.1:50021
    VOICEVOX_SPEAKER_ID=58
    ```

5. **VOICEVOXの起動**
    VOICEVOXエンジンを起動してください。

6. **VTube Studioの起動とAPI有効化**
    VTube Studioを起動し、WebSocket API（デフォルト: ws://localhost:8001）を有効にしてください。

7. **アプリケーションの実行**  
      ```bash
      python app/app.py
      ```

## 🔧 技術スタック

- **AI**: Google Gemini API
- **音声合成**: VOICEVOX
- **YouTube監視**: pytchat
- **非同期処理**: asyncio, aiohttp
- **画面キャプチャ**: mss
- **音声再生**: sounddevice, soundfile
- **Live2D連携**: VTube Studio WebSocket API, websockets

## 📝 使用方法

1. YouTubeライブストリームの動画IDを設定
2. アプリケーションを起動
3. YouTubeライブコメントが投稿されると自動的にAIが応答
4. 「画面を見て」などのトリガーフレーズで画面分析機能を実行
5. VTube StudioでLive2Dモデルを起動しておくと、AIの応答やコメントに合わせてアバターが自動で動作

## 🤝 貢献

このプロジェクトは学習・ポートフォリオ目的で作成されています。改善提案やバグ報告は歓迎します。

## 📄 ライセンス

MIT License
