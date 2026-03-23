# app/schemas.py
from __future__ import annotations
import json
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ===================== CATEGORY =====================
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["Coding"])
    description: str = Field("", max_length=500)

class CategoryCreate(CategoryBase):
    pass

class CategoryRead(CategoryBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ===================== TAG ==========================
class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, examples=["python"])

class TagCreate(TagBase):
    pass

class TagRead(TagBase):
    id: str
    model_config = ConfigDict(from_attributes=True)


# ===================== PROMPT =======================
class PromptBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    template: str = Field(..., min_length=1)
    description: str = Field("", max_length=1000)
    author: str = Field("anonymous", max_length=100)
    model_hint: str = Field("any", max_length=50)
    use_case: str = Field("general", max_length=100)
    variables: list[str] = Field(default_factory=list)

class PromptCreate(PromptBase):
    category_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list, description="Tag names — created if they don't exist")

class PromptUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    template: str | None = Field(None, min_length=1)
    description: str | None = None
    author: str | None = None
    model_hint: str | None = None
    use_case: str | None = None
    variables: list[str] | None = None
    category_ids: list[str] | None = None
    tags: list[str] | None = None

class PromptRead(PromptBase):
    id: str
    upvotes: int
    downvotes: int
    score: float
    hot_score: float
    usage_count: int
    copy_count: int
    view_count: int
    fork_count: int
    forked_from: str | None
    created_at: datetime
    updated_at: datetime
    categories: list[CategoryRead] = []
    tags: list[TagRead] = []
    model_config = ConfigDict(from_attributes=True)

    @field_validator("variables", mode="before")
    @classmethod
    def parse_variables(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

class PromptRender(BaseModel):
    values: dict[str, str] = Field(..., examples=[{"code": "def add(a, b): return a + b"}])

class PromptRenderedResponse(BaseModel):
    prompt_id: str
    rendered: str

class PromptFork(BaseModel):
    title: str | None = None
    author: str = "anonymous"

# ===================== VOTE =========================
class VoteCreate(BaseModel):
    value: int = Field(..., ge=-1, le=1, description="-1 for downvote, +1 for upvote")

class VoteRead(BaseModel):
    prompt_id: str
    upvotes: int
    downvotes: int
    score: float
    user_vote: int = 0  # what this user voted

# ===================== PAGINATION ===================
class PaginatedPrompts(BaseModel):
    items: list[PromptRead]
    total: int
    page: int
    size: int
    pages: int
    feed: str = "new"