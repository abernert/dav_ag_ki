from sqlalchemy.orm import Session
from typing import List, Optional
import os
import secrets
import hashlib

from app.db import models
from app.schemas.customers import CustomerCreate, CustomerUpdate, CustomerSecurityIn
from app.utils.errors import CobolError


DEFAULT_SECURITY_PASS = os.getenv("GENAPP_DEFAULT_CUSTOMER_PASS", "5732fec825535eeafb8fac50fee3a8aa")
DEFAULT_SECURITY_STATE = os.getenv("GENAPP_DEFAULT_CUSTOMER_STATE", "N")
DEFAULT_SECURITY_COUNT = int(os.getenv("GENAPP_DEFAULT_CUSTOMER_COUNT", "0"))
DEFAULT_SECURITY_MODE = os.getenv("GENAPP_SECURITY_MODE", "static").lower()
DEFAULT_SECURITY_LENGTH = int(os.getenv("GENAPP_SECURITY_RANDOM_BYTES", "8"))


def _next_counter(db: Session, name: str) -> int:
    # simple counter using a single-row table, serialized by transaction
    ctr = db.get(models.Counter, name)
    if not ctr:
        ctr = models.Counter(name=name, value=0)
        db.add(ctr)
        db.flush()
    ctr.value += 1
    db.add(ctr)
    db.flush()
    return ctr.value


def create_customer(db: Session, data: CustomerCreate) -> models.Customer:
    cust_num = _next_counter(db, "GENACUSTNUM")
    obj = models.Customer(
        customer_number=cust_num,
        first_name=data.first_name,
        last_name=data.last_name,
        date_of_birth=data.date_of_birth,
        house_name=data.house_name,
        house_number=data.house_number,
        postcode=data.postcode,
        phone_mobile=data.phone_mobile,
        phone_home=data.phone_home,
        email_address=str(data.email_address) if data.email_address else None,
    )
    db.add(obj)
    # ensure matching security record exists in same transaction
    password, state, count = _generate_default_security_values()
    _ensure_customer_security(
        db,
        customer=obj,
        password=password,
        state=state,
        count=count,
    )
    db.commit()
    db.refresh(obj)
    # audit
    _log_event(db, source="customers", message=f"create customer id={obj.id} cnum={obj.customer_number}")
    return obj


def list_customers(
    db: Session,
    limit: int = 100,
    offset: int = 0,
    name: str | None = None,
    postcode: str | None = None,
) -> List[models.Customer]:
    q = db.query(models.Customer)
    if name:
        like = f"%{name}%"
        q = q.filter((models.Customer.first_name.ilike(like)) | (models.Customer.last_name.ilike(like)))
    if postcode:
        q = q.filter(models.Customer.postcode.ilike(f"%{postcode}%"))
    return q.order_by(models.Customer.id.asc()).offset(offset).limit(limit).all()


def get_customer(db: Session, customer_id: int) -> Optional[models.Customer]:
    return db.get(models.Customer, customer_id)


def delete_customer(db: Session, customer_id: int) -> bool:
    obj = db.get(models.Customer, customer_id)
    if not obj:
        raise CobolError("01", "Customer not found")
    db.delete(obj)
    db.commit()
    _log_event(db, source="customers", message=f"delete customer id={customer_id}")
    return True


def update_customer(db: Session, customer_id: int, data: CustomerUpdate) -> Optional[models.Customer]:
    obj = db.get(models.Customer, customer_id)
    if not obj:
        raise CobolError("01", "Customer not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "email_address" and value is not None:
            setattr(obj, field, str(value))
        else:
            setattr(obj, field, value)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    _log_event(db, source="customers", message=f"update customer id={customer_id}")
    return obj


def set_customer_security(db: Session, customer_id: int, data: CustomerSecurityIn) -> Optional[models.CustomerSecure]:
    cust = db.get(models.Customer, customer_id)
    if not cust:
        raise CobolError("01", "Customer not found")
    sec = _ensure_customer_security(db, customer=cust)
    payload = data.model_dump(exclude_unset=True)
    for k, v in payload.items():
        setattr(sec, k, v)
    db.add(sec)
    db.commit()
    db.refresh(sec)
    _log_event(db, source="customers", message=f"set security customer_number={cust.customer_number}")
    return sec


def get_customer_security(db: Session, customer_id: int) -> Optional[models.CustomerSecure]:
    cust = db.get(models.Customer, customer_id)
    if not cust:
        raise CobolError("01", "Customer not found")
    return db.get(models.CustomerSecure, cust.customer_number)


def rotate_customer_security(db: Session, customer_id: int) -> Optional[models.CustomerSecure]:
    cust = db.get(models.Customer, customer_id)
    if not cust:
        raise CobolError("01", "Customer not found")
    sec = _ensure_customer_security(db, customer=cust)
    password, state, count = _generate_default_security_values()
    sec.customer_pass = password
    if state is not None:
        sec.state_indicator = state
    if count is not None:
        sec.pass_changes = count
    db.add(sec)
    db.commit()
    db.refresh(sec)
    _log_event(db, source="customers", message=f"rotate security customer_number={cust.customer_number}")
    return sec


def _log_event(db: Session, *, source: str, message: str, level: str = "INFO") -> None:
    try:
        db.add(models.Event(source=source, level=level, message=message))
        db.commit()
    except Exception:
        db.rollback()


def _ensure_customer_security(
    db: Session,
    *,
    customer: models.Customer,
    password: Optional[str] = None,
    state: Optional[str] = None,
    count: Optional[int] = None,
) -> models.CustomerSecure:
    sec = db.get(models.CustomerSecure, customer.customer_number)
    if sec:
        return sec
    sec = models.CustomerSecure(
        customer_number=customer.customer_number,
        customer_pass=password,
        state_indicator=state,
        pass_changes=count if count is not None else 0,
    )
    db.add(sec)
    return sec


def _generate_default_security_values() -> tuple[str, str | None, int | None]:
    mode = DEFAULT_SECURITY_MODE
    if mode == "random" or mode == "random_md5":
        token = secrets.token_bytes(DEFAULT_SECURITY_LENGTH)
        hashed = hashlib.md5(token).hexdigest()
        return hashed, DEFAULT_SECURITY_STATE, 0
    if mode == "rotate":
        token = secrets.token_bytes(DEFAULT_SECURITY_LENGTH)
        hashed = hashlib.md5(token).hexdigest()
        # increment count for visibility
        return hashed, DEFAULT_SECURITY_STATE, DEFAULT_SECURITY_COUNT + 1
    # static fallback
    return DEFAULT_SECURITY_PASS, DEFAULT_SECURITY_STATE, DEFAULT_SECURITY_COUNT
