"""
画面キャプチャモジュール - 画面キャプチャと画像処理を担当します。

- mssを使用して高速に画面をキャプチャします。
- Pillow (PIL) を用いて画像のリサイズやフォーマット変換を行います。
- 非同期実行のためにExecutorを活用します。
"""

import mss
import io
import asyncio
import logging
from PIL import Image, ExifTags
from typing import Optional

logger = logging.getLogger(__name__)

class ScreenCapture:
    """
    画面キャプチャと画像処理を担当するクラスです。
    """

    def _capture_sync(self) -> Optional[bytes]:
        """
        画面全体を同期的にキャプチャし、JPEG形式のバイトデータとして返します。
        エラー時はNoneを返します。
        """
        try:
            with mss.mss() as sct:
                # プライマリモニタをキャプチャします。
                monitor = sct.monitors[1]
                sct_img = sct.grab(monitor)
                # mssの画像データをPillowのImageオブジェクトに変換します。
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                # バイト配列にJPEGとして保存します。
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG', quality=85)
                return img_byte_arr.getvalue()
        except Exception as e:
            logger.error(f"同期的な画面キャプチャに失敗しました: {e}", exc_info=True)
            return None

    async def capture(self) -> Optional[bytes]:
        """
        画面を非同期的にキャプチャします。
        同期的なキャプチャ処理を別スレッドで実行します。
        
        Returns:
            Optional[bytes]: キャプチャした画像のJPEGバイトデータ。失敗した場合はNoneです。
        """
        loop = asyncio.get_running_loop()
        logger.info("画面キャプチャを開始します…")
        img_data = await loop.run_in_executor(None, self._capture_sync)
        if img_data:
            logger.info("画面キャプチャに成功しました。")
        else:
            logger.error("画面キャプチャに失敗しました。")
        return img_data
    
    def bytes_to_pil(self, image_data: bytes) -> Optional[Image.Image]:
        """
        バイトデータをPillowのImageオブジェクトに変換します。

        Args:
            image_data (bytes): 画像のバイトデータです。

        Returns:
            Optional[Image.Image]: PillowのImageオブジェクト。失敗した場合はNoneです。
        """
        try:
            img = Image.open(io.BytesIO(image_data))
            # EXIF情報に基づいて画像の向きを補正します。
            try:
                exif = img._getexif()
                if exif:
                    orientation_key = next((k for k, v in ExifTags.TAGS.items() if v == 'Orientation'), None)
                    if orientation_key in exif:
                        orientation = exif[orientation_key]
                        if orientation == 3: img = img.rotate(180, expand=True)
                        elif orientation == 6: img = img.rotate(270, expand=True)
                        elif orientation == 8: img = img.rotate(90, expand=True)
            except (AttributeError, KeyError, IndexError):
                # EXIF情報がない、または不正な場合は何もしません。
                pass
            return img
        except Exception as e:
            logger.error(f"バイトデータからPIL Imageへの変換に失敗しました: {e}")
            return None

    def resize_image(self, image: Image.Image, max_width: int = 1024, quality: int = 85) -> Optional[bytes]:
        """
        Pillow Imageオブジェクトをリサイズし、JPEGバイトデータとして返します。

        Args:
            image (Image.Image): リサイズするPillow Imageオブジェクトです。
            max_width (int): リサイズ後の最大幅です。
            quality (int): JPEGの品質です。

        Returns:
            Optional[bytes]: リサイズされた画像のJPEGバイトデータ。失敗した場合はNoneです。
        """
        try:
            if image.width > max_width:
                ratio = max_width / image.width
                new_height = int(image.height * ratio)
                resized_img = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
                logger.info(f"画像をリサイズしました: {max_width}x{new_height}")
            else:
                resized_img = image

            img_byte_arr = io.BytesIO()
            resized_img.save(img_byte_arr, format='JPEG', quality=quality)
            return img_byte_arr.getvalue()
        except Exception as e:
            logger.error(f"画像のリサイズに失敗しました: {e}")
            return None


