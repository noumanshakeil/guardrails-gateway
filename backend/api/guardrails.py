from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db import get_db
from backend.services import guardrails as svc

class RuleIn(BaseModel):
    name: str = Field(min_length=2)
    kind: str = Field(pattern="^(pii|toxicity|regex)$")
    pattern: str = ""
    action: str = Field(default="block", pattern="^(block|allow)$")
    enabled: bool = True

class CheckIn(BaseModel):
    text: str = Field(min_length=1)

router = APIRouter()

@router.get("/rules")
async def rules(db: AsyncSession = Depends(get_db)):
    rows = await svc.list_rules(db)
    return {"rules": [{"id": r.id, "name": r.name, "kind": r.kind, "pattern": r.pattern, "action": r.action, "enabled": r.enabled} for r in rows]}

@router.post("/rules")
async def create_rule(payload: RuleIn, db: AsyncSession = Depends(get_db)):
    row = await svc.create_rule(db, payload.name, payload.kind, payload.pattern, payload.action, payload.enabled)
    return {"id": row.id}

@router.patch("/rules/{rule_id}")
async def patch_rule(rule_id: str, payload: RuleIn, db: AsyncSession = Depends(get_db)):
    try:
        row = await svc.update_rule(db, rule_id, name=payload.name, kind=payload.kind, pattern=payload.pattern, action=payload.action, enabled=payload.enabled)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {"id": row.id}

@router.delete("/rules/{rule_id}")
async def remove_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    try:
        await svc.delete_rule(db, rule_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {"ok": True}

@router.post("/check")
async def check(payload: CheckIn, db: AsyncSession = Depends(get_db)):
    return await svc.check_text(db, payload.text)

@router.get("/audit")
async def audit(db: AsyncSession = Depends(get_db)):
    rows = await svc.list_audits(db)
    return {"decisions": [{"id": a.id, "allowed": a.allowed, "reason": a.reason, "rule_name": a.rule_name, "snippet": a.snippet[:120], "created_at": a.created_at.isoformat()} for a in rows]}
