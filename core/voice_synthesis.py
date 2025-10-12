"""
音声合成モジュール - VOICEVOX APIとの非同期通信と音声再生を担当します。

- aiohttpを使用してVOICEVOXエンジンへ非同期リクエストを送信します。
- 音声データを取得します。
- sounddeviceとsoundfileを用いて音声を非同期で再生します。
"""

import asyncio
import aiohttp
import logging
import sounddevice as sd
import soundfile as sf
import io
from typing import Optional

logger = logging.getLogger(__name__)

class VoiceSynthesizer:
    """
    VOICEVOXによる音声合成と再生を管理するクラスです。
    """
    
    def __init__(self, voicevox_url: str, speed_scale: float = 1.0, intonation_scale: float = 1.0):
        """
        VoiceSynthesizerを初期化します。

        Args:
            voicevox_url (str): VOICEVOXエンジンのURLです。
            speed_scale (float): 話速の倍率です。
            intonation_scale (float): 抑揚の倍率です。
        """
        self.base_url = voicevox_url
        self.speed_scale = speed_scale
        self.intonation_scale = intonation_scale
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize_session(self):
        """
        非同期HTTPセッションを初期化します。
        すでにセッションが存在し閉じていない場合は何もしません。
        """
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
            logger.info("aiohttpクライアントセッションを初期化しました。")

    async def close_session(self):
        """
        非同期HTTPセッションを閉じます。
        セッションが存在し、かつ開いている場合のみ閉じます。
        """
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("aiohttpクライアントセッションを閉じました。")

    async def _get_voice_data(self, text: str, speaker_id: int) -> Optional[bytes]:
        """
        指定したテキストとスピーカーIDでVOICEVOXから音声データを取得します。
        エラー時はNoneを返します。
        """
        if not self.session or self.session.closed:
            logger.error("aiohttpセッションが利用できません。再初期化します。")
            await self.initialize_session()
            if not self.session: 
                return None

        try:
            # 1. audio_queryの生成を行います。
            async with self.session.post(
                f"{self.base_url}/audio_query",
                params={"text": text, "speaker": speaker_id},
                timeout=10
            ) as resp:
                resp.raise_for_status()
                query_json = await resp.json()

            # 2. 発話速度と抑揚を設定値から適用します。
            if isinstance(self.speed_scale, (int, float)):
                query_json["speedScale"] = float(self.speed_scale)
            if isinstance(self.intonation_scale, (int, float)):
                query_json["intonationScale"] = float(self.intonation_scale)

            # 3. synthesisの実行を行います。
            async with self.session.post(
                f"{self.base_url}/synthesis",
                params={"speaker": speaker_id},
                json=query_json,
                timeout=20
                ) as resp:
                resp.raise_for_status()
                return await resp.read()
    
        except aiohttp.ClientConnectorError as e:
            logger.error(f"VOICEVOXエンジンへの接続に失敗しました: {e}")
        except aiohttp.ClientResponseError as e:
            logger.error(f"VOICEVOX APIエラー (ステータス: {e.status}): {e.message}")
        except asyncio.TimeoutError:
            logger.error("VOICEVOX APIへの接続がタイムアウトしました。")
        except Exception as e:
            logger.error(f"VOICEVOXリクエストで予期しないエラーが発生しました: {e}", exc_info=True)
    
        return None

    async def play_text(self, text: str, speaker_id: int):
        """
        指定されたテキストを音声合成し、再生します。

        Args:
            text (str): 読み上げるテキストです。
            speaker_id (int): VOICEVOXのスピーカーIDです。
        """
        if not text or not text.strip():
            logger.warning("空のテキストが指定されたため、再生をスキップします。")
            return

        logger.info(f"音声合成・再生を開始します: '{text[:30]}...'")
        voice_data = await self._get_voice_data(text, speaker_id)

        if not voice_data:
            logger.warning(f"音声データの取得に失敗しました: '{text[:30]}...'")
            return

        try:
            # sounddeviceの再生はブロッキングなため、別スレッドで実行します。
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._play_sound, voice_data)
        except Exception as e:
            logger.error(f"音声再生中にエラーが発生しました: {e}", exc_info=True)
            # エラー発生時にクリーンアップを試みます。
            try:
                sd.stop()
            except Exception as stop_e:
                logger.error(f"エラー発生後のsounddevice停止に失敗しました: {stop_e}")

    def _play_sound(self, voice_data: bytes):
        """
        音声データを同期的に再生するヘルパー関数です。
        run_in_executorから呼び出されることを想定しています。
        """
        try:
            with io.BytesIO(voice_data) as wav_io:
                data, samplerate = sf.read(wav_io, dtype='float32')
                sd.play(data, samplerate)
                sd.wait() # 再生が完了するまで待機します。
        except Exception as e:
            logger.error(f"同期的な音声再生中にエラーが発生しました: {e}")