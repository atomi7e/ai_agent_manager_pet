from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from src.services.ai_service import AIPlannerService
from src.database import save_plan, get_last_plans

# Инициализируем сервис
ai_service = AIPlannerService()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает приветствие и кнопки"""
    
    # 1. Создаем кнопки
    keyboard = [
        [KeyboardButton("📝 Новая задача"), KeyboardButton("📂 История")]
    ]
    # resize_keyboard=True делает кнопки компактными
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    user_name = update.effective_user.first_name
    
    # 2. Отправляем сообщение с клавиатурой
    await update.message.reply_text(
        f"Привет, {user_name}! 👋\n"
        "Я готов планировать. Нажми кнопку или просто напиши задачу.",
        reply_markup=markup
    )

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает историю задач"""
    user_id = update.effective_user.id
    plans = await get_last_plans(user_id)
    
    if not plans:
        await update.message.reply_text("У вас пока нет сохраненных планов.")
        return

    text = "📂 **Ваши последние задачи:**\n\n"
    for row in plans:
        # row['task_text'] - это текст задачи, row['created_at'] - дата
        text += f"🔹 {row['task_text']}\n"
    
    await update.message.reply_text(text)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает текст И нажатия кнопок"""
    user_id = update.effective_user.id
    text = update.message.text

    # --- ЛОГИКА КНОПОК ---
    
    if text == "📂 История":
        # Если нажали кнопку "История", вызываем функцию истории
        await history_command(update, context)
        return

    if text == "📝 Новая задача":
        # Если нажали "Новая задача", просто даем инструкцию
        await update.message.reply_text("Просто напиши мне свою цель, например:\n\n'Как подготовиться к марафону' или 'Выучить SQL за неделю'.")
        return

    # --- ЛОГИКА AI (если это не кнопки) ---

    # Показываем статус "печатает..."
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # 1. Генерируем ответ
    response_text = await ai_service.get_plan(user_id, text)
    
    # 2. Сохраняем
    await save_plan(user_id, text, response_text)
    
    # 3. Отправляем ответ
    await update.message.reply_text(response_text)