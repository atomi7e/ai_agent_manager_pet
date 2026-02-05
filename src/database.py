import aiosqlite

DB_NAME = "planner.db"

async def init_db():
    """Создает таблицу, если её нет"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                task_text TEXT,
                plan_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def save_plan(user_id: int, task: str, plan: str):
    """Сохраняет новый план в базу"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO plans (user_id, task_text, plan_response) VALUES (?, ?, ?)",
            (user_id, task, plan)
        )
        await db.commit()

async def get_last_plans(user_id: int, limit=5):
    """Возвращает последние 5 задач пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT task_text, created_at FROM plans WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        )
        rows = await cursor.fetchall()
        return rows