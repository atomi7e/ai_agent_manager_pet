# Файл: src/bot/handlers.py
from telegram import Update
from telegram.ext import ContextTypes
from src.services.ai_service import AIPlannerService
from src.database import save_plan, get_last_plans

# Инициализируем сервис
ai_service = AIPlannerService()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Привет, {user_name}! 👋\n"
        "Я готов планировать. Просто напиши свою задачу.\n"
        "Посмотреть историю: /history"
    )

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /history"""
    user_id = update.effective_user.id
    plans = await get_last_plans(user_id)
    
    if not plans:
        await update.message.reply_text("У вас пока нет сохраненных планов.")
        return

    text = "📂 Ваши последние задачи:\n\n"
    for row in plans:
        text += f"• {row['task_text']}\n"
    
    await update.message.reply_text(text)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text

    # Показываем, что бот печатает
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # 1. Генерируем ответ (AI)
    response_text = await ai_service.get_plan(user_id, text)
    
    # 2. Сохраняем в базу данных
    await save_plan(user_id, text, response_text)
    
    # 3. Отправляем ответ пользователю
    # ВАЖНО: Мы убрали parse_mode, чтобы не было ошибок Telegram
    await update.message.reply_text(response_text)