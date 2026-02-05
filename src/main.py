import sys
import os
import asyncio # Добавляем asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from src.config import TELEGRAM_TOKEN
# Импортируем новые функции
from src.bot.handlers import start_command, handle_text_message, history_command
from src.database import init_db

def main():
    # 1. Инициализируем базу данных перед запуском бота
    # Поскольку init_db асинхронная, запускаем её через asyncio.run
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())

    # 2. Настраиваем бота
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("history", history_command)) # Новая команда
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    print("Бот Planner запущен (с базой данных)...")
    app.run_polling()

if __name__ == "__main__":
    main()