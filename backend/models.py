from __future__ import annotations
from datetime import datetime
from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.db import Base

def utcnow(): return datetime.utcnow()

class PolicyRule(Base):
    __tablename__ = "policy_rules"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    kind: Mapped[str] = mapped_column(String(32), index=True)
    pattern: Mapped[str] = mapped_column(String(400), default="")
    action: Mapped[str] = mapped_column(String(16), default="block")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

class DecisionAudit(Base):
    __tablename__ = "decision_audits"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    rule_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    rule_name: Mapped[str] = mapped_column(String(120), default="")
    reason: Mapped[str] = mapped_column(String(64), default="")
    snippet: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
