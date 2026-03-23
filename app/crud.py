# app/crud.py
import json, math, re
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app import models, schemas


# ───────────── helpers ──────────────
def _extract_variables(template: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"\{\{(\w+)\}\}", template)))


def _calc_hot_score(upvotes: int, downvotes: int, created_at: datetime) -> float:
    """Reddit-style hot ranking: score decays over time."""
    score = upvotes - downvotes
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age_hours = max((now - created_at).total_seconds() / 3600, 0.1)
    # Boost = score / (age in hours ^ 1.5)
    # Newer high-score items rank higher
    gravity = 1.5
    hot = score / pow(age_hours, gravity)
    return round(hot, 6)


def _get_or_create_tags(db: Session, tag_names: list[str]) -> list[models.Tag]:
    tags = []
    for name in tag_names:
        name = name.strip().lower()
        if not name:
            continue
        tag = db.query(models.Tag).filter(func.lower(models.Tag.name) == name).first()
        if not tag:
            tag = models.Tag(name=name)
            db.add(tag)
            db.commit()
            db.refresh(tag)
        tags.append(tag)
    return tags


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
    return db.query(models.Category).filter(func.lower(models.Category.name) == name.lower()).first()

def delete_category(db: Session, category_id: str) -> bool:
    cat = get_category(db, category_id)
    if not cat:
        return False
    db.delete(cat)
    db.commit()
    return True


# ───────────── TAG ───────────────────
def get_tags(db: Session) -> list[models.Tag]:
    return db.query(models.Tag).order_by(models.Tag.name).all()


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
        variables=json.dumps(variables),
    )

    # Add prompt to session FIRST
    db.add(prompt)
    db.flush()

    if data.category_ids:
        cats = db.query(models.Category).filter(models.Category.id.in_(data.category_ids)).all()
        prompt.categories = cats

    if data.tags:
        tags = []
        for name in data.tags:
            name = name.strip().lower()
            if not name:
                continue
            tag = db.query(models.Tag).filter(func.lower(models.Tag.name) == name).first()
            if not tag:
                tag = models.Tag(name=name)
                db.add(tag)
                db.flush()
            tags.append(tag)
        prompt.tags = tags

    db.commit()
    db.refresh(prompt)
    return prompt

def get_prompt(db: Session, prompt_id: str) -> models.Prompt | None:
    return db.query(models.Prompt).filter(models.Prompt.id == prompt_id).first()


def view_prompt(db: Session, prompt_id: str) -> models.Prompt | None:
    """Get prompt and increment view count."""
    prompt = get_prompt(db, prompt_id)
    if prompt:
        prompt.view_count = (prompt.view_count or 0) + 1
        db.commit()
        db.refresh(prompt)
    return prompt


def list_prompts(
    db: Session,
    *,
    page: int = 1,
    size: int = 20,
    search: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    model_hint: str | None = None,
    use_case: str | None = None,
    feed: str = "new",   # new | hot | top | rising | most_used
) -> dict:
    q = db.query(models.Prompt)

    # ── filters ──
    if search:
        pattern = f"%{search}%"
        q = q.filter(or_(
            models.Prompt.title.ilike(pattern),
            models.Prompt.description.ilike(pattern),
            models.Prompt.template.ilike(pattern),
        ))
    if category:
        q = q.filter(models.Prompt.categories.any(models.Category.id == category))
    if tag:
        q = q.filter(models.Prompt.tags.any(func.lower(models.Tag.name) == tag.lower()))
    if model_hint:
        q = q.filter(func.lower(models.Prompt.model_hint) == model_hint.lower())
    if use_case:
        q = q.filter(func.lower(models.Prompt.use_case) == use_case.lower())

    # ── feed algorithm ──
    if feed == "hot":
        q = q.order_by(models.Prompt.hot_score.desc())
    elif feed == "top":
        q = q.order_by(models.Prompt.score.desc())
    elif feed == "rising":
        # Rising = high recent votes + newer
        q = q.order_by(models.Prompt.upvotes.desc(), models.Prompt.created_at.desc())
    elif feed == "most_used":
        q = q.order_by(models.Prompt.usage_count.desc())
    elif feed == "most_forked":
        q = q.order_by(models.Prompt.fork_count.desc())
    else:  # "new"
        q = q.order_by(models.Prompt.created_at.desc())

    total = q.count()
    pages = math.ceil(total / size) if total else 1
    items = q.offset((page - 1) * size).limit(size).all()

    return {"items": items, "total": total, "page": page, "size": size, "pages": pages, "feed": feed}


def update_prompt(db: Session, prompt_id: str, data: schemas.PromptUpdate) -> models.Prompt | None:
    prompt = db.query(models.Prompt).filter(models.Prompt.id == prompt_id).first()
    if not prompt:
        return None

    update_data = data.model_dump(exclude_unset=True)
    category_ids = update_data.pop("category_ids", None)
    tag_names = update_data.pop("tags", None)

    if "template" in update_data and "variables" not in update_data:
        update_data["variables"] = json.dumps(_extract_variables(update_data["template"]))
    elif "variables" in update_data:
        update_data["variables"] = json.dumps(update_data["variables"])

    for key, value in update_data.items():
        setattr(prompt, key, value)

    if category_ids is not None:
        cats = db.query(models.Category).filter(models.Category.id.in_(category_ids)).all()
        prompt.categories = cats

    if tag_names is not None:
        prompt.tags = _get_or_create_tags(db, tag_names)

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
    prompt.usage_count = (prompt.usage_count or 0) + 1
    db.commit()
    rendered = prompt.template
    for key, val in values.items():
        rendered = rendered.replace("{{" + key + "}}", val)
    return rendered


def copy_prompt(db: Session, prompt_id: str) -> models.Prompt | None:
    """Track when someone copies a prompt."""
    prompt = get_prompt(db, prompt_id)
    if not prompt:
        return None
    prompt.copy_count = (prompt.copy_count or 0) + 1
    db.commit()
    db.refresh(prompt)
    return prompt


# ───────────── VOTE ──────────────────
def vote_prompt(db: Session, prompt_id: str, voter_ip: str, value: int) -> dict | None:
    prompt = get_prompt(db, prompt_id)
    if not prompt:
        return None

    # Check existing vote from this IP
    existing = db.query(models.Vote).filter(
        models.Vote.prompt_id == prompt_id,
        models.Vote.voter_ip == voter_ip,
    ).first()

    if existing:
        if existing.value == value:
            # Same vote again = undo
            db.delete(existing)
        else:
            existing.value = value
    else:
        if value != 0:
            vote = models.Vote(prompt_id=prompt_id, voter_ip=voter_ip, value=value)
            db.add(vote)

    # Flush so the new/updated/deleted vote is visible to count queries
    db.flush()

    # Recalculate counts
    prompt.upvotes = db.query(func.count(models.Vote.id)).filter(
        models.Vote.prompt_id == prompt_id, models.Vote.value == 1
    ).scalar() or 0

    prompt.downvotes = db.query(func.count(models.Vote.id)).filter(
        models.Vote.prompt_id == prompt_id, models.Vote.value == -1
    ).scalar() or 0

    prompt.score = prompt.upvotes - prompt.downvotes
    prompt.hot_score = _calc_hot_score(prompt.upvotes, prompt.downvotes, prompt.created_at)

    db.commit()
    db.refresh(prompt)

    # What did this user end up voting?
    final_vote = db.query(models.Vote).filter(
        models.Vote.prompt_id == prompt_id,
        models.Vote.voter_ip == voter_ip,
    ).first()

    return {
        "prompt_id": prompt_id,
        "upvotes": prompt.upvotes,
        "downvotes": prompt.downvotes,
        "score": prompt.score,
        "user_vote": final_vote.value if final_vote else 0,
    }

# ───────────── FORK ──────────────────
def fork_prompt(db: Session, prompt_id: str, data: schemas.PromptFork) -> models.Prompt | None:
    original = get_prompt(db, prompt_id)
    if not original:
        return None

    forked = models.Prompt(
        title=data.title or f"{original.title} (fork)",
        template=original.template,
        description=f"Forked from: {original.title}\n\n{original.description}",
        author=data.author,
        model_hint=original.model_hint,
        use_case=original.use_case,
        variables=original.variables,
        forked_from=original.id,
    )
    forked.categories = list(original.categories)
    forked.tags = list(original.tags)

    original.fork_count = (original.fork_count or 0) + 1

    db.add(forked)
    db.commit()
    db.refresh(forked)
    return forked