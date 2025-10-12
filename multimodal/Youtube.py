import pytchat
import asyncio
import threading
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PytchatMonitor:
    """
    YouTubeライブのコメントを非同期で取得するためのクラスです。
    pytchatを利用してコメントを取得します。
    """
    def __init__(self, live_video_id: str):
        """
        インスタンスを初期化します。
        
        Parameters:
            live_video_id (str): 監視対象のYouTubeライブ動画IDです。
        """
        if not live_video_id:
            raise ValueError("ライブ動画IDは必須です。")
        self.video_id = live_video_id
        self.chat = pytchat.create(video_id=self.video_id)
        self.last_comment_id = None  # 直前に取得したコメントID（重複防止用）です。
        logger.info(f"PytchatMonitorを初期化しました（動画ID: {self.video_id}）")

    def _get_latest_sync(self) -> Optional[Dict[str, Any]]:
        """
        最新のコメントを同期的に取得し、APIの形式に合わせて返します。
        
        Returns:
            Optional[Dict[str, Any]]: 最新コメントの情報です。取得できない場合はNoneを返します。
        """
        try:
            if not self.chat.is_alive():
                logger.warning("チャットが切断されています。")
                return None
            chat_data = self.chat.get()
            comments = chat_data.items
            if not comments:
                return None
            latest_comment = comments[-1]
            comment_id = getattr(latest_comment, 'id', None)
            if comment_id and comment_id == self.last_comment_id:
                return None
            self.last_comment_id = comment_id
            # main_app.pyが期待するデータ形式に変換して返します
            return {
                'id': comment_id,
                'authorDetails': {
                    'displayName': latest_comment.author.name
                },
                'snippet': {
                    'displayMessage': latest_comment.message
                }
            }
        except Exception as e:
            logger.error(f"_get_latest_syncでエラーが発生しました: {e}")
            return None

    async def get_latest_comment(self) -> Optional[Dict[str, Any]]:
        """
        最新のコメントを非同期で1件取得します。
        同期処理であるpytchatの関数をスレッドプールで実行します。
        
        Returns:
            Optional[Dict[str, Any]]: 最新コメントの情報です。取得できない場合はNoneを返します。
        """
        try:
            loop = asyncio.get_event_loop()
            comment = await loop.run_in_executor(None, self._get_latest_sync)
            return comment
        except Exception as e:
            logger.error(f"get_latest_commentでエラーが発生しました: {e}")
            return None