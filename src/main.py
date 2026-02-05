import sys
import os
import asyncio
import logging

# --- 🛠 ВАЖНО: ЛЕЧИМ ОШИБКУ ModuleNotFoundError ---
# Эта строка помогает Python видеть весь проект целиком,
# даже если ты запускаешь файл из другой папки.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# --------------------------------------------------

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from src.config import TELEGRAM_TOKEN

# Импортируем все наши функции, включая новую remind_command
from src.bot.handlers import (
    start_command, 
    handle_text_message, 
    history_command, 
    button_click, 
    remind_command
)
from src.database import init_db

# Настройка логов (чтобы видеть ошибки в консоли)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    # 1. Запускаем базу данных
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())

    print("🚀 Запускаю бота (AI Agent v3.0)...")
    
    # 2. Создаем бота с защитой от ошибок сети
    # Увеличенные тайм-ауты спасают, если интернет медленный или VPN лагает
    app = ApplicationBuilder().token(TELEGRAM_TOKEN)\
        .connect_timeout(30)\
        .read_timeout(30)\
        .write_timeout(30)\
        .build()

    # 3. Регистрируем команды и обработчики
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("remind", remind_command)) # Таймер
    
    # Обработчик нажатий на кнопки (галочки, выбор роли)
    app.add_handler(CallbackQueryHandler(button_click))
    
    # Обработчик обычного текста (общение с AI)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    print("✅ Бот успешно запущен! Можно писать в Telegram.")
    
    # 4. Поехали!
    app.run_polling()

if __name__ == '__main__':
    main()