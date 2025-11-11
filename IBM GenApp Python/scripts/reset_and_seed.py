"""Reset local SQLite database and seed sample data from cntl/wsim sources."""
from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data/seed_data.json"
DB_PATH = BASE_DIR / "genapp.db"

# Ensure consistent DB location before SQLAlchemy engine is created
if "DATABASE_URL" not in os.environ or os.environ["DATABASE_URL"].startswith("sqlite:///./"):
    os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH}"

# Ensure project root is importable when script is launched from anywhere
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.main import init_db
from app.db.session import SessionLocal, engine
from app.services import customers as customer_service
from app.services import policies as policy_service
from app.services import claims as claim_service
from app.schemas.customers import CustomerCreate
from app.schemas.policies import (
    MotorPolicyCreate,
    HousePolicyCreate,
    CommercialPolicyCreate,
)
from app.schemas.claims import ClaimCreate


def _cleanup_db() -> None:
    # Close existing connections so SQLite file can be replaced cleanly
    engine.dispose()
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Removed {DB_PATH}")


def _load_seed_data() -> dict:
    with DATA_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def seed() -> None:
    data = _load_seed_data()
    session = SessionLocal()
    customer_map: dict[str, object] = {}
    policy_map: dict[str, object] = {}

    try:
        # Customers
        for customer in data.get("customers", []):
            payload = CustomerCreate(
                first_name=customer["first_name"],
                last_name=customer["last_name"],
                date_of_birth=_parse_date(customer.get("date_of_birth")),
                house_name=customer.get("house_name") or None,
                house_number=customer.get("house_number") or None,
                postcode=customer.get("postcode") or None,
                phone_mobile=customer.get("phone_mobile") or None,
                phone_home=customer.get("phone_home") or None,
                email_address=customer.get("email_address") or None,
            )
            obj = customer_service.create_customer(session, payload)
            customer_map[customer["key"]] = obj
            print(f"Inserted customer {obj.customer_number} ({obj.first_name} {obj.last_name})")

        # Policies
        for policy in data.get("policies", []):
            customer = customer_map[policy["customer_key"]]
            base_kwargs = dict(
                customer_id=customer.id,
                policy_number=policy.get("policy_number"),
                issue_date=_parse_date(policy.get("issue_date")),
                expiry_date=_parse_date(policy.get("expiry_date")),
                broker_id=policy.get("broker_id"),
                payment=policy.get("payment"),
                commission=policy.get("commission"),
            )
            policy_type = policy["type"].upper()
            if policy_type == "M":
                detail = policy["motor_detail"]
                obj = policy_service.create_policy_motor(
                    session,
                    MotorPolicyCreate(
                        **base_kwargs,
                        make=detail["make"],
                        model=detail["model"],
                        value=detail.get("value"),
                        reg_number=detail["reg_number"],
                        colour=detail.get("colour"),
                        cc=detail.get("cc"),
                        manufactured=detail.get("manufactured"),
                        premium=detail.get("premium"),
                        accidents=detail.get("accidents"),
                    ),
                )
            elif policy_type == "H":
                detail = policy["house_detail"]
                obj = policy_service.create_policy_house(
                    session,
                    HousePolicyCreate(
                        **base_kwargs,
                        property_type=detail["property_type"],
                        bedrooms=detail.get("bedrooms", 0),
                        value=detail.get("value", 0),
                        house_name=detail.get("house_name"),
                        house_number=detail.get("house_number"),
                        postcode=detail.get("postcode"),
                    ),
                )
            elif policy_type == "C":
                detail = policy["commercial_detail"]
                obj = policy_service.create_policy_commercial(
                    session,
                    CommercialPolicyCreate(
                        **base_kwargs,
                        address=detail["address"],
                        postcode=detail["postcode"],
                        latitude=detail.get("latitude"),
                        longitude=detail.get("longitude"),
                        customer=detail.get("customer"),
                        prop_type=detail.get("prop_type"),
                        fire_peril=detail.get("fire_peril"),
                        fire_premium=detail.get("fire_premium"),
                        crime_peril=detail.get("crime_peril"),
                        crime_premium=detail.get("crime_premium"),
                        flood_peril=detail.get("flood_peril"),
                        flood_premium=detail.get("flood_premium"),
                        weather_peril=detail.get("weather_peril"),
                        weather_premium=detail.get("weather_premium"),
                        status=detail.get("status"),
                        reject_reason=detail.get("reject_reason"),
                    ),
                )
            elif policy_type == "E":
                raise NotImplementedError("Seed data does not include Endowment example yet")
            else:
                raise ValueError(f"Unsupported policy type {policy_type}")

            policy_map[policy["key"]] = obj
            print(f"Inserted policy {obj.policy_number} ({obj.policy_type}) for customer {obj.customer_id}")

        # Claims
        for claim in data.get("claims", []):
            policy = policy_map[claim["policy_key"]]
            claim_obj = claim_service.create_claim(
                session,
                ClaimCreate(
                    policy_id=policy.id,
                    number=claim.get("number"),
                    date=_parse_date(claim.get("date")),
                    paid=claim.get("paid"),
                    value=claim.get("value"),
                    cause=claim.get("cause"),
                    observations=claim.get("observations"),
                ),
            )
            print(f"Inserted claim #{claim_obj.number or claim_obj.id} for policy {policy.policy_number}")

    finally:
        session.close()


def main() -> None:
    _cleanup_db()
    init_db()
    seed()
    print("Seed complete.")


if __name__ == "__main__":
    main()
