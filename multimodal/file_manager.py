"""
ファイル管理モジュール - データファイルの読み書きを担当します。

- 会話ログ、記憶、フィードバックログをJSON形式で保存・読み込みます。
- 非同期保存と同期保存の両方に対応しています。
- エラーハンドリングを実装しています。
"""

import json
import os
import asyncio
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class FileManager:
    """
    データファイルの永続化を管理するクラスです。
    """
    def __init__(self, settings: Dict[str, Any]):
        """
        FileManagerの初期化を行います。

        Parameters:
            settings (Dict[str, Any]): ファイルパスなどの設定情報です。
        """
        self.log_file = settings['LOG_FILE_PATH']
        self.memory_file = settings['MEMORY_FILE_PATH']
        self.feedback_file = settings['FEEDBACK_LOG_FILE_PATH']
        self.memory_limit = settings.get('MEMORY_LIMIT', 100)

    def _load_json_file(self, file_path: str) -> List:
        """
        汎用的なJSONファイル読み込み関数です。
        ファイルが存在しない場合は空リストを返します。
        """
        if not os.path.exists(file_path):
            logger.info(f"ファイルが見つかりません: {file_path}。空リストで開始します。")
            return []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    logger.info(f"{file_path} から {len(data)} 件のデータを読み込みました。")
                    return data
                else:
                    logger.warning(f"{file_path} のフォーマットが不正です（リスト形式を想定）。空リストで開始します。")
                    return []
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"{file_path} の読み込みまたはパースに失敗: {e}。空リストで開始します。")
            return []

    def _save_json_file_sync(self, file_path: str, data: List):
        """
        汎用的なJSONファイル同期保存関数です。
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info(f"{file_path} に {len(data)} 件のデータを保存しました。")
        except IOError as e:
            logger.error(f"{file_path} への保存に失敗しました: {e}")
        except Exception as e:
            logger.error(f"{file_path} への保存中に予期しないエラーが発生しました: {e}")

    async def _save_json_file_async(self, file_path: str, data: List):
        """
        汎用的なJSONファイル非同期保存関数です。
        """
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._save_json_file_sync, file_path, data)

    # --- 会話ログ関連 ---
    def load_conversation_log(self) -> List[Dict[str, Any]]:
        """
        会話ログを読み込みます。
        """
        return self._load_json_file(self.log_file)

    def save_conversation_log_sync(self, log_data: List[Dict[str, Any]]):
        """
        会話ログを同期的に保存します。
        """
        self._save_json_file_sync(self.log_file, log_data)

    async def save_conversation_log_async(self, log_data: List[Dict[str, Any]]):
        """
        会話ログを非同期で保存します。
        """
        await self._save_json_file_async(self.log_file, list(log_data)) # コピーを渡します

    # --- 記憶関連 ---
    def load_memory(self) -> List[str]:
        """
        AIの記憶データを読み込みます。
        """
        return self._load_json_file(self.memory_file)

    def save_memory(self, memory_data: List[str]):
        """
        AIの記憶データを保存します。
        重複を除外し、上限を超えた場合は古いものから削除します。
        """
        unique_memory = list(dict.fromkeys(memory_data))
        if len(unique_memory) > self.memory_limit:
            unique_memory = unique_memory[-self.memory_limit:]
            logger.info(f"記憶データを最新{self.memory_limit}件にトリミングしました。")
        self._save_json_file_sync(self.memory_file, unique_memory)

    # --- フィードバックログ関連 ---
    def load_feedback_log(self) -> List[str]:
        """
        フィードバックログを読み込みます。
        """
        return self._load_json_file(self.feedback_file)

    def save_feedback_log(self, feedback_data: List[str]):
        """
        フィードバックログを保存します（同期的なコールバック用）。
        """
        self._save_json_file_sync(self.feedback_file, feedback_data)