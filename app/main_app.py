"""
AI Assistant Application - Main Entry Point (YouTube Comment Monitoring)

このファイルはAIアシスタントアプリケーションのメイン実行ファイルです。
主な機能：
- 各モジュールの初期化と設定
- YouTubeコメント監視と対話ループの実行
- 音声合成による応答生成
- 会話履歴とメモリの管理
- 画面分析機能の統合
"""

import sys
import os
# プロジェクトのルートディレクトリをPythonパスに追加します
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import traceback
import logging
from typing import Dict, Any, List

# --- コアモジュール ---
from core.ai_logic import AIModel, AILogic
from core.voice_synthesis import VoiceSynthesizer
# 音声認識機能はこのバージョンでは使用しません

# --- マルチモーダルモジュール ---
from multimodal.screen_capture import ScreenCapture
# YouTubeコメント監視モニター
from multimodal.Youtube import PytchatMonitor  # Youtube.pyからPytchatMonitorをインポートします

# --- ユーティリティモジュール ---
from multimodal.file_manager import FileManager
from multimodal.config_loader import (
    load_settings,
    is_voicevox_connected,
    REQUIRED_LIBRARIES,
    check_dependencies
)

# --- ロギング設定 ---
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class AIAssistantApp:
    """
    AIアシスタントアプリケーションのメインクラス。
    状態管理と主要な処理ロジックをカプセル化します。
    """
    def __init__(self, settings: Dict[str, Any]):
        """
        AIAssistantAppのインスタンスを初期化します。

        Args:
            settings (Dict[str, Any]): .envファイルから読み込まれた設定。
        """
        self.settings = settings
        self.running = True

        # --- 状態管理 ---
        self.conversation_log: List[Dict[str, Any]] = []
        self.memory: List[str] = []
        self.feedback_log: List[str] = []
        # 最後に処理したコメントを保存（重複応答防止）
        self.last_processed_comment: Dict[str, Any] = {"author": None, "message": None}

        # --- モジュールの初期化 ---
        self.file_manager = FileManager(settings)
        self.ai_model = AIModel(settings['GEMINI_API_KEY'])
        self.voice_synthesizer = VoiceSynthesizer(
            settings['VOICEVOX_URL'],
            speed_scale=settings.get('VOICE_SPEED_SCALE', 1.0),
            intonation_scale=settings.get('VOICE_INTONATION_SCALE', 1.0)
        )
        # self.speech_recognizer = SpeechRecognizer() # 音声認識は使用しない
        self.screen_capture = ScreenCapture()
        self.ai_logic = AILogic(self.ai_model, self.settings, self.screen_capture)
       
        # YouTubeコメント監視モニターの初期化
        if self.settings.get("YOUTUBE_VIDEO_ID"):
            self.youtube_monitor = PytchatMonitor(self.settings["YOUTUBE_VIDEO_ID"])
        else:
            self.youtube_monitor = None
            logger.warning(".env ファイルに YOUTUBE_VIDEO_ID が設定されていません。YouTube の監視（モニタリング）が無効になっています。")

    async def initialize(self):
        """
        非同期で初期化処理を行います。
        """
        logger.info("AIアシスタントアプリケーションの初期化を開始します。")
        self.conversation_log = self.file_manager.load_conversation_log()
        self.memory = self.file_manager.load_memory()
        self.feedback_log = self.file_manager.load_feedback_log()
        await self.voice_synthesizer.initialize_session()
        logger.info("初期化が完了しました。")

    async def shutdown(self):
        """
        アプリケーションのクリーンアップ処理を行います。
        """
        logger.info("AIアシスタントアプリケーションの終了処理を開始します。")
        self.running = False
        await self.voice_synthesizer.close_session()
        logger.info("最終的なログとメモリを保存します。")
        self.file_manager.save_conversation_log_sync(self.conversation_log)
        self.file_manager.save_memory(self.memory)
        self.file_manager.save_feedback_log(self.feedback_log)
        logger.info("クリーンアップが完了しました。お疲れさまでした。")

    async def run(self):
        """
        アプリケーションのメインループを実行します。
        """
        await self.initialize()
        if not self.youtube_monitor:
            logger.critical("YouTubeモニターが初期化されていません。.envファイルにYOUTUBE_VIDEO_IDを設定してください。")
            return
        if not self.conversation_log:
            initial_message = "こんにちは！AIアシスタントです。YouTubeのコメント監視を開始します。"
            logger.info(f"AI Assistant: {initial_message}")
            await self.voice_synthesizer.play_text(initial_message, self.settings['VOICEVOX_SPEAKER_ID'])
            self.conversation_log.append({'speaker': 'ai', 'utterance': initial_message})
        logger.info(f"YouTubeチャットの監視を開始します（動画ID: {self.settings['YOUTUBE_VIDEO_ID']}）")
        while self.running:
            try:
                # 音声認識の代わりにYouTubeコメントからユーザー入力を取得します
                latest_comment = await self.youtube_monitor.get_latest_comment()
                user_utterance = ""
                log_utterance = ""
                if latest_comment:
                    author = latest_comment['authorDetails']['displayName']
                    message = latest_comment['snippet']['displayMessage'].strip()
                    # 同じコメントを連続で処理しないようにします
                    if (author == self.last_processed_comment.get("author") and
                        message == self.last_processed_comment.get("message")):
                        await asyncio.sleep(self.settings.get('YOUTUBE_POLLING_INTERVAL', 5.0))
                        continue
                    if message: # 空コメントは無視します
                        self.last_processed_comment = {"author": author, "message": message}
                        user_utterance = f"{author}: {message}"
                        log_utterance = f"[{author}] {message}"
                if not user_utterance:
                    # 新しいコメントがなければ待機します
                    await asyncio.sleep(self.settings.get('YOUTUBE_POLLING_INTERVAL', 5.0))
                    continue
                logger.info(f"新しいコメントを処理しました: {log_utterance}")
                self.conversation_log.append({'speaker': 'user', 'utterance': user_utterance})
                if user_utterance in self.settings.get('TERMINATION_PHRASES', []):
                    farewell_message = "ありがとうございました。またお話ししましょう。さようなら！"
                    logger.info(f"AI Assistant: {farewell_message}")
                    await self.voice_synthesizer.play_text(farewell_message, self.settings['VOICEVOX_SPEAKER_ID'])
                    self.conversation_log.append({'speaker': 'ai', 'utterance': farewell_message})
                    break
                # --- 応答生成 ---
                response_to_speak = ""
                if self.is_screen_analysis_triggered(user_utterance):
                    response_to_speak = await self._handle_screen_analysis(user_utterance)
                else:
                    response_text = await self.ai_logic.generate_response(
                        user_utterance,
                        self.conversation_log,
                        self.memory,
                        self.feedback_log
                    )
                    log_speaker = "ai_error" if "ごめんなさい" in response_text else "ai"
                    self.conversation_log.append({'speaker': log_speaker, 'utterance': response_text})
                    response_to_speak = response_text
                logger.info(f"AI Assistant: {response_to_speak}")
                # --- 音声再生と各種更新処理を並行実行 ---
                feedback_task = asyncio.create_task(
                    self.ai_logic.generate_and_save_feedback(
                        user_utterance,
                        response_to_speak,
                        self.conversation_log,
                        self.memory,
                        self.feedback_log, # フィードバックログを渡す
                        self.file_manager.save_feedback_log # 保存関数を渡す
                    )
                )
                speak_task = asyncio.create_task(
                    self.voice_synthesizer.play_text(response_to_speak, self.settings['VOICEVOX_SPEAKER_ID'])
                )
                new_facts = await self.ai_logic.extract_and_update_memory(
                    user_utterance,
                    response_to_speak,
                    self.memory
                )
                if new_facts:
                    self.file_manager.save_memory(self.memory)
                # --- タスクの完了を待ちます ---
                await speak_task
                await feedback_task
                await self.file_manager.save_conversation_log_async(self.conversation_log)
            except asyncio.CancelledError:
                logger.info("メインループがキャンセルされました。")
                break
            except Exception as e:
                logger.error(f"メインループで予期しないエラーが発生しました: {e}")
                traceback.print_exc()
                await asyncio.sleep(2) # エラー発生時に少し待機します
        await self.shutdown()


def main_entrypoint():
    """
    アプリケーションを起動するためのエントリーポイントです。
    """
    if not check_dependencies(REQUIRED_LIBRARIES):
        return

    settings = load_settings()
    if not settings.get("GEMINI_API_KEY"):
        logger.error("Gemini APIキーが設定されていません。.envファイルを確認してください。")
        return
    if not settings.get("YOUTUBE_VIDEO_ID"):
        logger.error("YOUTUBE_VIDEO_IDが設定されていません。.envファイルに追加してください。")
        return
    if not is_voicevox_connected(settings.get("VOICEVOX_URL")):
        logger.warning(
            f"VOICEVOXエンジン（{settings.get('VOICEVOX_URL')}）に接続できません。エンジンが起動しているか確認してください。"
        )
    app = AIAssistantApp(settings)
    try:
        # Windowsで発生する可能性のあるイベントループポリシーの問題に対応します
        if asyncio.get_event_loop_policy().__class__.__name__ == 'WindowsProactorEventLoopPolicy':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(app.run())
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("ユーザーによってアプリケーションが中断されました。終了処理を行います。")
    except Exception as e:
        logger.critical(f"アプリケーション実行中に重大なエラーが発生しました: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main_entrypoint()
