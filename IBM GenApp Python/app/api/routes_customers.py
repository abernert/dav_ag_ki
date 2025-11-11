from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.schemas.customers import CustomerCreate, CustomerOut, CustomerUpdate, CustomerSecurityIn, CustomerSecurityOut
from app.services import customers as svc
from app.utils.errors import CobolError, http_exception_for


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# JSON API
@router.get("/api/customers", response_model=list[CustomerOut])
def api_list_customers(
    name: str | None = None,
    postcode: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    try:
        return svc.list_customers(db, limit=limit, offset=offset, name=name, postcode=postcode)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)


@router.post("/api/customers", response_model=CustomerOut, status_code=201)
def api_create_customer(data: CustomerCreate, db: Session = Depends(get_db)):
    try:
        return svc.create_customer(db, data)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)


@router.get("/api/customers/{customer_id}", response_model=CustomerOut)
def api_get_customer(customer_id: int, db: Session = Depends(get_db)):
    try:
        obj = svc.get_customer(db, customer_id)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    if not obj:
        raise HTTPException(status_code=404, detail="Customer not found")
    return obj


@router.put("/api/customers/{customer_id}", response_model=CustomerOut)
def api_update_customer(customer_id: int, data: CustomerUpdate, db: Session = Depends(get_db)):
    try:
        return svc.update_customer(db, customer_id, data)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)


# Security endpoints (Customer Secure)
@router.get("/api/customers/{customer_id}/security", response_model=CustomerSecurityOut)
def api_get_customer_security(
    customer_id: int,
    rotate: bool = False,
    db: Session = Depends(get_db),
):
    try:
        if rotate:
            obj = svc.rotate_customer_security(db, customer_id)
        else:
            obj = svc.get_customer_security(db, customer_id)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    if not obj:
        raise HTTPException(status_code=404, detail="Customer or security not found")
    return obj


@router.put("/api/customers/{customer_id}/security", response_model=CustomerSecurityOut)
def api_set_customer_security(
    customer_id: int,
    data: CustomerSecurityIn,
    rotate: bool = False,
    db: Session = Depends(get_db),
):
    try:
        if rotate and not data.model_dump(exclude_unset=True):
            obj = svc.rotate_customer_security(db, customer_id)
        else:
            obj = svc.set_customer_security(db, customer_id, data)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    if not obj:
        raise HTTPException(status_code=404, detail="Customer not found")
    return obj


# Web UI routes
@router.get("/customers")
def ui_list_customers(
    request: Request,
    name: str | None = None,
    postcode: str | None = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    page = max(page, 1)
    offset = (page - 1) * size
    try:
        items = svc.list_customers(db, limit=size, offset=offset, name=name, postcode=postcode)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    return templates.TemplateResponse(
        "customers.html",
        {"request": request, "customers": items, "page": page, "size": size, "name": name or "", "postcode": postcode or ""},
    )


@router.get("/customers/new")
def ui_new_customer(request: Request):
    return templates.TemplateResponse("customer_form.html", {"request": request})


@router.get("/customers/{customer_id}")
def ui_customer_detail(customer_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        obj = svc.get_customer(db, customer_id)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    if not obj:
        raise HTTPException(status_code=404, detail="Customer not found")
    return templates.TemplateResponse("customer_detail.html", {"request": request, "customer": obj})


@router.post("/customers")
def ui_create_customer(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    date_of_birth: Optional[str] = Form(None),
    house_name: Optional[str] = Form(None),
    house_number: Optional[str] = Form(None),
    postcode: Optional[str] = Form(None),
    phone_mobile: Optional[str] = Form(None),
    phone_home: Optional[str] = Form(None),
    email_address: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    data = CustomerCreate(
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        house_name=house_name,
        house_number=house_number,
        postcode=postcode,
        phone_mobile=phone_mobile,
        phone_home=phone_home,
        email_address=email_address,
    )
    try:
        svc.create_customer(db, data)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    return RedirectResponse(url="/customers", status_code=303)


@router.get("/customers/{customer_id}/edit")
def ui_edit_customer(customer_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        obj = svc.get_customer(db, customer_id)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    if not obj:
        raise HTTPException(status_code=404, detail="Customer not found")
    return templates.TemplateResponse("customer_edit.html", {"request": request, "customer": obj})


@router.post("/customers/{customer_id}/edit")
def ui_update_customer_submit(
    customer_id: int,
    request: Request,
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    date_of_birth: Optional[str] = Form(None),
    house_name: Optional[str] = Form(None),
    house_number: Optional[str] = Form(None),
    postcode: Optional[str] = Form(None),
    phone_mobile: Optional[str] = Form(None),
    phone_home: Optional[str] = Form(None),
    email_address: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    data = CustomerUpdate(
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        house_name=house_name,
        house_number=house_number,
        postcode=postcode,
        phone_mobile=phone_mobile,
        phone_home=phone_home,
        email_address=email_address,
    )
    try:
        svc.update_customer(db, customer_id, data)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    return RedirectResponse(url="/customers", status_code=303)


@router.post("/customers/{customer_id}/delete")
def ui_delete_customer(customer_id: int, db: Session = Depends(get_db)):
    try:
        svc.delete_customer(db, customer_id)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    return RedirectResponse(url="/customers", status_code=303)
