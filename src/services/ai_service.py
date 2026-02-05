import google.generativeai as genai
from src.config import GEMINI_API_KEY

class AIPlannerService:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction="""
            Ты — AI-планировщик. Твоя задача — разбивать цели на шаги.
            Форматирование: используй Markdown (жирный шрифт, списки).
            Будь краток и структурирован.
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
            return f"Ошибка AI сервиса: {str(e)}"