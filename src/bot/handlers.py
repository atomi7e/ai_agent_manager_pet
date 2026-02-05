import io
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from src.services.ai_service import AIPlannerService
from src.database import save_plan, get_last_plans, add_xp, get_user_stats

ai_service = AIPlannerService()

user_roles = {}
ROLES = {
    "standard": "Ты обычный помощник. Отвечай нейтрально и четко.",
    "coder": "Ты Senior Python Developer. Используй технические термины.",
    "gym": "Ты жесткий фитнес-тренер. Мотивируй агрессивно.",
    "student": "Ты студент старшего курса AITU. Общайся неформально."
}

# --- МЕНЮ С КНОПКОЙ ПРОФИЛЯ ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("📝 Новая задача"), KeyboardButton("📂 История")],
        [KeyboardButton("🎭 Сменить роль"), KeyboardButton("⏰ Таймер")],
        [KeyboardButton("👤 Профиль")] # <--- НОВАЯ КНОПКА
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! Я твой AI-помощник. 🚀\n"
        "Создавай задачи, выполняй их и прокачивай свой уровень!", 
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

# --- ЛОГИКА ПРОФИЛЯ ---
async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    xp, level = await get_user_stats(user_id)
    
    # Визуализация прогресса
    current_progress = xp % 100
    filled = current_progress // 10
    bar = "🟩" * filled + "⬜" * (10 - filled)
    
    text = (
        f"👤 **Твой Профиль**\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🏅 Уровень: **{level}**\n"
        f"✨ Опыт: **{xp} XP**\n"
        f"📊 Прогресс: [{bar}] {current_progress}/100\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"Выполняй задачи и жми 'Сдать', чтобы получить XP!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def alarm(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    await context.bot.send_message(chat_id=job.chat_id, text=f"⏰ НАПОМИНАНИЕ: {job.data}")

async def remind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_message.chat_id
    try:
        if not context.args: return await update.message.reply_text("Пример: /remind 10m Текст")
        time_str = context.args[0].lower()
        message = ' '.join(context.args[1:]) if len(context.args) > 1 else "Время вышло!"
        seconds = 0
        if time_str.endswith("s"): seconds = int(time_str[:-1])
        elif time_str.endswith("m"): seconds = int(time_str[:-1]) * 60
        elif time_str.endswith("h"): seconds = int(time_str[:-1]) * 3600
        else: return await update.message.reply_text("Ошибка формата времени.")
        context.job_queue.run_once(alarm, seconds, chat_id=chat_id, data=message)
        await update.message.reply_text(f"✅ Таймер установлен!")
    except: await update.message.reply_text("❌ Ошибка.")

async def send_plan_response(update, plan_text, task_source):
    user_id = update.effective_user.id
    buttons = []
    lines = plan_text.split('\n')
    
    for i, line in enumerate(lines):
        clean_line = line.strip().strip('-').strip()
        if clean_line:
            buttons.append([InlineKeyboardButton(f"⬜ {clean_line}", callback_data=f"check_{i}")])
    
    if buttons:
        buttons.append([InlineKeyboardButton("🚀 СДАТЬ ЗАДАЧУ (+XP)", callback_data="submit_task")])

    markup = InlineKeyboardMarkup(buttons) if buttons else None
    await update.message.reply_text(f"🎯 **План ({task_source}):**\nОтмечай пункты и жми 'Сдать'!", reply_markup=markup, parse_mode="Markdown")
    await save_plan(user_id, f"[{task_source}]", plan_text)

# --- ОБРАБОТЧИКИ ТЕКСТА (С КНОПКОЙ ПРОФИЛЯ) ---
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "👤 Профиль": return await profile_command(update, context) # <--- ОБРАБОТКА НАЖАТИЯ
    if text == "📂 История": return await history_command(update, context)
    if text == "⏰ Таймер": return await update.message.reply_text("Пиши /remind 10m Текст")
    if text == "🎭 Сменить роль":
        keyboard = [[InlineKeyboardButton("👨‍💻 Кодер", callback_data="role_coder"), InlineKeyboardButton("💪 Тренер", callback_data="role_gym")],
                    [InlineKeyboardButton("🎓 Студент", callback_data="role_student"), InlineKeyboardButton("😐 Стандарт", callback_data="role_standard")]]
        return await update.message.reply_text("Выбери роль:", reply_markup=InlineKeyboardMarkup(keyboard))
    if text == "📝 Новая задача": return await update.message.reply_text("Пиши задачу или шли голосовое.")

    msg = await update.message.reply_text("🧠 Думаю...")
    role = user_roles.get(user_id, ROLES["standard"])
    plan = await ai_service.get_plan(user_id, text, role_prompt=role)
    await msg.delete()
    await send_plan_response(update, plan, "Текст")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("👀 Смотрю...")
    photo_file = await update.message.photo[-1].get_file()
    stream = io.BytesIO()
    await photo_file.download_to_memory(stream)
    stream.seek(0)
    role = user_roles.get(update.effective_user.id, ROLES["standard"])
    text = update.message.caption or "Составь план"
    plan = await ai_service.get_plan(update.effective_user.id, text, role_prompt=role, image_file=stream)
    await msg.delete()
    await send_plan_response(update, plan, "Фото")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("👂 Слушаю...")
    voice_file = await update.message.voice.get_file()
    stream = io.BytesIO()
    await voice_file.download_to_memory(stream)
    stream.seek(0)
    role = user_roles.get(update.effective_user.id, ROLES["standard"])
    plan = await ai_service.get_plan(update.effective_user.id, "Голосовое сообщение", role_prompt=role, audio_file=stream)
    await msg.delete()
    await send_plan_response(update, plan, "Голос")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    data = query.data
    
    if data.startswith("role_"):
        await query.answer()
        role_key = data.split("_")[1]
        user_roles[user_id] = ROLES.get(role_key, ROLES["standard"])
        await query.edit_message_text(f"✅ Роль: **{role_key.upper()}**")
        return

    if data.startswith("check_"):
        await query.answer()
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
        return

    if data == "submit_task":
        current_markup = query.message.reply_markup
        all_checked = True
        total_items = 0
        
        for row in current_markup.inline_keyboard:
            btn = row[0]
            if btn.callback_data.startswith("check_"):
                total_items += 1
                if "⬜" in btn.text:
                    all_checked = False
        
        if not all_checked:
            await query.answer("❌ Сначала выполни все пункты!", show_alert=True)
        else:
            xp_reward = total_items * 10 + 50
            leveled_up = await add_xp(user_id, xp_reward)
            
            await query.edit_message_text(f"🏆 **ЗАДАЧА ВЫПОЛНЕНА!**\n\nТы получил: **+{xp_reward} XP**")
            
            if leveled_up:
                await context.bot.send_message(chat_id=user_id, text="🎉 **НОВЫЙ УРОВЕНЬ!** Поздравляю! 🚀")
            else:
                await query.answer(f"+{xp_reward} XP получено.", show_alert=False)