from __future__ import annotations
import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import DecisionAudit, PolicyRule
from backend.utils.ids import short_id

_PII = re.compile(r"(\b[\w.+-]+@[\w-]+\.[\w.-]+\b|\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b)", re.I)
_TOXIC = re.compile(r"\b(idiot|stupid|kill yourself|hate you|moron)\b", re.I)

async def seed_defaults(session: AsyncSession) -> None:
    if (await session.execute(select(PolicyRule).limit(1))).scalar_one_or_none():
        return
    for name, kind, pattern, action in [
        ("Block emails", "pii", "", "block"),
        ("Block slurs", "toxicity", "", "block"),
        ("Allow internal tag", "regex", r"\[internal\]", "allow"),
    ]:
        session.add(PolicyRule(id=short_id(), name=name, kind=kind, pattern=pattern, action=action, enabled=True))
    await session.commit()

async def list_rules(session: AsyncSession) -> list[PolicyRule]:
    await seed_defaults(session)
    return list((await session.execute(select(PolicyRule).order_by(PolicyRule.created_at.desc()))).scalars())

async def create_rule(session: AsyncSession, name: str, kind: str, pattern: str = "", action: str = "block", enabled: bool = True) -> PolicyRule:
    row = PolicyRule(id=short_id(), name=name.strip()[:120], kind=kind.lower()[:32], pattern=pattern.strip()[:400], action=action.lower()[:16], enabled=enabled)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row

async def update_rule(session: AsyncSession, rule_id: str, **fields) -> PolicyRule:
    row = await session.get(PolicyRule, rule_id)
    if not row:
        raise ValueError("rule not found")
    for key, val in fields.items():
        if val is not None and hasattr(row, key):
            setattr(row, key, val)
    await session.commit()
    await session.refresh(row)
    return row

async def delete_rule(session: AsyncSession, rule_id: str) -> None:
    row = await session.get(PolicyRule, rule_id)
    if not row:
        raise ValueError("rule not found")
    await session.delete(row)
    await session.commit()

def _match_rule(rule: PolicyRule, text: str) -> bool:
    if rule.kind == "pii":
        return bool(_PII.search(text))
    if rule.kind == "toxicity":
        return bool(_TOXIC.search(text))
    if rule.kind == "regex" and rule.pattern:
        try:
            return bool(re.search(rule.pattern, text, re.I))
        except re.error:
            return False
    return False

async def _audit(session: AsyncSession, *, allowed: bool, snippet: str, reason: str, rule: PolicyRule | None) -> None:
    session.add(DecisionAudit(id=short_id(), allowed=allowed, rule_id=rule.id if rule else None, rule_name=rule.name if rule else "", reason=reason, snippet=snippet[:500]))
    await session.commit()

async def check_text(session: AsyncSession, text: str) -> dict:
    await seed_defaults(session)
    clean = (text or "").strip()
    rules = [r for r in await list_rules(session) if r.enabled]
    for rule in [r for r in rules if r.action == "allow"]:
        if _match_rule(rule, clean):
            await _audit(session, allowed=True, snippet=clean, reason="allow_rule", rule=rule)
            return {"allowed": True, "reason": "allow_rule", "rule_id": rule.id, "rule_name": rule.name}
    for rule in [r for r in rules if r.action == "block"]:
        if _match_rule(rule, clean):
            await _audit(session, allowed=False, snippet=clean, reason=rule.kind, rule=rule)
            return {"allowed": False, "reason": rule.kind, "rule_id": rule.id, "rule_name": rule.name}
    await _audit(session, allowed=True, snippet=clean, reason="pass", rule=None)
    return {"allowed": True, "reason": "pass", "rule_id": None, "rule_name": ""}

async def list_audits(session: AsyncSession, limit: int = 50) -> list[DecisionAudit]:
    stmt = select(DecisionAudit).order_by(DecisionAudit.created_at.desc()).limit(limit)
    return list((await session.execute(stmt)).scalars())
