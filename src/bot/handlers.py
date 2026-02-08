import io
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import ContextTypes
from src.services.ai_service import AIPlannerService
# Импортируем ВСЕ функции, включая старые для совместимости
from src.database import (
    save_plan, get_last_plans, add_rewards, get_user_profile, 
    get_leaderboard, update_user_meta, check_achievements_unlock, buy_item,
    get_user_stats, add_xp 
)

ai_service = AIPlannerService()
user_roles = {}
ROLES = {"standard": "Помощник", "coder": "Python Dev", "gym": "Тренер", "student": "Студент"}

# --- МЕНЮ И СТАРТ ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.username if user.username else user.first_name
    await update_user_meta(user.id, name)
    
    # 👇👇👇 ВСТАВЬ СВОЮ NGROK ССЫЛКУ 👇👇👇
    NGROK_URL = "https://arrythmic-improvisatory-angela.ngrok-free.dev"
    WEB_APP_URL = f"{NGROK_URL}?user_id={user.id}"
    
    keyboard = [
        [KeyboardButton("🚀 ОТКРЫТЬ MINI APP", web_app=WebAppInfo(url=WEB_APP_URL))],
        [KeyboardButton("🏪 Магазин"), KeyboardButton("📝 Новая задача")],
        [KeyboardButton("👤 Профиль"), KeyboardButton("🏆 Рейтинг")],
        [KeyboardButton("📂 История"), KeyboardButton("🎮 Мини-игра")]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f"Привет, {name}! v8.0: Экономика, Магазин и Ачивки! 🚀", reply_markup=markup)

# --- НОВЫЕ ФУНКЦИИ (Магазин, Лидерборд) ---
async def shop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    profile = await get_user_profile(user_id)
    
    text = f"🏪 **МАГАЗИН ТИТУЛОВ**\n💰 Твой баланс: **{profile['coins']} 🪙**\n\nВыбери титул:"
    items = [
        ("title_pro", "⚡ Продуктивный", 100),
        ("title_boss", "😎 Биг Босс", 300),
        ("title_cyber", "🤖 Кибер-Панк", 500),
        ("title_king", "👑 Король Python", 1000),
    ]
    buttons = []
    for slug, name, price in items:
        buttons.append([InlineKeyboardButton(f"{name} — {price} 🪙", callback_data=f"buy_{slug}_{price}_{name}")])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    p = await get_user_profile(user_id)
    achievements_str = ", ".join(p['achievements']) if p['achievements'] else "Нет"
    
    text = (
        f"👤 **{p['username']}**\n"
        f"🏷 Титул: **{p['active_title']}**\n"
        f"🏅 Уровень: **{p['level']}** ({p['xp']} XP)\n"
        f"💰 Монеты: **{p['coins']} 🪙**\n"
        f"🏆 Ачивки: {achievements_str}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    leaders = await get_leaderboard()
    text = "🏆 **ТОП ЛИДЕРОВ:**\n\n"
    for i, r in enumerate(leaders, 1):
        medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
        text += f"{medal} [{r['active_title']}] **{r['username']}** — {r['xp']} XP\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# --- СТАРЫЕ ВАЖНЫЕ ФУНКЦИИ (Возвращены!) ---
async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    plans = await get_last_plans(user_id)
    if not plans:
        await update.message.reply_text("История пуста.")
        return
    text = "📂 **Последние задачи:**\n\n"
    for r in plans:
        short_task = (r['task_text'][:30] + '..') if len(r['task_text']) > 30 else r['task_text']
        text += f"🔹 {short_task}\n"
    await update.message.reply_text(text)

async def play_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("🧠 Генерирую умный вопрос...")
    quiz_data = await ai_service.generate_quiz()
    if not quiz_data:
        await msg.edit_text("AI задумался... Попробуй еще раз.")
        return
    buttons = []
    for i, option in enumerate(quiz_data['options']):
        is_correct = "true" if i == quiz_data['correct_index'] else "false"
        buttons.append([InlineKeyboardButton(option, callback_data=f"quiz_{is_correct}")])
    await msg.edit_text(f"❓ **ВОПРОС:**\n{quiz_data['question']}", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

async def send_plan_response(update, plan_text, source_type, user_original_text):
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
    
    await update.message.reply_text(f"🎯 **План:**\n_{user_original_text}_\n\n👇 Отмечай пункты:", reply_markup=markup, parse_mode="Markdown")
    final_task_text = f"[{source_type}] {user_original_text}"
    await save_plan(user_id, final_task_text, plan_text)

# --- ОБРАБОТЧИКИ ТИПОВ СООБЩЕНИЙ ---
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user
    await update_user_meta(user.id, user.username or user.first_name)

    if text == "🏪 Магазин": return await shop_command(update, context)
    if text == "🏆 Рейтинг": return await leaderboard_command(update, context)
    if text == "🎮 Мини-игра": return await play_quiz(update, context)
    if text == "👤 Профиль": return await profile_command(update, context)
    if text == "📂 История": return await history_command(update, context)
    if text == "⏰ Таймер": return await update.message.reply_text("Используй: /remind 10m Текст")
    
    if text == "🎭 Сменить роль":
        keyboard = [[InlineKeyboardButton("👨‍💻 Кодер", callback_data="role_coder"), InlineKeyboardButton("💪 Тренер", callback_data="role_gym")]]
        return await update.message.reply_text("Выбери роль:", reply_markup=InlineKeyboardMarkup(keyboard))
    if text == "📝 Новая задача": return await update.message.reply_text("Напиши задачу текстом...")

    msg = await update.message.reply_text("🧠 Думаю...")
    role = user_roles.get(user.id, ROLES["standard"])
    plan = await ai_service.get_plan(user.id, text, role_prompt=role)
    await msg.delete()
    await send_plan_response(update, plan, "Текст", text)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("👀 Смотрю...")
    photo_file = await update.message.photo[-1].get_file()
    stream = io.BytesIO()
    await photo_file.download_to_memory(stream)
    stream.seek(0)
    
    role = user_roles.get(update.effective_user.id, ROLES["standard"])
    caption = update.message.caption or "Анализ фото"
    plan = await ai_service.get_plan(update.effective_user.id, caption, role_prompt=role, image_file=stream)
    await msg.delete()
    await send_plan_response(update, plan, "Фото", caption)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("👂 Слушаю...")
    voice_file = await update.message.voice.get_file()
    stream = io.BytesIO()
    await voice_file.download_to_memory(stream)
    stream.seek(0)
    role = user_roles.get(update.effective_user.id, ROLES["standard"])
    plan = await ai_service.get_plan(update.effective_user.id, "Голосовое сообщение", role_prompt=role, audio_file=stream)
    await msg.delete()
    await send_plan_response(update, plan, "Голос", "Голосовая задача")

# --- ОБРАБОТКА КНОПОК ---
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    data = query.data
    
    if data.startswith("buy_"):
        await query.answer()
        _, slug, price, name = data.split("_", 3)
        result = await buy_item(user_id, slug, name, int(price))
        await context.bot.send_message(user_id, result)
        return

    if data.startswith("quiz_"):
        is_correct = data.split("_")[1]
        if is_correct == "true":
            lvl_up, new_bal = await add_rewards(user_id, 20, 10) 
            msg = f"✅ Верно! (+20 XP, +10 🪙)"
            if lvl_up: msg += "\n🎉 **LEVEL UP!**"
        else:
            msg = "❌ Неверно."
        await query.edit_message_text(f"{query.message.text}\n\n{msg}", parse_mode="Markdown")
        return

    if data.startswith("check_"):
        await query.answer()
        markup = query.message.reply_markup
        new_kb = []
        for row in markup.inline_keyboard:
            btn = row[0]
            if btn.callback_data == data:
                txt = btn.text.replace("⬜", "✅") if "⬜" in btn.text else btn.text.replace("✅", "⬜")
                new_kb.append([InlineKeyboardButton(txt, callback_data=btn.callback_data)])
            else:
                new_kb.append([btn])
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(new_kb))
        return

    if data == "submit_task":
        checked = 0
        markup = query.message.reply_markup
        for row in markup.inline_keyboard:
            if "✅" in row[0].text: checked += 1
            if "⬜" in row[0].text: 
                await query.answer("❌ Доделай все пункты!", show_alert=True)
                return

        xp = checked * 10 + 50
        coins = checked * 5 + 20
        lvl_up, new_bal = await add_rewards(user_id, xp, coins)
        new_achievements = await check_achievements_unlock(user_id)
        
        res_text = f"🏆 **ЗАДАЧА ВЫПОЛНЕНА!**\n➕ {xp} XP\n➕ {coins} 🪙 Монет"
        if lvl_up: res_text += "\n🚀 **НОВЫЙ УРОВЕНЬ!**"
        if new_achievements: res_text += "\n\n🏅 **НОВАЯ АЧИВКА:** " + ", ".join(new_achievements)
        await query.edit_message_text(res_text, parse_mode="Markdown")
        
    if data.startswith("role_"):
        await query.answer("Роль изменена")

# --- ТАЙМЕР ---
async def alarm(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=context.job.chat_id, text=f"⏰ {context.job.data}")

async def remind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        t = context.args[0].lower()
        sec = int(t[:-1]) * (60 if 'm' in t else 3600 if 'h' in t else 1)
        msg = ' '.join(context.args[1:]) or "Время вышло!"
        context.job_queue.run_once(alarm, sec, chat_id=update.effective_chat.id, data=msg)
        await update.message.reply_text("✅ Таймер установлен")
    except: await update.message.reply_text("❌ Ошибка: /remind 10m Текст")