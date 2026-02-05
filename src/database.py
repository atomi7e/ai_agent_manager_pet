import aiosqlite

DB_NAME = "planner.db"

async def init_db():
    """Создает таблицы, если их нет"""
    async with aiosqlite.connect(DB_NAME) as db:
        # Таблица задач
        await db.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task_text TEXT,
                plan_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # --- ТАБЛИЦА ПРОФИЛЯ (XP и Уровни) ---
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1
            )
        """)
        await db.commit()

async def save_plan(user_id: int, task: str, plan: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO plans (user_id, task_text, plan_response) VALUES (?, ?, ?)",
            (user_id, task, plan)
        )
        await db.commit()

async def get_last_plans(user_id: int, limit=5):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT task_text, created_at FROM plans WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        )
        return await cursor.fetchall()

# --- ФУНКЦИИ ДЛЯ ОПЫТА ---
async def get_user_stats(user_id: int):
    """Получает статистику юзера"""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT xp, level FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row['xp'], row['level']
            else:
                await db.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
                await db.commit()
                return 0, 1

async def add_xp(user_id: int, amount: int):
    """Начисляет XP"""
    async with aiosqlite.connect(DB_NAME) as db:
        xp, level = await get_user_stats(user_id)
        new_xp = xp + amount
        new_level = (new_xp // 100) + 1 
        
        await db.execute("UPDATE users SET xp = ?, level = ? WHERE user_id = ?", (new_xp, new_level, user_id))
        await db.commit()
        
        return new_level > level