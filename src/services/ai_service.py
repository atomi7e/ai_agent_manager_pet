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

    async def get_plan(self, user_id: int, user_text: str, role_prompt: str = "", image_file=None, audio_file=None, user_facts: list = None) -> str:
        """
        Генерирует план, учитывая факты о пользователе
        """
        facts_str = ""
        if user_facts:
            facts_str = "ЧТО Я ЗНАЮ О ТЕБЕ:\n" + "\n".join([f"- {f}" for f in user_facts]) + "\n\n"

        full_prompt = f"""
        {role_prompt}
        
        {facts_str}
        
        Задача: Составь план действий. Разбей на 3-6 шагов.
        Запрос пользователя: {user_text}
        """
        
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

    async def extract_facts(self, text: str):
        """Пытается найти факты о юзере в тексте"""
        prompt = f"""
        Analyze the following user message. Does it contain any PERMANENT facts about the user (e.g., their name, profession, hobbies, technologies they study, goals)?
        
        Message: "{text}"
        
        If YES, extract the fact as a short sentence in Russian.
        If NO, return "None".
        Only return the fact or "None". Do not add extra text.
        """
        try:
            response = await self.model.generate_content_async(prompt)
            result = response.text.strip()
            if "None" in result or len(result) < 3:
                return None
            return result
        except:
            return None

    async def generate_quiz(self):
        topics = ["Python", "Cybersecurity", "Logic", "Science", "History"]
        topic = random.choice(topics)
        prompt = f"Create a multiple-choice quiz about {topic}. Format: QUESTION | A | B | C | D | CORRECT_INDEX (0-3)"
        try:
            response = await self.model.generate_content_async(prompt)
            parts = response.text.strip().split('|')
            if len(parts) >= 6:
                return {"question": parts[0].strip(), "options": [p.strip() for p in parts[1:5]], "correct_index": int(parts[5].strip())}
            return None
        except: return None