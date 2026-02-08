from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import aiosqlite
from src.database import DB_NAME, get_user_stats, get_last_plans

app = FastAPI()

# Папка, где будут лежать HTML файлы
templates = Jinja2Templates(directory="src/templates")

# Главная страница Mini App
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, user_id: int):
    # 1. Получаем данные из базы
    xp, level = await get_user_stats(user_id)
    plans = await get_last_plans(user_id, limit=10)
    
    # Считаем прогресс
    progress = xp % 100
    
    # 2. Отправляем их в HTML
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user_id": user_id,
        "xp": xp,
        "level": level,
        "progress": progress,
        "plans": plans
    })

# API для получения данных (если захочешь делать динамику через JS)
@app.get("/api/stats/{user_id}")
async def get_stats(user_id: int):
    xp, level = await get_user_stats(user_id)
    return {"xp": xp, "level": level}