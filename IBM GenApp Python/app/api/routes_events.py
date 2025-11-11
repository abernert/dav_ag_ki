from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.services import events as svc


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/events")
def ui_list_events(
    request: Request,
    source: Optional[str] = None,
    level: Optional[str] = None,
    page: int = 1,
    size: int = 50,
    db: Session = Depends(get_db),
):
    page = max(page, 1)
    offset = (page - 1) * size
    items = svc.list_events(db, source=source, level=level, limit=size, offset=offset)
    return templates.TemplateResponse(
        "events.html",
        {
            "request": request,
            "events": items,
            "source": source or "",
            "level": level or "",
            "page": page,
            "size": size,
        },
    )


@router.get("/api/events")
def api_list_events(
    source: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    return svc.list_events(db, source=source, level=level, limit=limit, offset=offset)

