import os
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.session import Base, engine, get_db
from app.db import models
from app.api.routes_customers import router as customers_router
from app.api.routes_policies import router as policies_router
from app.api.routes_claims import router as claims_router
from app.api.routes_events import router as events_router


def _ensure_runtime_migrations() -> None:
    """Lightweight, best-effort migrations for SQLite dev DB.
    - Add commission column to policies if missing.
    - Ensure unique index on policies.policy_number.
    """
    try:
        with engine.connect() as conn:
            # detect columns in policies
            cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info('policies')").fetchall()]
            if 'commission' not in cols:
                conn.exec_driver_sql("ALTER TABLE policies ADD COLUMN commission INTEGER")
            # unique index for policy_number
            conn.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_policies_policy_number ON policies(policy_number)"
            )
    except Exception:
        # non-fatal in dev
        pass


def init_db() -> None:
    # Create tables if not exist (simple approach for local dev)
    Base.metadata.create_all(bind=engine)
    _ensure_runtime_migrations()


def create_app() -> FastAPI:
    app = FastAPI(title="GenApp Python", version="0.1.0")
    init_db()

    # Static & templates
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    templates = Jinja2Templates(directory="app/templates")

    # Routers
    app.include_router(customers_router)
    app.include_router(policies_router)
    app.include_router(claims_router)
    app.include_router(events_router)

    @app.get("/")
    def index(request: Request, db: Session = Depends(get_db)):
        counts = {
            "customers": db.execute(select(func.count(models.Customer.id))).scalar_one(),
            "policies": db.execute(select(func.count(models.Policy.id))).scalar_one(),
            "claims": db.execute(select(func.count(models.Claim.id))).scalar_one(),
            "events": db.execute(select(func.count(models.Event.id))).scalar_one(),
        }
        return templates.TemplateResponse("index.html", {"request": request, "counts": counts})

    return app


app = create_app()

# To run locally:
# uvicorn app.main:app --reload
