# Файл: fix_env.py
import os

# --- ВСТАВЬ СЮДА СВОИ КЛЮЧИ ВНУТРЬ КАВЫЧЕК ---
GEMINI_KEY = "AIzaSyBQyDlF0KQTHE3fngDFSScvvAfPh7DG51c"
TELEGRAM_TOKEN = "8227175656:AAG0W7Z7YLLL8M_cQGU3jBL5HkRCdIoicCA"

content = f"GEMINI_API_KEY={GEMINI_KEY}\nTELEGRAM_BOT_TOKEN={TELEGRAM_TOKEN}"

# Python сам запишет файл в правильной кодировке UTF-8
with open(".env", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Файл .env успешно перезаписан в кодировке UTF-8!")