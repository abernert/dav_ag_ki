from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from datetime import date
import json

from app.db import models
from app.utils.errors import CobolError
from app.schemas.policies import (
    PolicyCreate,
    PolicyUpdate,
    MotorPolicyCreate,
    HousePolicyCreate,
    EndowmentPolicyCreate,
    CommercialPolicyCreate,
)


def _next_counter(db: Session, name: str) -> int:
    ctr = db.get(models.Counter, name)
    if not ctr:
        ctr = models.Counter(name=name, value=0)
        db.add(ctr)
        db.flush()
    ctr.value += 1
    db.add(ctr)
    db.flush()
    return ctr.value


def create_policy(db: Session, data: PolicyCreate) -> models.Policy:
    # Ensure customer exists
    customer = db.get(models.Customer, data.customer_id)
    if not customer:
        raise CobolError("70", "Customer not found")

    # assign policy number if missing, ensure soft-unique
    policy_number = data.policy_number
    if policy_number is None:
        policy_number = _next_counter(db, "GENAPOLICYNUM")
        if db.query(models.Policy).filter(models.Policy.policy_number == policy_number).first():
            policy_number = _next_counter(db, "GENAPOLICYNUM")
    else:
        if policy_number <= 0:
            raise CobolError("98", "policy_number muss positiv sein")
        if db.query(models.Policy).filter(models.Policy.policy_number == policy_number).first():
            raise CobolError("90", "Policy number already in use")

    obj = models.Policy(
        policy_type=data.policy_type.upper(),
        policy_number=policy_number,
        customer_id=data.customer_id,
        issue_date=data.issue_date,
        expiry_date=data.expiry_date,
        last_changed=data.last_changed,
        broker_id=data.broker_id,
        brokers_ref=data.brokers_ref,
        payment=data.payment,
        commission=data.commission,
        details=json.dumps(data.details) if data.details else None,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    _log_event(db, source="policies", message=f"create policy id={obj.id} pnum={obj.policy_number} type={obj.policy_type}")
    return obj


def list_policies(
    db: Session,
    limit: int = 100,
    offset: int = 0,
    policy_type: str | None = None,
    customer_id: int | None = None,
    active_only: bool = False,
    postcode: str | None = None,
) -> List[models.Policy]:
    q = db.query(models.Policy)
    if postcode:
        like = f"%{postcode}%"
        q = q.join(models.Customer)
        q = q.outerjoin(models.CommercialPolicy, models.Policy.id == models.CommercialPolicy.policy_id)
        q = q.filter(
            or_(
                models.Customer.postcode.ilike(like),
                models.CommercialPolicy.postcode.ilike(like),
            )
        )
    if policy_type:
        q = q.filter(models.Policy.policy_type == policy_type.upper())
    if customer_id:
        q = q.filter(models.Policy.customer_id == customer_id)
    if active_only:
        today = date.today()
        q = q.filter((models.Policy.expiry_date == None) | (models.Policy.expiry_date >= today))
    return q.order_by(models.Policy.id.asc()).offset(offset).limit(limit).all()


def get_policy(db: Session, policy_id: int) -> Optional[models.Policy]:
    return db.get(models.Policy, policy_id)


def _model_to_dict(obj) -> dict | None:
    if obj is None:
        return None
    return {column.name: getattr(obj, column.name) for column in obj.__table__.columns}


def get_policy_detail(db: Session, policy_id: int) -> Optional[dict]:
    p = db.get(models.Policy, policy_id)
    if not p:
        return None
    detail = None
    if p.policy_type == "M":
        detail = db.query(models.MotorPolicy).filter_by(policy_id=p.id).first()
    elif p.policy_type == "H":
        detail = db.query(models.HousePolicy).filter_by(policy_id=p.id).first()
    elif p.policy_type == "E":
        detail = db.query(models.EndowmentPolicy).filter_by(policy_id=p.id).first()
    elif p.policy_type == "C":
        detail = db.query(models.CommercialPolicy).filter_by(policy_id=p.id).first()
    return {"policy": p, "detail": detail, "detail_dict": _model_to_dict(detail)}


def delete_policy(db: Session, policy_id: int) -> bool:
    obj = db.get(models.Policy, policy_id)
    if not obj:
        raise CobolError("01", "Policy not found")
    db.delete(obj)
    db.commit()
    _log_event(db, source="policies", message=f"delete policy id={policy_id}")
    return True


def update_policy(
    db: Session,
    policy_id: int,
    data: PolicyUpdate,
    *,
    commit: bool = True,
    log: bool = True,
) -> models.Policy:
    obj = db.get(models.Policy, policy_id)
    if not obj:
        raise CobolError("01", "Policy not found")
    payload = data.model_dump(exclude_unset=True)
    if "policy_number" in payload:
        new_number = payload["policy_number"]
        if new_number is None:
            raise CobolError("98", "policy_number darf nicht leer sein")
        if new_number <= 0:
            raise CobolError("98", "policy_number muss positiv sein")
        existing = (
            db.query(models.Policy)
            .filter(models.Policy.policy_number == new_number, models.Policy.id != obj.id)
            .first()
        )
        if existing:
            raise CobolError("90", "Policy number already in use")
    for field, value in payload.items():
        if field == "policy_number" and value is None:
            continue
        setattr(obj, field, value)
    db.add(obj)
    if commit:
        db.commit()
        db.refresh(obj)
        if log:
            _log_event(db, source="policies", message=f"update policy id={policy_id}")
    else:
        db.flush()
    return obj


def update_policy_motor(
    db: Session,
    policy_id: int,
    *,
    make: str | None = None,
    model: str | None = None,
    value: int | None = None,
    reg_number: str | None = None,
    colour: str | None = None,
    cc: int | None = None,
    manufactured: str | None = None,
    premium: int | None = None,
    accidents: int | None = None,
    commit: bool = True,
) -> bool:
    det = db.query(models.MotorPolicy).filter_by(policy_id=policy_id).first()
    if not det:
        raise CobolError("01", "Policy detail not found")
    for k, v in {
        "make": make,
        "model": model,
        "value": value,
        "reg_number": reg_number,
        "colour": colour,
        "cc": cc,
        "manufactured": manufactured,
        "premium": premium,
        "accidents": accidents,
    }.items():
        if v is not None:
            setattr(det, k, v)
    db.add(det)
    if commit:
        db.commit()
    else:
        db.flush()
    return True


def update_policy_house(
    db: Session,
    policy_id: int,
    *,
    property_type: str | None = None,
    bedrooms: int | None = None,
    value: int | None = None,
    house_name: str | None = None,
    house_number: str | None = None,
    postcode: str | None = None,
    commit: bool = True,
) -> bool:
    det = db.query(models.HousePolicy).filter_by(policy_id=policy_id).first()
    if not det:
        raise CobolError("01", "Policy detail not found")
    for k, v in {
        "property_type": property_type,
        "bedrooms": bedrooms,
        "value": value,
        "house_name": house_name,
        "house_number": house_number,
        "postcode": postcode,
    }.items():
        if v is not None:
            setattr(det, k, v)
    db.add(det)
    if commit:
        db.commit()
    else:
        db.flush()
    return True


def update_policy_endowment(
    db: Session,
    policy_id: int,
    *,
    with_profits: str | None = None,
    equities: str | None = None,
    managed_fund: str | None = None,
    fund_name: str | None = None,
    term: int | None = None,
    sum_assured: int | None = None,
    life_assured: str | None = None,
    commit: bool = True,
) -> bool:
    det = db.query(models.EndowmentPolicy).filter_by(policy_id=policy_id).first()
    if not det:
        raise CobolError("01", "Policy detail not found")
    for k, v in {
        "with_profits": with_profits,
        "equities": equities,
        "managed_fund": managed_fund,
        "fund_name": fund_name,
        "term": term,
        "sum_assured": sum_assured,
        "life_assured": life_assured,
    }.items():
        if v is not None:
            setattr(det, k, v)
    db.add(det)
    if commit:
        db.commit()
    else:
        db.flush()
    return True


def update_policy_commercial(
    db: Session,
    policy_id: int,
    *,
    address: str | None = None,
    postcode: str | None = None,
    latitude: str | None = None,
    longitude: str | None = None,
    customer: str | None = None,
    prop_type: str | None = None,
    fire_peril: int | None = None,
    fire_premium: int | None = None,
    crime_peril: int | None = None,
    crime_premium: int | None = None,
    flood_peril: int | None = None,
    flood_premium: int | None = None,
    weather_peril: int | None = None,
    weather_premium: int | None = None,
    status: int | None = None,
    reject_reason: str | None = None,
    commit: bool = True,
) -> bool:
    det = db.query(models.CommercialPolicy).filter_by(policy_id=policy_id).first()
    if not det:
        raise CobolError("01", "Policy detail not found")
    for k, v in {
        "address": address,
        "postcode": postcode,
        "latitude": latitude,
        "longitude": longitude,
        "customer": customer,
        "prop_type": prop_type,
        "fire_peril": fire_peril,
        "fire_premium": fire_premium,
        "crime_peril": crime_peril,
        "crime_premium": crime_premium,
        "flood_peril": flood_peril,
        "flood_premium": flood_premium,
        "weather_peril": weather_peril,
        "weather_premium": weather_premium,
        "status": status,
        "reject_reason": reject_reason,
    }.items():
        if v is not None:
            setattr(det, k, v)
    db.add(det)
    if commit:
        db.commit()
    else:
        db.flush()
    return True


def create_policy_motor(db: Session, data: MotorPolicyCreate) -> models.Policy:
    policy_number = data.policy_number
    if policy_number is None:
        policy_number = _next_counter(db, "GENAPOLICYNUM")
        if db.query(models.Policy).filter(models.Policy.policy_number == policy_number).first():
            policy_number = _next_counter(db, "GENAPOLICYNUM")
    base = models.Policy(
        policy_type="M",
        policy_number=policy_number,
        customer_id=data.customer_id,
        issue_date=data.issue_date,
        expiry_date=data.expiry_date,
        last_changed=data.last_changed,
        broker_id=data.broker_id,
        brokers_ref=data.brokers_ref,
        payment=data.payment,
        commission=None,
    )
    db.add(base)
    db.flush()

    detail = models.MotorPolicy(
        policy_id=base.id,
        make=data.make,
        model=data.model,
        value=data.value,
        reg_number=data.reg_number,
        colour=data.colour,
        cc=data.cc,
        manufactured=data.manufactured,
        premium=data.premium,
        accidents=data.accidents,
    )
    db.add(detail)
    db.commit()
    db.refresh(base)
    _log_event(db, source="policies", message=f"create motor policy id={base.id}")
    return base


def create_policy_house(db: Session, data: HousePolicyCreate) -> models.Policy:
    policy_number = data.policy_number
    if policy_number is None:
        policy_number = _next_counter(db, "GENAPOLICYNUM")
        if db.query(models.Policy).filter(models.Policy.policy_number == policy_number).first():
            policy_number = _next_counter(db, "GENAPOLICYNUM")
    base = models.Policy(
        policy_type="H",
        policy_number=policy_number,
        customer_id=data.customer_id,
        issue_date=data.issue_date,
        expiry_date=data.expiry_date,
        last_changed=data.last_changed,
        broker_id=data.broker_id,
        brokers_ref=data.brokers_ref,
        payment=data.payment,
        commission=None,
    )
    db.add(base)
    db.flush()

    detail = models.HousePolicy(
        policy_id=base.id,
        property_type=data.property_type,
        bedrooms=data.bedrooms,
        value=data.value,
        house_name=data.house_name,
        house_number=data.house_number,
        postcode=data.postcode,
    )
    db.add(detail)
    db.commit()
    db.refresh(base)
    _log_event(db, source="policies", message=f"create house policy id={base.id}")
    return base


def create_policy_endowment(db: Session, data: EndowmentPolicyCreate) -> models.Policy:
    policy_number = data.policy_number
    if policy_number is None:
        policy_number = _next_counter(db, "GENAPOLICYNUM")
        if db.query(models.Policy).filter(models.Policy.policy_number == policy_number).first():
            policy_number = _next_counter(db, "GENAPOLICYNUM")
    base = models.Policy(
        policy_type="E",
        policy_number=policy_number,
        customer_id=data.customer_id,
        issue_date=data.issue_date,
        expiry_date=data.expiry_date,
        last_changed=data.last_changed,
        broker_id=data.broker_id,
        brokers_ref=data.brokers_ref,
        payment=data.payment,
        commission=None,
    )
    db.add(base)
    db.flush()

    detail = models.EndowmentPolicy(
        policy_id=base.id,
        with_profits=data.with_profits,
        equities=data.equities,
        managed_fund=data.managed_fund,
        fund_name=data.fund_name,
        term=data.term,
        sum_assured=data.sum_assured,
        life_assured=data.life_assured,
    )
    db.add(detail)
    db.commit()
    db.refresh(base)
    _log_event(db, source="policies", message=f"create endowment policy id={base.id}")
    return base


def create_policy_commercial(db: Session, data: CommercialPolicyCreate) -> models.Policy:
    policy_number = data.policy_number
    if policy_number is None:
        policy_number = _next_counter(db, "GENAPOLICYNUM")
        if db.query(models.Policy).filter(models.Policy.policy_number == policy_number).first():
            policy_number = _next_counter(db, "GENAPOLICYNUM")
    base = models.Policy(
        policy_type="C",
        policy_number=policy_number,
        customer_id=data.customer_id,
        issue_date=data.issue_date,
        expiry_date=data.expiry_date,
        last_changed=data.last_changed,
        broker_id=data.broker_id,
        brokers_ref=data.brokers_ref,
        payment=data.payment,
        commission=None,
    )
    db.add(base)
    db.flush()

    detail = models.CommercialPolicy(
        policy_id=base.id,
        address=data.address,
        postcode=data.postcode,
        latitude=data.latitude,
        longitude=data.longitude,
        customer=data.customer,
        prop_type=data.prop_type,
        fire_peril=data.fire_peril,
        fire_premium=data.fire_premium,
        crime_peril=data.crime_peril,
        crime_premium=data.crime_premium,
        flood_peril=data.flood_peril,
        flood_premium=data.flood_premium,
        weather_peril=data.weather_peril,
        weather_premium=data.weather_premium,
        status=data.status,
        reject_reason=data.reject_reason,
    )
    db.add(detail)
    db.commit()
    db.refresh(base)
    _log_event(db, source="policies", message=f"create commercial policy id={base.id}")
    return base


def list_policies_detailed(
    db: Session,
    limit: int = 100,
    offset: int = 0,
    policy_type: str | None = None,
    customer_id: int | None = None,
    active_only: bool = False,
    postcode: str | None = None,
) -> list[dict]:
    base = list_policies(
        db,
        limit=limit,
        offset=offset,
        policy_type=policy_type,
        customer_id=customer_id,
        active_only=active_only,
        postcode=postcode,
    )
    result: list[dict] = []
    for p in base:
        det = get_policy_detail(db, p.id)
        payload = {
            "id": p.id,
            "policy_type": p.policy_type,
            "policy_number": p.policy_number,
            "customer_id": p.customer_id,
            "issue_date": p.issue_date,
            "expiry_date": p.expiry_date,
            "last_changed": p.last_changed,
            "broker_id": p.broker_id,
            "brokers_ref": p.brokers_ref,
            "payment": p.payment,
            "commission": p.commission,
            "detail": det["detail_dict"] if det else None,
        }
        result.append(payload)
    return result


def _log_event(db: Session, *, source: str, message: str, level: str = "INFO") -> None:
    try:
        db.add(models.Event(source=source, level=level, message=message))
        db.commit()
    except Exception:
        db.rollback()


def log_policy_event(db: Session, message: str, level: str = "INFO") -> None:
    _log_event(db, source="policies", message=message, level=level)
