from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.database import get_user_profile, get_last_plans

app = FastAPI()
templates = Jinja2Templates(directory="src/templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, user_id: int):
    # Берем полный профиль с ачивками
    user_data = await get_user_profile(user_id)
    plans = await get_last_plans(user_id, limit=10)
    
    # Передаем в шаблон
    return templates.TemplateResponse("index.html", {
        "request": request,
        "username": user_data['username'],
        "title": user_data['active_title'],
        "coins": user_data['coins'],
        "achievements": user_data['achievements'],
        "xp": user_data['xp'],
        "level": user_data['level'],
        "progress": user_data['xp'] % 100,
        "plans": plans
    })