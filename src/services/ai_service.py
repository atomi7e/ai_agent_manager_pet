import google.generativeai as genai
from src.config import GEMINI_API_KEY
import logging
import PIL.Image

class AIPlannerService:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Используем модель, которая работает стабильно
        self.model_name = "gemini-flash-latest" 
        
        self.model = genai.GenerativeModel(model_name=self.model_name)
        self.chats = {}

    async def get_plan(self, user_id: int, user_text: str, role_prompt: str = "", image_file=None) -> str:
        """
        user_text: запрос пользователя
        role_prompt: роль бота
        image_file: файл картинки
        """
        
        full_prompt = f"""
        {role_prompt}
        
        Твоя задача: Если прислали фото — проанализируй его. Если текст — составь план.
        Разбей ответ на 3-6 шагов. Каждый шаг с новой строки через тире "-".
        Не пиши вступлений, сразу пункты.
        
        Запрос пользователя: {user_text}
        """

        if user_id not in self.chats:
            self.chats[user_id] = self.model.start_chat(history=[])
        
        try:
            chat = self.chats[user_id]
            
            if image_file:
                img = PIL.Image.open(image_file)
                response = await chat.send_message_async([full_prompt, img])
            else:
                response = await chat.send_message_async(full_prompt)
                
            return response.text
        except Exception as e:
            error_msg = str(e)
            logging.error(f"AI Error: {error_msg}")
            
            if "429" in error_msg:
                return "⚠️ Слишком много запросов. Подожди минуту."
            
            return f"Ошибка AI ({self.model_name}): {error_msg}"