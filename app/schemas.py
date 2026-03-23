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


# ===================== PROMPT =======================
class PromptBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, examples=["Python Docstring Generator"])
    template: str = Field(
        ...,
        min_length=1,
        examples=[
            "Write a Google-style docstring for the following Python function:\n\n```python\n{{code}}\n```"
        ],
    )
    description: str = Field("", max_length=1000)
    author: str = Field("anonymous", max_length=100)
    model_hint: str = Field("any", max_length=50)
    use_case: str = Field("general", max_length=100)
    variables: list[str] = Field(default_factory=list, examples=[["code"]])


class PromptCreate(PromptBase):
    category_ids: list[str] = Field(default_factory=list)


class PromptUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    template: str | None = Field(None, min_length=1)
    description: str | None = None
    author: str | None = None
    model_hint: str | None = None
    use_case: str | None = None
    variables: list[str] | None = None
    category_ids: list[str] | None = None


class PromptRead(PromptBase):
    id: str
    rating: float
    usage_count: int
    created_at: datetime
    updated_at: datetime
    categories: list[CategoryRead] = []
    model_config = ConfigDict(from_attributes=True)

    @field_validator("variables", mode="before")
    @classmethod
    def parse_variables(cls, v):
        """DB stores variables as JSON string — convert to list for response."""
        if isinstance(v, str):
            return json.loads(v)
        return v


class PromptRender(BaseModel):
    """Send variable values, get back the filled template."""
    values: dict[str, str] = Field(
        ..., examples=[{"code": "def add(a, b): return a + b"}]
    )


class PromptRenderedResponse(BaseModel):
    prompt_id: str
    rendered: str


# ===================== PAGINATION ===================
class PaginatedPrompts(BaseModel):
    items: list[PromptRead]
    total: int
    page: int
    size: int
    pages: int