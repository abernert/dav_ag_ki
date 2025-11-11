from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import models
from app.schemas.claims import ClaimCreate, ClaimUpdate
from app.utils.errors import CobolError


def list_claims(db: Session, policy_id: int | None = None, limit: int = 100, offset: int = 0) -> List[models.Claim]:
    q = db.query(models.Claim)
    if policy_id:
        q = q.filter(models.Claim.policy_id == policy_id)
    return q.order_by(models.Claim.id.asc()).offset(offset).limit(limit).all()


def create_claim(db: Session, data: ClaimCreate) -> models.Claim:
    # ensure policy exists
    if not db.get(models.Policy, data.policy_id):
        raise CobolError("70", "Policy not found")
    obj = models.Claim(
        policy_id=data.policy_id,
        number=data.number,
        date=data.date,
        paid=data.paid,
        value=data.value,
        cause=data.cause,
        observations=data.observations,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    _log_event(db, source="claims", message=f"create claim id={obj.id} policy_id={obj.policy_id}")
    return obj


def delete_claim(db: Session, claim_id: int) -> bool:
    obj = db.get(models.Claim, claim_id)
    if not obj:
        raise CobolError("01", "Claim not found")
    db.delete(obj)
    db.commit()
    _log_event(db, source="claims", message=f"delete claim id={claim_id}")
    return True


def get_claim(db: Session, claim_id: int) -> models.Claim:
    obj = db.get(models.Claim, claim_id)
    if not obj:
        raise CobolError("01", "Claim not found")
    return obj


def update_claim(
    db: Session,
    claim_id: int,
    data: ClaimUpdate,
    *,
    commit: bool = True,
) -> models.Claim:
    obj = db.get(models.Claim, claim_id)
    if not obj:
        raise CobolError("01", "Claim not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.add(obj)
    if commit:
        db.commit()
        db.refresh(obj)
        _log_event(db, source="claims", message=f"update claim id={obj.id}")
    else:
        db.flush()
    return obj


def _log_event(db: Session, *, source: str, message: str, level: str = "INFO") -> None:
    try:
        db.add(models.Event(source=source, level=level, message=message))
        db.commit()
    except Exception:
        db.rollback()
