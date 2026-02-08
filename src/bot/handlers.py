import io
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import ContextTypes
from src.services.ai_service import AIPlannerService
from src.database import save_plan, get_last_plans, add_xp, get_user_stats, get_leaderboard, update_user_meta

ai_service = AIPlannerService()

# Временная память для ролей
user_roles = {}

ROLES = {
    "standard": "Ты обычный помощник. Отвечай нейтрально и четко.",
    "coder": "Ты Senior Python Developer. Используй технические термины, советуй библиотеки.",
    "gym": "Ты жесткий фитнес-тренер. Мотивируй агрессивно, используй сленг.",
    "student": "Ты студент старшего курса AITU. Шаришь за дедлайны. Общайся неформально."
}

# --- МЕНЮ И КОМАНДЫ ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню с кнопкой Mini App"""
    user = update.effective_user
    # Обновляем имя пользователя в базе (чтобы в рейтинге было имя)
    name = user.username if user.username else user.first_name
    await update_user_meta(user.id, name)
    
    # ⚠️ ВСТАВЬ СЮДА СВОЮ ССЫЛКУ ОТ NGROK ⚠️
    # Пример: "https://a1b2-c3d4.ngrok-free.app"
    NGROK_URL = "https://arrythmic-improvisatory-angela.ngrok-free.dev" 
    
    WEB_APP_URL = f"{NGROK_URL}?user_id={user.id}"
    
    keyboard = [
        # Кнопка открытия Mini App
        [KeyboardButton("🚀 ОТКРЫТЬ MINI APP", web_app=WebAppInfo(url=WEB_APP_URL))],
        
        [KeyboardButton("📝 Новая задача"), KeyboardButton("🎮 Мини-игра")],
        [KeyboardButton("👤 Профиль"), KeyboardButton("🏆 Рейтинг")],
        [KeyboardButton("📂 История"), KeyboardButton("🎭 Сменить роль")]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"Привет, {name}! Я твой AI-агент v7.0.\n"
        "Теперь у нас есть веб-интерфейс, игры и рейтинг! 🚀",
        reply_markup=markup
    )

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает топ пользователей"""
    leaders = await get_leaderboard()
    text = "🏆 **ТОП ПРОДУКТИВНЫХ:**\n\n"
    
    for i, row in enumerate(leaders, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} **{row['username']}** — {row['xp']} XP (Lvl {row['level']})\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает профиль текстом"""
    user_id = update.effective_user.id
    xp, level = await get_user_stats(user_id)
    
    current_progress = xp % 100
    filled = current_progress // 10
    bar = "🟩" * filled + "⬜" * (10 - filled)
    
    text = (
        f"👤 **Твой Профиль**\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🏅 Уровень: **{level}**\n"
        f"✨ Опыт: **{xp} XP**\n"
        f"📊 Прогресс: [{bar}] {current_progress}/100"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    plans = await get_last_plans(user_id)
    if not plans:
        await update.message.reply_text("История пуста.")
        return
    text = "📂 **Последние задачи:**\n" + "\n".join([f"• {r['task_text']}" for r in plans])
    await update.message.reply_text(text)

# --- ИГРЫ И ЗАДАЧИ ---

async def play_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запускает мини-игру"""
    msg = await update.message.reply_text("🧠 Генерирую умный вопрос...")
    
    quiz_data = await ai_service.generate_quiz()
    
    if not quiz_data:
        await msg.edit_text("AI задумался... Попробуй еще раз.")
        return

    buttons = []
    # Варианты ответов
    for i, option in enumerate(quiz_data['options']):
        # В callback_data прячем правильный ответ (true/false)
        is_correct = "true" if i == quiz_data['correct_index'] else "false"
        buttons.append([InlineKeyboardButton(option, callback_data=f"quiz_{is_correct}")])
    
    await msg.edit_text(
        f"❓ **ВОПРОС:**\n{quiz_data['question']}",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )

async def send_plan_response(update, plan_text, task_source):
    """Универсальная отправка плана с кнопкой проверки"""
    user_id = update.effective_user.id
    buttons = []
    lines = plan_text.split('\n')
    
    # Кнопки для пунктов
    for i, line in enumerate(lines):
        clean_line = line.strip().strip('-').strip()
        if clean_line:
            buttons.append([InlineKeyboardButton(f"⬜ {clean_line}", callback_data=f"check_{i}")])
    
    # Кнопка сдачи
    if buttons:
        buttons.append([InlineKeyboardButton("🚀 СДАТЬ ЗАДАЧУ (+XP)", callback_data="submit_task")])

    markup = InlineKeyboardMarkup(buttons) if buttons else None
    await update.message.reply_text(
        f"🎯 **План ({task_source}):**\nОтмечай пункты и жми 'Сдать'!", 
        reply_markup=markup, 
        parse_mode="Markdown"
    )
    await save_plan(user_id, f"[{task_source}]", plan_text)

# --- ОБРАБОТЧИКИ СООБЩЕНИЙ ---

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user
    # Обновляем метаданные при каждом сообщении
    await update_user_meta(user.id, user.username or user.first_name)

    # Роутинг команд меню
    if text == "🏆 Рейтинг": return await leaderboard_command(update, context)
    if text == "🎮 Мини-игра": return await play_quiz(update, context)
    if text == "👤 Профиль": return await profile_command(update, context)
    if text == "📂 История": return await history_command(update, context)
    if text == "⏰ Таймер": return await update.message.reply_text("Используй: /remind 10m Текст")
    
    if text == "🎭 Сменить роль":
        keyboard = [
            [InlineKeyboardButton("👨‍💻 Кодер", callback_data="role_coder"), InlineKeyboardButton("💪 Тренер", callback_data="role_gym")],
            [InlineKeyboardButton("🎓 Студент", callback_data="role_student"), InlineKeyboardButton("😐 Стандарт", callback_data="role_standard")]
        ]
        return await update.message.reply_text("Выбери роль:", reply_markup=InlineKeyboardMarkup(keyboard))
        
    if text == "📝 Новая задача": return await update.message.reply_text("Напиши задачу текстом или отправь фото/голосовое.")

    # Если просто текст -> AI Планировщик
    msg = await update.message.reply_text("🧠 Думаю...")
    role = user_roles.get(user.id, ROLES["standard"])
    plan = await ai_service.get_plan(user.id, text, role_prompt=role)
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

# --- ОБРАБОТКА КНОПОК ---

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    data = query.data
    
    # 1. Ответ на квиз
    if data.startswith("quiz_"):
        is_correct = data.split("_")[1]
        if is_correct == "true":
            leveled = await add_xp(user_id, 20)
            res_text = "✅ **ПРАВИЛЬНО!** (+20 XP)"
            if leveled: res_text += "\n🎉 **НОВЫЙ УРОВЕНЬ!**"
        else:
            res_text = "❌ **Неверно.** Опыт не получен."
        
        await query.edit_message_text(f"{query.message.text}\n\n{res_text}", parse_mode="Markdown")
        return

    # 2. Смена роли
    if data.startswith("role_"):
        await query.answer()
        role_key = data.split("_")[1]
        user_roles[user_id] = ROLES.get(role_key, ROLES["standard"])
        await query.edit_message_text(f"✅ Роль изменена на: **{role_key.upper()}**")
        return

    # 3. Галочки (Чек-боксы)
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

    # 4. Сдача задачи (Верификация)
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
            await query.answer("❌ Выполни все пункты перед сдачей!", show_alert=True)
        else:
            xp_reward = total_items * 10 + 50 # 10 за пункт + 50 бонус
            leveled = await add_xp(user_id, xp_reward)
            
            msg = f"🏆 **ЗАДАЧА ВЫПОЛНЕНА!**\nТы получил: **+{xp_reward} XP**"
            if leveled: msg += "\n🎉 **LEVEL UP!** Поздравляю! 🚀"
            
            await query.edit_message_text(msg, parse_mode="Markdown")

# --- ТАЙМЕР ---
async def alarm(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    await context.bot.send_message(chat_id=job.chat_id, text=f"⏰ НАПОМИНАНИЕ: {job.data}")

async def remind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_message.chat_id
    try:
        if not context.args: return await update.message.reply_text("Пример: /remind 10m Попить воды")
        time_str = context.args[0].lower()
        message = ' '.join(context.args[1:]) if len(context.args) > 1 else "Время вышло!"
        seconds = 0
        if time_str.endswith("s"): seconds = int(time_str[:-1])
        elif time_str.endswith("m"): seconds = int(time_str[:-1]) * 60
        elif time_str.endswith("h"): seconds = int(time_str[:-1]) * 3600
        else: return await update.message.reply_text("Формат: 10s, 5m, 1h.")
        
        context.job_queue.run_once(alarm, seconds, chat_id=chat_id, data=message)
        await update.message.reply_text(f"✅ Таймер на {time_str} установлен!")
    except: await update.message.reply_text("❌ Ошибка формата.")