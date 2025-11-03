"""
AIコアロジックモジュール - AIの思考と応答生成を担当します。

- Gemini APIとの非同期通信を行います。
- システムプロンプト・記憶・フィードバックを動的に組み立てます。
- 応答テキストの生成と整形を行います。
- 会話からの事実抽出や自己フィードバック生成も担当します。
"""

import google.generativeai as genai
import logging
import random
import re
from typing import List, Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

class AIModel:
    """
    Gemini APIモデルをラップするクラスです。
    """
    def __init__(self, api_key: str, model_name: str = 'gemini-2.0-flash-lite'):
        """
        AIModelのインスタンスを初期化します。

        Parameters:
            api_key (str): Gemini APIキーです。
            model_name (str, optional): 使用するモデル名です。デフォルトはgemini-2.0-flash-liteです。
        """
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
            logger.info(f"Gemini APIの設定に成功しました（モデル: {model_name}）")
        except Exception as e:
            logger.critical(f"Gemini APIの設定に失敗しました: {e}")
            raise ValueError("Gemini APIキーが無効、または設定に失敗しました。") from e

    async def generate_content_async(self, *args, **kwargs):
        """
        モデルから非同期で応答を生成します。
        """
        return await self.model.generate_content_async(*args, **kwargs)


class AILogic:
    """
    AIの思考ロジックを管理するクラスです。
    """
    def __init__(self, ai_model: AIModel, settings: Dict[str, Any], screen_capture=None):
        """
        AILogicのインスタンスを初期化します。

        Parameters:
            ai_model (AIModel): AIモデルのインスタンスです。
            settings (Dict[str, Any]): アプリケーション設定です。
            screen_capture: 画面キャプチャインスタンスです。
        """
        self.ai_model = ai_model
        self.settings = settings
        self.screen_capture = screen_capture
        self._load_prompts()

    def _load_prompts(self):
        """
        プロンプトファイルを読み込みます。
        """
        try:
            with open(self.settings['SYSTEM_PROMPT_PATH'], 'r', encoding='utf-8') as f:
                self.system_prompt = f.read()
            with open(self.settings['FEEDBACK_PROMPT_PATH'], 'r', encoding='utf-8') as f:
                self.feedback_prompt_template = f.read()
            with open(self.settings['MEMORY_EXTRACTION_PROMPT_PATH'], 'r', encoding='utf-8') as f:
                self.memory_extraction_prompt_template = f.read()
        except FileNotFoundError as e:
            logger.critical(f"プロンプトファイルが見つかりません: {e.filename}。パスを確認してください。")
            raise
        except Exception as e:
            logger.critical(f"プロンプトファイルの読み込み中にエラーが発生しました: {e}")
            raise
    
    def _get_relevant_memory(self, user_utterance: str, memory_list: List[str], history: List[Dict]) -> List[str]:
        """
        現在の発話と直近の会話履歴から関連する記憶を検索します。

        Parameters:
            user_utterance (str): ユーザーの現在の発話です。
            memory_list (List[str]): 全ての記憶のリストです。
            history (List[Dict]): 直近の会話履歴です。

        Returns:
            List[str]: 関連すると判断された記憶のリストです。
        """
        if not memory_list:
            return []

        search_text = user_utterance
        for entry in history:
            if isinstance(entry.get('utterance'), str):
                search_text += " " + entry['utterance']

        # キーワード抽出（ストップワード除去）
        keywords = set(re.split(r'[\s,.?!、。？！]+', search_text.lower()))
        stop_words = {'は', 'が', 'を', 'に', 'と', 'から', 'まで', 'で', 'です', 'ます', 'ね', 'よ', 'か', 'の', 'こと', 'もの', 'そう', 'これ', 'それ', 'あれ', 'どれ', 'さん'}
        keywords = {k for k in keywords if len(k) > 1 and k not in stop_words}

        relevant_facts = {fact for fact in memory_list if any(kw in fact.lower() for kw in keywords)}
        relevant_list = list(relevant_facts)
        if relevant_list:
            logger.info(f"{len(relevant_list)}件の関連記憶を検出しました（キーワード例: {list(keywords)[:5]}）: {relevant_list}")
        return relevant_list

    def _build_prompt_messages(
        self,
        user_utterance: str,
        conversation_log: List[Dict],
        memory: List[str],
        feedback_log: List[str],
        image_data: Optional[bytes] = None
    ) -> List[Dict]:
        """
        Gemini APIに送信するためのメッセージリストを構築します。
        """
        messages = []
        # 1. システムプロンプトとコンテキスト情報
        initial_parts = [self.system_prompt]
        relevant_memory = self._get_relevant_memory(user_utterance, memory, conversation_log[-4:])
        if relevant_memory:
            memory_text = "\n---\n関連する可能性のある記憶:\n" + "\n".join([f"- {fact}" for fact in relevant_memory])
            initial_parts.append(memory_text)
        if feedback_log:
            feedback_text = "\n---\n前回の自己フィードバック:\n" + feedback_log[-1]
            initial_parts.append(feedback_text)
        messages.append({'role': 'user', 'parts': initial_parts})
        # モデルが自身の応答を生成するための 'model' roleの空のpartsを追加します
        messages.append({'role': 'model', 'parts': ["はい、AIアシスタントとしてお話しします。"]})
        # 2. 会話履歴
        history_limit = 10 if not image_data else 2
        recent_log = conversation_log[-(history_limit * 2):]
        for entry in recent_log:
            role = 'user' if entry['speaker'] in ['user', 'master'] else 'model'
            if isinstance(entry.get('utterance'), str):
                messages.append({'role': role, 'parts': [entry['utterance']]})
        # 3. 現在のユーザー入力と画像
        current_user_parts = [user_utterance]
        if image_data:
            logger.info("画像をプロンプトに追加します（画面分析用）。")
            pil_image = self.screen_capture.bytes_to_pil(image_data)
            if pil_image:
                current_user_parts.append("\nこの画面について教えてください。")
                current_user_parts.append(pil_image)
            else:
                logger.error("画像データの処理に失敗しました。")
        messages.append({'role': 'user', 'parts': current_user_parts})
        return messages

    async def generate_response(
        self,
        user_utterance: str,
        conversation_log: List[Dict],
        memory: List[str],
        feedback_log: List[str],
        image_data: Optional[bytes] = None
    ) -> str:
        """
        Gemini APIを呼び出して応答を生成します。
        """
        try:
            messages = self._build_prompt_messages(
                user_utterance, conversation_log, memory, feedback_log, image_data
            )
            if not messages:
                raise ValueError("Gemini APIに送信するメッセージリストが空です。")
            generation_config = genai.types.GenerationConfig(
                temperature=0.8, top_p=0.95
            ) if not image_data else genai.types.GenerationConfig(
                temperature=0.7, top_p=0.9
            )
            response = await self.ai_model.generate_content_async(
                messages, generation_config=generation_config
            )
            if response.parts:
                response_text = response.text.replace("**", "").strip()
            else:
                logger.warning(f"Geminiの応答が空またはブロックされました。理由: {response.prompt_feedback}")
                return random.choice(self.settings.get('FALLBACK_RESPONSES', [""]))
        except Exception as e:
            logger.error(f"Gemini API呼び出しまたは処理中にエラーが発生しました: {e}", exc_info=True)
            return "ごめんなさい、今ちょっと調子が悪いです…"

    async def extract_and_update_memory(
        self, 
        user_utterance: str, 
        ai_response: str, 
        current_memory: List[str]
    ) -> List[str]:
        """
        会話から新しい事実を抽出し、メモリリストを更新します。

        Parameters:
            user_utterance (str): ユーザーの発話です。
            ai_response (str): AIの応答です。
            current_memory (List[str]): 現在のメモリリストです（この場で更新されます）。

        Returns:
            List[str]: 新しく追加された事実のリストです。
        """
        if not user_utterance or not ai_response:
            return []
        prompt = self.memory_extraction_prompt_template.format(
            user_utterance=user_utterance,
            ai_response=ai_response
        )
        try:
            config = genai.types.GenerationConfig(temperature=0.1, top_p=0.5)
            response = await self.ai_model.generate_content_async(prompt, generation_config=config)
            if response.parts and response.text.strip().lower() != 'なし':
                facts_text = response.text.strip()
                extracted = [line[2:].strip() for line in facts_text.split('\n') if line.startswith('- ')]
                new_facts = [fact for fact in extracted if fact and fact not in current_memory]
                if new_facts:
                    current_memory.extend(new_facts)
                    logger.info(f"{len(new_facts)}件の新しい事実を抽出しました: {new_facts}")
                return new_facts
            return []
        except Exception as e:
            logger.error(f"事実抽出中にエラーが発生しました: {e}")
            return []

    async def generate_and_save_feedback(
        self,
        user_utterance: str,
        ai_response: str,
        current_log: List[Dict],
        current_memory: List[str],
        feedback_log: List[str],
        save_func: Callable
    ):
        """
        自己フィードバックを生成し、リストを更新して保存します。
        """
        if not user_utterance or not ai_response:
            return
        recent_log_str = "\n".join([f"{entry['speaker']}: {entry['utterance']}" for entry in current_log[-6:]])
        memory_str = "\n".join([f"- {fact}" for fact in current_memory]) if current_memory else "なし"
        previous_feedback = feedback_log[-1] if feedback_log else "なし"
        prompt = self.feedback_prompt_template.format(
            user_utterance=user_utterance,
            ai_response=ai_response,
            recent_conversation_log=recent_log_str,
            current_memory=memory_str,
            previous_feedback=previous_feedback
        )
        try:
            config = genai.types.GenerationConfig(temperature=0.7, top_p=0.9)
            response = await self.ai_model.generate_content_async(prompt, generation_config=config)
            if response.parts:
                feedback_text = response.text.strip()
                logger.info("自己フィードバックを生成しました。")
                feedback_log.append(feedback_text)
                if len(feedback_log) > 10:
                    feedback_log.pop(0)
                save_func(feedback_log)
            else:
                logger.warning(f"自己フィードバック生成APIの応答が空でした。ブロック理由: {response.prompt_feedback}")
        except Exception as e:
            logger.error(f"自己フィードバック生成中にエラーが発生しました: {e}")
