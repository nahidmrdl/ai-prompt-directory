# app/routers/prompts.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import get_settings
from app.schemas import (
    PromptCreate, PromptRead, PromptUpdate,
    PaginatedPrompts, PromptRender, PromptRenderedResponse,
)
from app import crud

settings = get_settings()
router = APIRouter(prefix="/prompts", tags=["Prompts"])


# ────── CREATE ──────
@router.post("/", response_model=PromptRead, status_code=status.HTTP_201_CREATED)
def create_prompt(data: PromptCreate, db: Session = Depends(get_db)):
    return crud.create_prompt(db, data)


# ────── LIST with search / filter / sort / paginate ──────
@router.get("/", response_model=PaginatedPrompts)
def list_prompts(
    search: str | None = Query(None, description="Full-text search in title, description, template"),
    category: str | None = Query(None, description="Filter by category ID"),
    model_hint: str | None = Query(None, description="Filter by target model (gpt-4, claude, etc.)"),
    use_case: str | None = Query(None, description="Filter by use-case (coding, writing, etc.)"),
    sort_by: str = Query("created_at", enum=["created_at", "rating", "usage_count"]),
    order: str = Query("desc", enum=["asc", "desc"]),
    page: int = Query(1, ge=1),
    size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
):
    return crud.list_prompts(
        db,
        page=page, size=size,
        search=search, category=category,
        model_hint=model_hint, use_case=use_case,
        sort_by=sort_by, order=order,
    )


# ────── GET ONE ──────
@router.get("/{prompt_id}", response_model=PromptRead)
def get_prompt(prompt_id: str, db: Session = Depends(get_db)):
    prompt = crud.get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(404, "Prompt not found")
    return prompt


# ────── UPDATE ──────
@router.patch("/{prompt_id}", response_model=PromptRead)
def update_prompt(prompt_id: str, data: PromptUpdate, db: Session = Depends(get_db)):
    prompt = crud.update_prompt(db, prompt_id, data)
    if not prompt:
        raise HTTPException(404, "Prompt not found")
    return prompt


# ────── DELETE ──────
@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt(prompt_id: str, db: Session = Depends(get_db)):
    if not crud.delete_prompt(db, prompt_id):
        raise HTTPException(404, "Prompt not found")


# ────── RENDER (fill in variables) ──────
@router.post("/{prompt_id}/render", response_model=PromptRenderedResponse)
def render_prompt(prompt_id: str, body: PromptRender, db: Session = Depends(get_db)):
    rendered = crud.render_prompt(db, prompt_id, body.values)
    if rendered is None:
        raise HTTPException(404, "Prompt not found")
    return PromptRenderedResponse(prompt_id=prompt_id, rendered=rendered)


# ────── RATE ──────
@router.post("/{prompt_id}/rate", response_model=PromptRead)
def rate_prompt(
    prompt_id: str,
    score: float = Query(..., ge=0, le=5, description="Rating 0-5"),
    db: Session = Depends(get_db),
):
    prompt = crud.rate_prompt(db, prompt_id, score)
    if not prompt:
        raise HTTPException(404, "Prompt not found")
    return prompt