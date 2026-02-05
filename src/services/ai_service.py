import google.generativeai as genai
from src.config import GEMINI_API_KEY
import logging

class AIPlannerService:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        
        # БЕРЕМ МОДЕЛЬ ИЗ ТВОЕГО СПИСКА
        # "Lite" версия работает быстро и меньше тратит лимиты
        self.model_name = "gemini-flash-latest"
        
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction="""
            Ты — помощник по планированию.
            Твоя задача: разбить цель пользователя на четкие шаги.
            Отвечай просто, используй списки. Не используй сложное форматирование.
            """
        )
        self.chats = {}

    async def get_plan(self, user_id: int, user_text: str) -> str:
        if user_id not in self.chats:
            self.chats[user_id] = self.model.start_chat(history=[])
        
        try:
            chat = self.chats[user_id]
            response = await chat.send_message_async(user_text)
            return response.text
        except Exception as e:
            error_msg = str(e)
            logging.error(f"AI Error: {error_msg}")
            
            # Если словили лимит, предупреждаем пользователя
            if "429" in error_msg:
                return "⚠️ Слишком много запросов. Подождите пару минут и попробуйте снова."
            
            return f"Ошибка при обращении к AI ({self.model_name}): {error_msg}"