from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.services import claims as svc
from app.schemas.claims import ClaimCreate, ClaimOut, ClaimUpdate
from app.utils.errors import CobolError, http_exception_for


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/api/claims", response_model=list[ClaimOut])
def api_list_claims(
    policy_id: Optional[int] = None,
    page: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    if page and page > 0:
        offset = (page - 1) * limit
    try:
        return svc.list_claims(db, policy_id=policy_id, limit=limit, offset=offset)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)


@router.post("/api/claims", response_model=ClaimOut, status_code=201)
def api_create_claim(data: ClaimCreate, db: Session = Depends(get_db)):
    try:
        return svc.create_claim(db, data)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)


@router.get("/api/claims/{claim_id}", response_model=ClaimOut)
def api_get_claim(claim_id: int, db: Session = Depends(get_db)):
    try:
        return svc.get_claim(db, claim_id)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)


@router.put("/api/claims/{claim_id}", response_model=ClaimOut)
def api_update_claim(claim_id: int, data: ClaimUpdate, db: Session = Depends(get_db)):
    try:
        return svc.update_claim(db, claim_id, data)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)


@router.get("/claims")
def ui_list_claims(
    request: Request,
    policy_id: Optional[int] = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    page = max(page, 1)
    offset = (page - 1) * size
    try:
        items = svc.list_claims(db, policy_id=policy_id, limit=size, offset=offset)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    return templates.TemplateResponse(
        "claims.html",
        {
            "request": request,
            "claims": items,
            "policy_id": policy_id,
            "page": page,
            "size": size,
        },
    )


@router.get("/claims/new")
def ui_new_claim(request: Request):
    return templates.TemplateResponse("claim_form.html", {"request": request})


@router.post("/claims")
def ui_create_claim(
    request: Request,
    policy_id: int = Form(...),
    number: Optional[int] = Form(None),
    date: Optional[str] = Form(None),
    paid: Optional[int] = Form(None),
    value: Optional[int] = Form(None),
    cause: Optional[str] = Form(None),
    observations: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    try:
        svc.create_claim(
            db,
            ClaimCreate(
                policy_id=policy_id,
                number=number,
                date=date,
                paid=paid,
                value=value,
                cause=cause,
                observations=observations,
            ),
        )
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    return RedirectResponse(url="/claims", status_code=303)


@router.get("/claims/{claim_id}/edit")
def ui_edit_claim(claim_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        claim = svc.get_claim(db, claim_id)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    return templates.TemplateResponse("claim_edit.html", {"request": request, "claim": claim})


@router.post("/claims/{claim_id}/edit")
def ui_update_claim(
    claim_id: int,
    request: Request,
    number: Optional[int] = Form(None),
    date: Optional[str] = Form(None),
    paid: Optional[int] = Form(None),
    value: Optional[int] = Form(None),
    cause: Optional[str] = Form(None),
    observations: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    try:
        svc.update_claim(
            db,
            claim_id,
            ClaimUpdate(
                number=number,
                date=date,
                paid=paid,
                value=value,
                cause=cause,
                observations=observations,
            ),
        )
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    return RedirectResponse(url="/claims", status_code=303)


@router.post("/claims/{claim_id}/delete")
def ui_delete_claim(claim_id: int, db: Session = Depends(get_db)):
    try:
        svc.delete_claim(db, claim_id)
    except CobolError as exc:
        raise http_exception_for(exc.code, exc.message)
    return RedirectResponse(url="/claims", status_code=303)
