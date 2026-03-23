# app/routers/tags.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import TagRead
from app import crud

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get("/", response_model=list[TagRead])
def list_tags(db: Session = Depends(get_db)):
    return crud.get_tags(db)