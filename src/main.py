import sys
import os
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from src.config import TELEGRAM_TOKEN
from src.database import init_db

from src.bot.handlers import (
    start_command, 
    handle_text_message, 
    history_command, 
    button_click, 
    remind_command,
    handle_photo,
    handle_voice,
    profile_command # <--- ВАЖНО
)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def post_init(application):
    await init_db()
    print("✅ База данных подключена!")

def main():
    print("🚀 Запускаю бота (v6.0 - Profile Button)...")
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN)\
        .post_init(post_init)\
        .connect_timeout(30)\
        .read_timeout(30)\
        .write_timeout(30)\
        .build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("remind", remind_command))
    app.add_handler(CommandHandler("profile", profile_command))
    
    app.add_handler(CallbackQueryHandler(button_click))
    
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    print("✅ Бот готов!")
    app.run_polling()

if __name__ == '__main__':
    main()