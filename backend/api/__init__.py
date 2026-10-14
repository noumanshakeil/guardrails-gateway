from fastapi import APIRouter
from backend.api import health, guardrails, ui
api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(guardrails.router, prefix="/api", tags=["guardrails"])
api_router.include_router(ui.router, tags=["ui"])
