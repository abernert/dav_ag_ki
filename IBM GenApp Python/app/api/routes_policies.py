from fastapi import APIRouter, Depends, Request, Form, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
import json

from app.db.session import get_db
from app.schemas.policies import (
    PolicyCreate,
    PolicyOut,
    PolicyUpdate,
    MotorPolicyCreate,
    HousePolicyCreate,
    EndowmentPolicyCreate,
    CommercialPolicyCreate,
)
from app.services import policies as svc
from app.services import customers as cust_svc
from app.utils.errors import CobolError, http_exception_for


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _parse_optional_int(value: str | int | None, *, field_label: str, raise_error: bool) -> tuple[int | None, str | None]:
    if value is None:
        return None, None
    if isinstance(value, int):
        return value, None
    text = value.strip()
    if not text:
        return None, None
    try:
        return int(text), None
    except ValueError:
        message = f"{field_label} muss eine ganze Zahl sein."
        if raise_error:
            raise HTTPException(status_code=400, detail=message)
        return None, message


# JSON API
@router.get("/api/policies", response_model=list[PolicyOut])
def api_list_policies(
    policy_type: str | None = None,
    customer_id: str | None = Query(default=None),
    active_only: bool = False,
    postcode: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    parsed_customer_id, _ = _parse_optional_int(customer_id, field_label="customer_id", raise_error=True)
    try:
        return svc.list_policies(
            db,
            policy_type=policy_type,
            customer_id=parsed_customer_id,
            active_only=active_only,
            postcode=postcode,
            limit=limit,
            offset=offset,
        )
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)


@router.get("/api/policies/detailed")
def api_list_policies_detailed(
    policy_type: str | None = None,
    customer_id: str | None = Query(default=None),
    active_only: bool = False,
    postcode: str | None = None,
    page: int | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    if page and page > 0:
        offset = (page - 1) * limit
    parsed_customer_id, _ = _parse_optional_int(customer_id, field_label="customer_id", raise_error=True)
    try:
        return svc.list_policies_detailed(
            db,
            policy_type=policy_type,
            customer_id=parsed_customer_id,
            active_only=active_only,
            postcode=postcode,
            limit=limit,
            offset=offset,
        )
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)


@router.post("/api/policies", response_model=PolicyOut, status_code=201)
def api_create_policy(data: PolicyCreate, db: Session = Depends(get_db)):
    try:
        return svc.create_policy(db, data)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)


@router.post("/api/policies/motor", response_model=PolicyOut, status_code=201)
def api_create_policy_motor(data: MotorPolicyCreate, db: Session = Depends(get_db)):
    try:
        return svc.create_policy_motor(db, data)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)


@router.post("/api/policies/house", response_model=PolicyOut, status_code=201)
def api_create_policy_house(data: HousePolicyCreate, db: Session = Depends(get_db)):
    try:
        return svc.create_policy_house(db, data)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)


@router.post("/api/policies/endowment", response_model=PolicyOut, status_code=201)
def api_create_policy_endowment(data: EndowmentPolicyCreate, db: Session = Depends(get_db)):
    try:
        return svc.create_policy_endowment(db, data)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)


@router.post("/api/policies/commercial", response_model=PolicyOut, status_code=201)
def api_create_policy_commercial(data: CommercialPolicyCreate, db: Session = Depends(get_db)):
    try:
        return svc.create_policy_commercial(db, data)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)


# Web UI routes
@router.get("/policies")
def ui_list_policies(
    request: Request,
    policy_type: str | None = None,
    customer_id: str | None = Query(default=None),
    active_only: bool = False,
    postcode: str | None = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    page = max(page, 1)
    offset = (page - 1) * size
    parsed_customer_id, error_message = _parse_optional_int(customer_id, field_label="Kunden-ID", raise_error=False)
    errors: list[str] = []
    if error_message:
        errors.append(error_message)
    try:
        items = svc.list_policies(
            db,
            policy_type=policy_type,
            customer_id=parsed_customer_id,
            active_only=active_only,
            postcode=postcode,
            limit=size,
            offset=offset,
        )
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    if isinstance(customer_id, str) and customer_id is not None:
        customer_value = customer_id.strip()
    else:
        customer_value = ""
    return templates.TemplateResponse(
        "policies.html",
        {
            "request": request,
            "policies": items,
            "policy_type": policy_type or "",
            "customer_id": customer_value,
            "active_only": active_only,
            "postcode": postcode or "",
            "page": page,
            "size": size,
            "errors": errors,
        },
    )


@router.get("/policies/new")
def ui_new_policy(request: Request, db: Session = Depends(get_db)):
    customers = cust_svc.list_customers(db)
    return templates.TemplateResponse("policy_form.html", {"request": request, "customers": customers})


@router.post("/policies")
def ui_create_policy(
    request: Request,
    policy_type: str = Form(...),
    customer_id: int = Form(...),
    policy_number: Optional[int] = Form(None),
    details: Optional[str] = Form(None),
    commission: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    details_dict = {}
    if details:
        try:
            details_dict = json.loads(details)
        except Exception:
            details_dict = {"raw": details}

    data = PolicyCreate(
        policy_type=policy_type,
        policy_number=policy_number,
        customer_id=customer_id,
        commission=commission,
        details=details_dict,
    )
    try:
        svc.create_policy(db, data)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    return RedirectResponse(url="/policies", status_code=303)


@router.get("/policies/{policy_id}")
def ui_policy_detail(policy_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        data = svc.get_policy_detail(db, policy_id)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    if not data:
        raise HTTPException(status_code=404, detail="Policy not found")
    return templates.TemplateResponse("policy_detail.html", {"request": request, **data})


@router.get("/policies/{policy_id}/edit")
def ui_policy_edit(policy_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        data = svc.get_policy_detail(db, policy_id)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    if not data:
        raise HTTPException(status_code=404, detail="Policy not found")
    return templates.TemplateResponse("policy_edit.html", {"request": request, **data})


@router.post("/policies/{policy_id}/edit")
def ui_policy_edit_submit(
    policy_id: int,
    request: Request,
    db: Session = Depends(get_db),
    # common
    policy_number: int | None = None,
    issue_date: str | None = None,
    expiry_date: str | None = None,
    brokers_ref: str | None = None,
    broker_id: int | None = None,
    payment: int | None = None,
    commission: int | None = None,
    # motor
    make: str | None = None,
    model: str | None = None,
    value: int | None = None,
    reg_number: str | None = None,
    colour: str | None = None,
    cc: int | None = None,
    manufactured: str | None = None,
    premium: int | None = None,
    accidents: int | None = None,
    # house
    property_type: str | None = None,
    bedrooms: int | None = None,
    house_name: str | None = None,
    house_number: str | None = None,
    postcode: str | None = None,
    # endowment
    with_profits: str | None = None,
    equities: str | None = None,
    managed_fund: str | None = None,
    fund_name: str | None = None,
    term: int | None = None,
    sum_assured: int | None = None,
    life_assured: str | None = None,
    # commercial
    address: str | None = None,
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
):
    try:
        with db.begin():
            svc.update_policy(
                db,
                policy_id,
                data=PolicyUpdate(
                    policy_number=policy_number,
                    issue_date=issue_date,
                    expiry_date=expiry_date,
                    broker_id=broker_id,
                    brokers_ref=brokers_ref,
                    payment=payment,
                    commission=commission,
                ),
                commit=False,
                log=False,
            )
            current_policy = svc.get_policy(db, policy_id)
            if not current_policy:
                raise CobolError("01", "Policy not found")
            if current_policy.policy_type == "M":
                svc.update_policy_motor(
                    db,
                    policy_id,
                    make=make,
                    model=model,
                    value=value,
                    reg_number=reg_number,
                    colour=colour,
                    cc=cc,
                    manufactured=manufactured,
                    premium=premium,
                    accidents=accidents,
                    commit=False,
                )
            elif current_policy.policy_type == "H":
                svc.update_policy_house(
                    db,
                    policy_id,
                    property_type=property_type,
                    bedrooms=bedrooms,
                    value=value,
                    house_name=house_name,
                    house_number=house_number,
                    postcode=postcode,
                    commit=False,
                )
            elif current_policy.policy_type == "E":
                svc.update_policy_endowment(
                    db,
                    policy_id,
                    with_profits=with_profits,
                    equities=equities,
                    managed_fund=managed_fund,
                    fund_name=fund_name,
                    term=term,
                    sum_assured=sum_assured,
                    life_assured=life_assured,
                    commit=False,
                )
            elif current_policy.policy_type == "C":
                svc.update_policy_commercial(
                    db,
                    policy_id,
                    address=address,
                    postcode=postcode,
                    latitude=latitude,
                    longitude=longitude,
                    customer=customer,
                    prop_type=prop_type,
                    fire_peril=fire_peril,
                    fire_premium=fire_premium,
                    crime_peril=crime_peril,
                    crime_premium=crime_premium,
                    flood_peril=flood_peril,
                    flood_premium=flood_premium,
                    weather_peril=weather_peril,
                    weather_premium=weather_premium,
                    status=status,
                    reject_reason=reject_reason,
                    commit=False,
                )
        svc.log_policy_event(db, f"update policy id={policy_id}")
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    return RedirectResponse(url=f"/policies/{policy_id}", status_code=303)


@router.post("/policies/{policy_id}/delete")
def ui_delete_policy(policy_id: int, db: Session = Depends(get_db)):
    try:
        svc.delete_policy(db, policy_id)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    return RedirectResponse(url="/policies", status_code=303)


@router.put("/api/policies/{policy_id}", response_model=PolicyOut)
def api_update_policy(policy_id: int, data: PolicyUpdate, db: Session = Depends(get_db)):
    try:
        return svc.update_policy(db, policy_id, data)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)


@router.put("/api/policies/motor/{policy_id}")
def api_update_policy_motor(
    policy_id: int,
    make: str | None = None,
    model: str | None = None,
    value: int | None = None,
    reg_number: str | None = None,
    colour: str | None = None,
    cc: int | None = None,
    manufactured: str | None = None,
    premium: int | None = None,
    accidents: int | None = None,
    db: Session = Depends(get_db),
):
    try:
        svc.update_policy_motor(
            db,
            policy_id,
            make=make,
            model=model,
            value=value,
            reg_number=reg_number,
            colour=colour,
            cc=cc,
            manufactured=manufactured,
            premium=premium,
            accidents=accidents,
        )
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    return {"ok": True}


@router.put("/api/policies/house/{policy_id}")
def api_update_policy_house(
    policy_id: int,
    property_type: str | None = None,
    bedrooms: int | None = None,
    value: int | None = None,
    house_name: str | None = None,
    house_number: str | None = None,
    postcode: str | None = None,
    db: Session = Depends(get_db),
):
    try:
        svc.update_policy_house(
            db,
            policy_id,
            property_type=property_type,
            bedrooms=bedrooms,
            value=value,
            house_name=house_name,
            house_number=house_number,
            postcode=postcode,
        )
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    return {"ok": True}


@router.put("/api/policies/endowment/{policy_id}")
def api_update_policy_endowment(
    policy_id: int,
    with_profits: str | None = None,
    equities: str | None = None,
    managed_fund: str | None = None,
    fund_name: str | None = None,
    term: int | None = None,
    sum_assured: int | None = None,
    life_assured: str | None = None,
    db: Session = Depends(get_db),
):
    try:
        svc.update_policy_endowment(
            db,
            policy_id,
            with_profits=with_profits,
            equities=equities,
            managed_fund=managed_fund,
            fund_name=fund_name,
            term=term,
            sum_assured=sum_assured,
            life_assured=life_assured,
        )
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    return {"ok": True}


@router.put("/api/policies/commercial/{policy_id}")
def api_update_policy_commercial(
    policy_id: int,
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
    db: Session = Depends(get_db),
):
    try:
        svc.update_policy_commercial(
            db,
            policy_id,
            address=address,
            postcode=postcode,
            latitude=latitude,
            longitude=longitude,
            customer=customer,
            prop_type=prop_type,
            fire_peril=fire_peril,
            fire_premium=fire_premium,
            crime_peril=crime_peril,
            crime_premium=crime_premium,
            flood_peril=flood_peril,
            flood_premium=flood_premium,
            weather_peril=weather_peril,
            weather_premium=weather_premium,
            status=status,
            reject_reason=reject_reason,
        )
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    return {"ok": True}
