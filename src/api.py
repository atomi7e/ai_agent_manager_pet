from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from src.database import (
    get_user_profile, get_last_plans, complete_plan_db, add_rewards, 
    get_weekly_stats, get_leaderboard, buy_item, save_plan
)
from src.services.ai_service import AIPlannerService

app = FastAPI()
templates = Jinja2Templates(directory="src/templates")
ai_service = AIPlannerService()

# Список товаров (Единый источник правды)
SHOP_ITEMS = [
    {"slug": "title_pro", "name": "⚡ Продуктивный", "price": 100},
    {"slug": "title_boss", "name": "😎 Биг Босс", "price": 300},
    {"slug": "title_cyber", "name": "🤖 Кибер-Панк", "price": 500},
    {"slug": "title_king", "name": "👑 Король Python", "price": 1000},
]

class CreateTaskRequest(BaseModel):
    user_id: int
    text: str

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, user_id: int):
    user_data = await get_user_profile(user_id)
    plans = await get_last_plans(user_id, limit=20)
    chart_labels, chart_data = await get_weekly_stats(user_id)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "username": user_data['username'],
        "title": user_data['active_title'],
        "coins": user_data['coins'],
        "achievements": user_data['achievements'],
        "xp": user_data['xp'],
        "level": user_data['level'],
        "progress": user_data['xp'] % 100,
        "plans": plans,
        "chart_labels": chart_labels,
        "chart_data": chart_data,
        "shop_items": SHOP_ITEMS # Передаем товары в шаблон
    })

# --- API ENDPOINTS ---

@app.get("/api/leaderboard")
async def api_leaderboard():
    leaders = await get_leaderboard(limit=10)
    return {"leaders": leaders}

@app.post("/api/complete/{task_id}")
async def api_complete(task_id: int, user_id: int):
    await complete_plan_db(task_id)
    is_levelup, new_coins = await add_rewards(user_id, 50, 10)
    return {"status": "success", "reward": "+50 XP, +10 Coins", "levelup": is_levelup, "new_coins": new_coins}

@app.post("/api/buy/{item_slug}")
async def api_buy(item_slug: str, user_id: int):
    # Ищем товар
    item = next((i for i in SHOP_ITEMS if i["slug"] == item_slug), None)
    if not item: return {"status": "error", "message": "Товар не найден"}
    
    result = await buy_item(user_id, item_slug, item["name"], item["price"])
    return {"status": "info", "message": result}

@app.post("/api/tasks/create")
async def api_create_task(req: CreateTaskRequest):
    # 1. Генерируем AI план
    plan_text = await ai_service.get_plan(req.user_id, req.text)
    # 2. Сохраняем
    full_text = f"[Web] {req.text}"
    task_id = await save_plan(req.user_id, full_text, plan_text)
    
    return {
        "status": "success",
        "task": {
            "id": task_id,
            "text": full_text,
            "created_at": "Только что"
        }
    }