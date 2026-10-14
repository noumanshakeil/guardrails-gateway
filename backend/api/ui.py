from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db import get_db
from backend.services import guardrails as svc

router = APIRouter()
templates = Jinja2Templates(directory="backend/templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Guardrails Gateway", "rules": await svc.list_rules(db), "audits": await svc.list_audits(db, limit=20), "result": None, "prompt": ""})

@router.post("/ui/check", response_class=HTMLResponse)
async def ui_check(request: Request, text: str = Form(...), db: AsyncSession = Depends(get_db)):
    result = await svc.check_text(db, text)
    return templates.TemplateResponse("index.html", {"request": request, "title": "Guardrails Gateway", "rules": await svc.list_rules(db), "audits": await svc.list_audits(db, limit=20), "result": result, "prompt": text})

@router.post("/ui/rules")
async def ui_rule(name: str = Form(...), kind: str = Form("regex"), pattern: str = Form(""), action: str = Form("block"), db: AsyncSession = Depends(get_db)):
    await svc.create_rule(db, name, kind, pattern, action)
    return RedirectResponse("/", status_code=303)
