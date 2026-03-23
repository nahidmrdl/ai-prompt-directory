# app/crud.py
import json, math, re
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app import models, schemas


# ───────────── helpers ──────────────
def _extract_variables(template: str) -> list[str]:
    """Pull out {{var}} placeholders from a template string."""
    return list(dict.fromkeys(re.findall(r"\{\{(\w+)\}\}", template)))


# ───────────── CATEGORY ─────────────
def create_category(db: Session, data: schemas.CategoryCreate) -> models.Category:
    cat = models.Category(name=data.name, description=data.description)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def get_categories(db: Session) -> list[models.Category]:
    return db.query(models.Category).order_by(models.Category.name).all()


def get_category(db: Session, category_id: str) -> models.Category | None:
    return db.query(models.Category).filter(models.Category.id == category_id).first()


def get_category_by_name(db: Session, name: str) -> models.Category | None:
    return db.query(models.Category).filter(
        func.lower(models.Category.name) == name.lower()
    ).first()


def delete_category(db: Session, category_id: str) -> bool:
    cat = get_category(db, category_id)
    if not cat:
        return False
    db.delete(cat)
    db.commit()
    return True


# ───────────── PROMPT ────────────────
def create_prompt(db: Session, data: schemas.PromptCreate) -> models.Prompt:
    variables = data.variables or _extract_variables(data.template)
    prompt = models.Prompt(
        title=data.title,
        template=data.template,
        description=data.description,
        author=data.author,
        model_hint=data.model_hint,
        use_case=data.use_case,
        variables=json.dumps(variables),          # always store as JSON string
    )
    if data.category_ids:
        cats = (
            db.query(models.Category)
            .filter(models.Category.id.in_(data.category_ids))
            .all()
        )
        prompt.categories = cats

    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt                                  # return ORM object as-is


def get_prompt(db: Session, prompt_id: str) -> models.Prompt | None:
    return db.query(models.Prompt).filter(models.Prompt.id == prompt_id).first()


def list_prompts(
    db: Session,
    *,
    page: int = 1,
    size: int = 20,
    search: str | None = None,
    category: str | None = None,
    model_hint: str | None = None,
    use_case: str | None = None,
    sort_by: str = "created_at",
    order: str = "desc",
) -> dict:
    q = db.query(models.Prompt)

    if search:
        pattern = f"%{search}%"
        q = q.filter(
            or_(
                models.Prompt.title.ilike(pattern),
                models.Prompt.description.ilike(pattern),
                models.Prompt.template.ilike(pattern),
            )
        )
    if category:
        q = q.filter(models.Prompt.categories.any(models.Category.id == category))
    if model_hint:
        q = q.filter(func.lower(models.Prompt.model_hint) == model_hint.lower())
    if use_case:
        q = q.filter(func.lower(models.Prompt.use_case) == use_case.lower())

    sort_col = getattr(models.Prompt, sort_by, models.Prompt.created_at)
    q = q.order_by(sort_col.desc() if order == "desc" else sort_col.asc())

    total = q.count()
    pages = math.ceil(total / size) if total else 1
    items = q.offset((page - 1) * size).limit(size).all()

    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}


def update_prompt(db: Session, prompt_id: str, data: schemas.PromptUpdate) -> models.Prompt | None:
    prompt = db.query(models.Prompt).filter(models.Prompt.id == prompt_id).first()
    if not prompt:
        return None

    update_data = data.model_dump(exclude_unset=True)
    category_ids = update_data.pop("category_ids", None)

    if "template" in update_data and "variables" not in update_data:
        update_data["variables"] = json.dumps(_extract_variables(update_data["template"]))
    elif "variables" in update_data:
        update_data["variables"] = json.dumps(update_data["variables"])

    for key, value in update_data.items():
        setattr(prompt, key, value)

    if category_ids is not None:
        cats = db.query(models.Category).filter(models.Category.id.in_(category_ids)).all()
        prompt.categories = cats

    db.commit()
    db.refresh(prompt)
    return prompt


def delete_prompt(db: Session, prompt_id: str) -> bool:
    prompt = get_prompt(db, prompt_id)
    if not prompt:
        return False
    db.delete(prompt)
    db.commit()
    return True


def render_prompt(db: Session, prompt_id: str, values: dict[str, str]) -> str | None:
    prompt = get_prompt(db, prompt_id)
    if not prompt:
        return None

    # bump usage counter WITHOUT touching variables
    prompt.usage_count = (prompt.usage_count or 0) + 1
    db.commit()

    rendered = prompt.template
    for key, val in values.items():
        rendered = rendered.replace("{{" + key + "}}", val)
    return rendered


def rate_prompt(db: Session, prompt_id: str, score: float) -> models.Prompt | None:
    prompt = get_prompt(db, prompt_id)
    if not prompt:
        return None
    count = prompt.usage_count or 1
    prompt.rating = round(((prompt.rating * (count - 1)) + score) / count, 2)
    db.commit()
    db.refresh(prompt)
    return prompt