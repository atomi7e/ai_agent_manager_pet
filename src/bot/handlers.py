from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from src.services.ai_service import AIPlannerService
from src.database import save_plan, get_last_plans

ai_service = AIPlannerService()

# Временная память для ролей
user_roles = {}

ROLES = {
    "standard": "Ты обычный помощник. Отвечай нейтрально и четко.",
    "coder": "Ты Senior Python Developer. Используй технические термины, советуй библиотеки.",
    "gym": "Ты жесткий фитнес-тренер. Мотивируй агрессивно, используй сленг.",
    "student": "Ты студент старшего курса AITU. Шаришь за дедлайны. Общайся неформально."
}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню"""
    keyboard = [
        [KeyboardButton("📝 Новая задача"), KeyboardButton("📂 История")],
        [KeyboardButton("🎭 Сменить роль"), KeyboardButton("⏰ Таймер")] # Добавили кнопку
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Привет! Я твой AI-агент. 👋\nВыбери действие в меню:",
        reply_markup=markup
    )

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    plans = await get_last_plans(user_id)
    if not plans:
        await update.message.reply_text("История пуста.")
        return
    text = "📂 **Последние задачи:**\n" + "\n".join([f"• {r['task_text']}" for r in plans])
    await update.message.reply_text(text)

async def alarm(context: ContextTypes.DEFAULT_TYPE):
    """Срабатывание таймера"""
    job = context.job
    await context.bot.send_message(chat_id=job.chat_id, text=f"⏰ НАПОМИНАНИЕ: {job.data}")

async def remind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /remind"""
    chat_id = update.effective_message.chat_id
    try:
        if not context.args:
            await update.message.reply_text("Использование: /remind 10m Текст")
            return

        time_str = context.args[0].lower()
        message = ' '.join(context.args[1:]) if len(context.args) > 1 else "Время вышло!"
        
        seconds = 0
        if time_str.endswith("s"): seconds = int(time_str[:-1])
        elif time_str.endswith("m"): seconds = int(time_str[:-1]) * 60
        elif time_str.endswith("h"): seconds = int(time_str[:-1]) * 3600
        else:
            await update.message.reply_text("⚠️ Формат: 10s (сек), 5m (мин), 1h (час).")
            return

        context.job_queue.run_once(alarm, seconds, chat_id=chat_id, data=message)
        await update.message.reply_text(f"✅ Таймер на {time_str} установлен!\nТекст: {message}")

    except (IndexError, ValueError):
        await update.message.reply_text("❌ Ошибка формата. Пример: /remind 5m Чай")

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    # --- 1. ОБРАБОТКА МЕНЮ ---
    if text == "📂 История":
        await history_command(update, context)
        return
    
    if text == "⏰ Таймер":
        # Инструкция для пользователя при нажатии кнопки
        await update.message.reply_text(
            "⏳ **Как поставить напоминание:**\n\n"
            "Используй команду `/remind` + время + текст.\n"
            "Примеры:\n"
            "• `/remind 10m Выключить пельмени` (10 минут)\n"
            "• `/remind 1h Позвонить маме` (1 час)\n"
            "• `/remind 30s Тест` (30 секунд)",
            parse_mode="Markdown"
        )
        return

    if text == "🎭 Сменить роль":
        keyboard = [
            [InlineKeyboardButton("👨‍💻 Кодер", callback_data="role_coder"), InlineKeyboardButton("💪 Тренер", callback_data="role_gym")],
            [InlineKeyboardButton("🎓 Студент", callback_data="role_student"), InlineKeyboardButton("😐 Стандарт", callback_data="role_standard")],
        ]
        await update.message.reply_text("Выбери режим общения:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if text == "📝 Новая задача":
        await update.message.reply_text("Напиши свою цель, и я составлю план.")
        return

    # --- 2. AI ГЕНЕРАЦИЯ ---
    current_role_prompt = user_roles.get(user_id, ROLES["standard"])
    
    msg = await update.message.reply_text(f"🧠 Думаю... ({get_role_name(current_role_prompt)})")
    plan_text = await ai_service.get_plan(user_id, text, role_prompt=current_role_prompt)
    
    # Создаем чек-лист
    buttons = []
    lines = plan_text.split('\n')
    for i, line in enumerate(lines):
        clean_line = line.strip().strip('-').strip()
        if clean_line:
            buttons.append([InlineKeyboardButton(f"⬜ {clean_line}", callback_data=f"done_{i}")])

    if not buttons:
        await msg.edit_text(plan_text)
    else:
        await msg.edit_text(
            f"🎯 План: **{text}**",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown"
        )
    
    await save_plan(user_id, text, plan_text)

def get_role_name(prompt):
    if prompt == ROLES["coder"]: return "Кодер 👨‍💻"
    if prompt == ROLES["gym"]: return "Тренер 💪"
    if prompt == ROLES["student"]: return "Студент 🎓"
    return "Обычный"

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id

    if data.startswith("role_"):
        role_key = data.split("_")[1]
        user_roles[user_id] = ROLES.get(role_key, ROLES["standard"])
        await query.edit_message_text(f"✅ Роль изменена на: **{role_key.upper()}**")
        return

    if data.startswith("done_"):
        current_markup = query.message.reply_markup
        new_keyboard = []
        for row in current_markup.inline_keyboard:
            btn = row[0]
            if btn.callback_data == data:
                new_text = btn.text.replace("⬜", "✅") if "⬜" in btn.text else btn.text.replace("✅", "⬜")
                new_keyboard.append([InlineKeyboardButton(new_text, callback_data=btn.callback_data)])
            else:
                new_keyboard.append([btn])
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(new_keyboard))