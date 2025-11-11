from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import models


def list_events(
    db: Session,
    *,
    source: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[models.Event]:
    q = db.query(models.Event)
    if source:
        q = q.filter(models.Event.source == source)
    if level:
        q = q.filter(models.Event.level == level)
    return q.order_by(models.Event.created_at.desc()).offset(offset).limit(limit).all()

