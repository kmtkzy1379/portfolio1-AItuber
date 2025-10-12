"""
設定ローダーモジュール - アプリケーションの設定読み込みと管理を担当します。

- .envファイルから環境変数を読み込みます。
- 設定値の型変換やデフォルト値の設定を行います。
- アプリケーション全体で利用する定数を定義します。
- 外部サービス（VOICEVOX）への接続確認を行います。
"""
import os
import logging
from dotenv import load_dotenv
import requests
from typing import Dict, Any, List, Set

logger = logging.getLogger(__name__)

# --- 定数定義 ---
# アプリケーションのルートディレクトリを基準にパスを設定します。
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
PROMPTS_DIR = os.path.join(BASE_DIR, 'prompt')

# 必須ライブラリ一覧です。
REQUIRED_LIBRARIES = {
    'pytchat', 'aiohttp', 'sounddevice', 'soundfile',
    'numpy', 'google.generativeai', 'mss', 'PIL', 
    'requests', 'dotenv'
}

def load_settings() -> Dict[str, Any]:
    """
    .envファイルから設定を読み込み、辞書として返します。
    .envファイルが存在しない場合は警告を出し、環境変数やデフォルト値を利用します。
    必要なディレクトリも作成します。
    
    Returns:
        Dict[str, Any]: 設定値を格納した辞書です。
    """
    env_path = os.path.join(BASE_DIR, '.env')
    if not os.path.exists(env_path):
        logger.warning(f".envファイルが {env_path} に見つかりません。デフォルト値や環境変数を利用します。")
    load_dotenv(dotenv_path=env_path)

    os.makedirs(DATA_DIR, exist_ok=True)

    settings = {
        # APIキー
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        
        # YouTube関連設定
        "YOUTUBE_VIDEO_ID": os.getenv("YOUTUBE_VIDEO_ID"),
        "YOUTUBE_POLLING_INTERVAL": float(os.getenv("YOUTUBE_POLLING_INTERVAL", 5.0)),

        # VOICEVOX関連設定
        "VOICEVOX_URL": os.getenv("VOICEVOX_URL", "http://127.0.0.1:50021"),
        "VOICEVOX_SPEAKER_ID": int(os.getenv("VOICEVOX_SPEAKER_ID", 58)),
        # 音声スケール設定（環境変数で上書き可能です）
        "VOICE_SPEED_SCALE": float(os.getenv("VOICE_SPEED_SCALE", 1.0)),
        "VOICE_INTONATION_SCALE": float(os.getenv("VOICE_INTONATION_SCALE", 1.0)),
        
        # ファイルパス
        "LOG_FILE_PATH": os.path.join(DATA_DIR, "conversation_log.json"),
        "MEMORY_FILE_PATH": os.path.join(DATA_DIR, "ai_memory.json"),
        "FEEDBACK_LOG_FILE_PATH": os.path.join(DATA_DIR, "ai_feedback_log.json"),
        
        # プロンプトファイルパス
        "SYSTEM_PROMPT_PATH": os.path.join(PROMPTS_DIR, "system_prompt.txt"),
        "FEEDBACK_PROMPT_PATH": os.path.join(PROMPTS_DIR, "self_feedback_prompt.txt"),
        "MEMORY_EXTRACTION_PROMPT_PATH": os.path.join(PROMPTS_DIR, "memory_extraction_prompt.txt"),
        
        # AIの挙動設定
        "MEMORY_LIMIT": int(os.getenv("MEMORY_LIMIT", 100)),
        "SCREEN_TRIGGER_PHRASES": [
            "画面認識機能のチェックをしてください"
        ],
        "TERMINATION_PHRASES": [
            "さようなら", "バイバイ", "終了", "終わり", "またね"
        ],
        "FALLBACK_RESPONSES": [
            "えっと、なんて言おうかな…？",
            "うーん、考え中です…！",
            "ごめんなさい、うまく言葉が出てこないです…",
            "うまく理解できませんでした。"
        ]
    }
    logger.info("アプリケーション設定を読み込みました。")
    return settings


def is_voicevox_connected(url: str) -> bool:
    """
    VOICEVOXエンジンが指定されたURLで起動しているかを確認します。
    
    Args:
        url (str): VOICEVOXエンジンのURLです。
        
    Returns:
        bool: 接続できればTrue、できなければFalseです。
    """
    if not url:
        return False
    try:
        response = requests.get(f"{url}/speakers", timeout=3)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def check_dependencies(required: Set[str]) -> bool:
    """
    必須ライブラリがインストールされているかを確認します。

    Args:
        required (Set[str]): 必須ライブラリ名のセットです。

    Returns:
        bool: 全てインストールされていればTrueです。
    """
    missing = set()
    for lib in required:
        try:
            __import__(lib.split('==')[0])
        except ImportError:
            missing.add(lib)
    
    if missing:
        logger.critical("必須ライブラリが不足しています。pipでインストールしてください。")
        logger.critical(f"不足ライブラリ: {', '.join(missing)}")
        print("\npipで以下のライブラリをインストールしてください:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    logger.info("全ての必須ライブラリがインストールされています。")
    return True