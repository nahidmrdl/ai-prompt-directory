# app/models.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, DateTime, Float,
    ForeignKey, Table, Integer, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def new_id():
    return str(uuid.uuid4())


# ---------- many-to-many: prompts <-> categories ----------
prompt_category = Table(
    "prompt_category",
    Base.metadata,
    Column("prompt_id", String, ForeignKey("prompts.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", String, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)


class Category(Base):
    __tablename__ = "categories"

    id          = Column(String, primary_key=True, default=new_id)
    name        = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, default="")
    created_at  = Column(DateTime(timezone=True), default=utcnow)

    prompts = relationship(
        "Prompt", secondary=prompt_category, back_populates="categories"
    )


class Prompt(Base):
    __tablename__ = "prompts"

    id          = Column(String, primary_key=True, default=new_id)
    title       = Column(String(200), nullable=False, index=True)
    template    = Column(Text, nullable=False)
    description = Column(Text, default="")
    author      = Column(String(100), default="anonymous")
    model_hint  = Column(String(50), default="any")     # gpt-4, claude, etc.
    use_case    = Column(String(100), default="general") # coding, writing, etc.
    rating      = Column(Float, default=0.0)
    usage_count = Column(Integer, default=0)
    variables   = Column(Text, default="[]")             # JSON list of {{var}} names
    created_at  = Column(DateTime(timezone=True), default=utcnow)
    updated_at  = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    categories = relationship(
        "Category", secondary=prompt_category, back_populates="prompts"
    )