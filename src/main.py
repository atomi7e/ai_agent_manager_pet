import sys
import os
import asyncio
import logging

# --- 🛠 ИСПРАВЛЕНИЕ ОШИБКИ ИМПОРТА ---
# Это говорит Питону: "Ищи модули не только здесь, но и в папке уровнем выше"
# Без этого он не видит папку 'src', когда ты запускаешь main.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# -------------------------------------

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from src.config import TELEGRAM_TOKEN
from src.bot.handlers import start_command, handle_text_message, history_command
from src.database import init_db

# Настройка логов
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    # 1. Запускаем базу данных
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())

    # 2. Создаем бота с защитой от плохого интернета
    print("🚀 Запускаю бота...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN)\
        .connect_timeout(30)\
        .read_timeout(30)\
        .write_timeout(30)\
        .build()

    # 3. Подключаем функции
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    print("✅ Бот успешно запущен! Напиши ему в Telegram.")
    
    # 4. Поехали!
    app.run_polling()

if __name__ == '__main__':
    main()