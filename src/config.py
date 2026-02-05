import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("AIzaSyBQyDlF0KQTHE3fngDFSScvvAfPh7DG51c")
TELEGRAM_TOKEN = os.getenv("8227175656:AAG0W7Z7YLLL8M_cQGU3jBL5HkRCdIoicCA")

if not GEMINI_API_KEY or not TELEGRAM_TOKEN:
    raise ValueError("Ошибка: Проверьте API ключи в файле .env")