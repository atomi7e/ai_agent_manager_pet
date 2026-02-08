import google.generativeai as genai
from src.config import GEMINI_API_KEY
import logging
import PIL.Image
import json
import random

class AIPlannerService:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model_name = "gemini-flash-latest" 
        self.model = genai.GenerativeModel(model_name=self.model_name)
        self.chats = {}

    async def get_plan(self, user_id: int, user_text: str, role_prompt: str = "", image_file=None, audio_file=None) -> str:
        full_prompt = f"""
        {role_prompt}
        Задача: Составь план действий. Разбей на 3-6 шагов. Без вступлений.
        Запрос: {user_text}
        """
        # (Логика чата остается прежней)
        if user_id not in self.chats: self.chats[user_id] = self.model.start_chat(history=[])
        try:
            chat = self.chats[user_id]
            content = [full_prompt]
            if image_file: content.append(PIL.Image.open(image_file))
            if audio_file: content.append({"mime_type": "audio/ogg", "data": audio_file.read()})
            
            response = await chat.send_message_async(content)
            return response.text
        except Exception as e:
            return f"Ошибка AI: {e}"

    async def generate_quiz(self):
        """Генерирует вопрос для викторины"""
        topics = ["Python programming", "Cybersecurity", "Logic puzzles", "Science facts", "History"]
        topic = random.choice(topics)
        
        prompt = f"""
        Create a multiple-choice quiz question about {topic}.
        Strictly follow this format with '|' separator:
        QUESTION | OPTION_A | OPTION_B | OPTION_C | OPTION_D | CORRECT_OPTION_INDEX (0, 1, 2, or 3)
        
        Example:
        What is 2+2? | 3 | 4 | 5 | 6 | 1
        """
        
        try:
            response = await self.model.generate_content_async(prompt)
            text = response.text.strip()
            parts = text.split('|')
            if len(parts) >= 6:
                return {
                    "question": parts[0].strip(),
                    "options": [p.strip() for p in parts[1:5]],
                    "correct_index": int(parts[5].strip())
                }
            return None
        except Exception as e:
            logging.error(f"Quiz Error: {e}")
            return None