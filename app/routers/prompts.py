# app/routers/prompts.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import get_settings
from app.schemas import (
    PromptCreate, PromptRead, PromptUpdate,
    PaginatedPrompts, PromptRender, PromptRenderedResponse,
    PromptFork, VoteCreate, VoteRead,
)
from app import crud

settings = get_settings()
router = APIRouter(prefix="/prompts", tags=["Prompts"])


@router.post("/", response_model=PromptRead, status_code=status.HTTP_201_CREATED)
def create_prompt(data: PromptCreate, db: Session = Depends(get_db)):
    return crud.create_prompt(db, data)


@router.get("/", response_model=PaginatedPrompts)
def list_prompts(
    search: str | None = Query(None),
    category: str | None = Query(None),
    tag: str | None = Query(None, description="Filter by tag name"),
    model_hint: str | None = Query(None),
    use_case: str | None = Query(None),
    feed: str = Query("new", enum=["new", "hot", "top", "rising", "most_used", "most_forked"]),
    page: int = Query(1, ge=1),
    size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
):
    return crud.list_prompts(
        db, page=page, size=size,
        search=search, category=category, tag=tag,
        model_hint=model_hint, use_case=use_case, feed=feed,
    )


@router.get("/{prompt_id}", response_model=PromptRead)
def get_prompt(prompt_id: str, db: Session = Depends(get_db)):
    prompt = crud.view_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(404, "Prompt not found")
    return prompt


@router.patch("/{prompt_id}", response_model=PromptRead)
def update_prompt(prompt_id: str, data: PromptUpdate, db: Session = Depends(get_db)):
    prompt = crud.update_prompt(db, prompt_id, data)
    if not prompt:
        raise HTTPException(404, "Prompt not found")
    return prompt


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt(prompt_id: str, db: Session = Depends(get_db)):
    if not crud.delete_prompt(db, prompt_id):
        raise HTTPException(404, "Prompt not found")


@router.post("/{prompt_id}/render", response_model=PromptRenderedResponse)
def render_prompt(prompt_id: str, body: PromptRender, db: Session = Depends(get_db)):
    rendered = crud.render_prompt(db, prompt_id, body.values)
    if rendered is None:
        raise HTTPException(404, "Prompt not found")
    return PromptRenderedResponse(prompt_id=prompt_id, rendered=rendered)


@router.post("/{prompt_id}/vote", response_model=VoteRead)
def vote_prompt(prompt_id: str, body: VoteCreate, request: Request, db: Session = Depends(get_db)):
    voter_ip = request.client.host if request.client else "unknown"
    result = crud.vote_prompt(db, prompt_id, voter_ip, body.value)
    if not result:
        raise HTTPException(404, "Prompt not found")
    return result


@router.post("/{prompt_id}/fork", response_model=PromptRead, status_code=status.HTTP_201_CREATED)
def fork_prompt(prompt_id: str, body: PromptFork, db: Session = Depends(get_db)):
    forked = crud.fork_prompt(db, prompt_id, body)
    if not forked:
        raise HTTPException(404, "Prompt not found")
    return forked


@router.post("/{prompt_id}/copy", response_model=PromptRead)
def copy_prompt(prompt_id: str, db: Session = Depends(get_db)):
    prompt = crud.copy_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(404, "Prompt not found")
    return prompt