import google.generativeai as genai
from src.config import GEMINI_API_KEY
import logging

class AIPlannerService:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model_name = "gemini-flash-latest"
        
        # Базовая модель
        self.model = genai.GenerativeModel(model_name=self.model_name)
        self.chats = {}

    async def get_plan(self, user_id: int, user_text: str, role_prompt: str = "") -> str:
        """
        user_text: запрос пользователя
        role_prompt: инструкция, кем быть боту (кодер, тренер и т.д.)
        """
        
        # Мы собираем мощный промпт из трех частей:
        # 1. Роль (кто ты?)
        # 2. Формат (что делать?)
        # 3. Задача (текст пользователя)
        
        full_prompt = f"""
        {role_prompt}
        
        Твоя задача: разбить цель пользователя на 3-6 конкретных шагов.
        
        ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ (СТРОГО):
        1. Каждый шаг пиши с новой строки.
        2. Начинай каждый шаг с символа тире "-".
        3. Не пиши вступлений и заключений. Только список.
        
        Цель пользователя: {user_text}
        """

        if user_id not in self.chats:
            self.chats[user_id] = self.model.start_chat(history=[])
        
        try:
            chat = self.chats[user_id]
            response = await chat.send_message_async(full_prompt)
            return response.text
        except Exception as e:
            error_msg = str(e)
            logging.error(f"AI Error: {error_msg}")
            if "429" in error_msg:
                return "⚠️ Лимит запросов. Подожди минуту."
            return f"Ошибка AI: {error_msg}"