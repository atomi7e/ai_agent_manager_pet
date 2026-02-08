import aiosqlite

DB_NAME = "planner.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # 1. Таблица задач
        await db.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task_text TEXT,
                plan_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Таблица пользователей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT, 
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                coins INTEGER DEFAULT 0,
                active_title TEXT DEFAULT 'Новичок'
            )
        """)
        
        # 3. Таблица Ачивок
        await db.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                user_id INTEGER,
                slug TEXT,
                name TEXT,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, slug)
            )
        """)

        # 4. Таблица Инвентаря (Покупки)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                user_id INTEGER,
                item_slug TEXT,
                item_type TEXT,
                UNIQUE(user_id, item_slug)
            )
        """)

        # Миграции (добавляем колонки, если их нет)
        try: await db.execute("ALTER TABLE users ADD COLUMN username TEXT")
        except: pass
        try: await db.execute("ALTER TABLE users ADD COLUMN coins INTEGER DEFAULT 0")
        except: pass
        try: await db.execute("ALTER TABLE users ADD COLUMN active_title TEXT DEFAULT 'Новичок'")
        except: pass
        
        await db.commit()

# --- ФУНКЦИИ ЗАДАЧ ---
async def save_plan(user_id: int, task: str, plan: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO plans (user_id, task_text, plan_response) VALUES (?, ?, ?)", (user_id, task, plan))
        await db.commit()

async def get_last_plans(user_id: int, limit=10):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT task_text, created_at FROM plans WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit))
        return await cursor.fetchall()

async def update_user_meta(user_id: int, username: str):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
        if await cursor.fetchone():
            await db.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
        else:
            await db.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        await db.commit()

# --- ГЕЙМИФИКАЦИЯ ---

async def get_user_profile(user_id: int):
    """Возвращает полный профиль (для бота и Mini App)"""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()
            if not user: 
                # Если юзера нет, возвращаем заглушку
                return {"username": "Guest", "xp": 0, "level": 1, "coins": 0, "active_title": "Ghost", "achievements": []}
            
        async with db.execute("SELECT name FROM achievements WHERE user_id = ?", (user_id,)) as cursor:
            achievements = [row['name'] for row in await cursor.fetchall()]

        return {
            "username": user['username'],
            "xp": user['xp'],
            "level": user['level'],
            "coins": user['coins'],
            "active_title": user['active_title'],
            "achievements": achievements
        }

async def add_rewards(user_id: int, xp_amount: int, coins_amount: int):
    """Начисляет награды и проверяет Level Up"""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT xp, level, coins FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row: return False, 0
            
            cur_xp, cur_lvl, cur_coins = row['xp'], row['level'], row['coins']

        new_xp = cur_xp + xp_amount
        new_coins = cur_coins + coins_amount
        new_lvl = (new_xp // 100) + 1
        
        await db.execute("UPDATE users SET xp = ?, level = ?, coins = ? WHERE user_id = ?", 
                         (new_xp, new_lvl, new_coins, user_id))
        await db.commit()
        
        return (new_lvl > cur_lvl), new_coins

async def check_achievements_unlock(user_id: int):
    """Проверяет условия для ачивок"""
    new_unlocks = []
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT count(*) as cnt FROM plans WHERE user_id = ?", (user_id,)) as c:
            task_count = (await c.fetchone())[0]
        
        conditions = [
            ("first_step", "👶 Первые шаги", task_count >= 1),
            ("worker", "🔨 Трудяга (5 задач)", task_count >= 5),
            ("machine", "🤖 Машина (10 задач)", task_count >= 10),
        ]

        for slug, name, condition in conditions:
            if condition:
                try:
                    await db.execute("INSERT INTO achievements (user_id, slug, name) VALUES (?, ?, ?)", (user_id, slug, name))
                    new_unlocks.append(name)
                except:
                    pass 
        await db.commit()
    return new_unlocks

async def buy_item(user_id: int, item_slug: str, item_name: str, cost: int, item_type="title"):
    """Покупка предмета"""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        
        # Проверка баланса
        async with db.execute("SELECT coins FROM users WHERE user_id = ?", (user_id,)) as c:
            row = await c.fetchone()
            if not row or row['coins'] < cost: return "❌ Недостаточно монет!"

        # Проверка наличия
        async with db.execute("SELECT 1 FROM inventory WHERE user_id = ? AND item_slug = ?", (user_id, item_slug)) as c:
            if await c.fetchone(): return "✅ У тебя это уже есть!"

        # Транзакция
        try:
            await db.execute("UPDATE users SET coins = coins - ? WHERE user_id = ?", (cost, user_id))
            await db.execute("INSERT INTO inventory (user_id, item_slug, item_type) VALUES (?, ?, ?)", (user_id, item_slug, item_type))
            if item_type == "title":
                await db.execute("UPDATE users SET active_title = ? WHERE user_id = ?", (item_name, user_id))
            await db.commit()
            return f"🎉 Куплено: **{item_name}**!"
        except Exception as e:
            return f"Ошибка: {e}"

async def get_leaderboard(limit=10):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT username, xp, level, active_title FROM users ORDER BY xp DESC LIMIT ?", (limit,))
        return await cursor.fetchall()

# --- ФУНКЦИИ ДЛЯ СОВМЕСТИМОСТИ (Чтобы не ломались старые импорты) ---
async def get_user_stats(user_id: int):
    p = await get_user_profile(user_id)
    return p['xp'], p['level']

async def add_xp(user_id: int, amount: int):
    lvl_up, _ = await add_rewards(user_id, amount, 0)
    return lvl_up