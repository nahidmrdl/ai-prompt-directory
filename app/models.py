# app/models.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, DateTime, Float,
    ForeignKey, Table, Integer,
)
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def new_id():
    return str(uuid.uuid4())


# many-to-many: prompts <-> categories
prompt_category = Table(
    "prompt_category",
    Base.metadata,
    Column("prompt_id", String, ForeignKey("prompts.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", String, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)

# many-to-many: prompts <-> tags
prompt_tag = Table(
    "prompt_tag",
    Base.metadata,
    Column("prompt_id", String, ForeignKey("prompts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", String, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Category(Base):
    __tablename__ = "categories"
    id          = Column(String, primary_key=True, default=new_id)
    name        = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, default="")
    created_at  = Column(DateTime(timezone=True), default=utcnow)
    prompts     = relationship("Prompt", secondary=prompt_category, back_populates="categories")


class Tag(Base):
    __tablename__ = "tags"
    id         = Column(String, primary_key=True, default=new_id)
    name       = Column(String(50), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    prompts    = relationship("Prompt", secondary=prompt_tag, back_populates="tags")


class Prompt(Base):
    __tablename__ = "prompts"
    id          = Column(String, primary_key=True, default=new_id)
    title       = Column(String(200), nullable=False, index=True)
    template    = Column(Text, nullable=False)
    description = Column(Text, default="")
    author      = Column(String(100), default="anonymous")
    model_hint  = Column(String(50), default="any")
    use_case    = Column(String(100), default="general")
    variables   = Column(Text, default="[]")

    # Engagement metrics
    upvotes     = Column(Integer, default=0)
    downvotes   = Column(Integer, default=0)
    score       = Column(Float, default=0.0)        # upvotes - downvotes
    hot_score   = Column(Float, default=0.0)        # time-decayed popularity
    usage_count = Column(Integer, default=0)
    copy_count  = Column(Integer, default=0)
    view_count  = Column(Integer, default=0)

    # Fork tracking
    forked_from = Column(String, ForeignKey("prompts.id"), nullable=True)
    fork_count  = Column(Integer, default=0)

    created_at  = Column(DateTime(timezone=True), default=utcnow)
    updated_at  = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    categories  = relationship("Category", secondary=prompt_category, back_populates="prompts")
    tags        = relationship("Tag", secondary=prompt_tag, back_populates="prompts")
    votes       = relationship("Vote", back_populates="prompt", cascade="all, delete-orphan")
    parent      = relationship("Prompt", remote_side=[id], backref="forks_list")


class Vote(Base):
    __tablename__ = "votes"
    id         = Column(String, primary_key=True, default=new_id)
    prompt_id  = Column(String, ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False, index=True)
    voter_ip   = Column(String(45), nullable=False)   # IP-based until we add user accounts
    value      = Column(Integer, nullable=False)       # +1 or -1
    created_at = Column(DateTime(timezone=True), default=utcnow)

    prompt = relationship("Prompt", back_populates="votes")