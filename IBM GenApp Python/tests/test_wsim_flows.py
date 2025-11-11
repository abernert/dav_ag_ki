from __future__ import annotations

import os
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure isolated SQLite DB for tests (in temp dir to avoid perms)
TEST_DB = Path("test_output") / "test_genapp_wsim.db"
TEST_DB.parent.mkdir(parents=True, exist_ok=True)
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"  # type: ignore

from app.main import create_app  # noqa: E402
from app.utils import datasets  # noqa: E402


def teardown_module(module):  # noqa: D401
    if TEST_DB.exists():
        TEST_DB.unlink()
    try:
        TEST_DB.parent.rmdir()
    except OSError:
        pass


app = create_app()
client = TestClient(app)


def test_wsim_like_flow():
    first_name = datasets.random_first_name()
    last_name = datasets.random_surname()
    postcode = datasets.random_postcode()

    # 1. Create customer
    resp = client.post(
        "/api/customers",
        json={
            "first_name": first_name[:10],
            "last_name": last_name[:20],
            "postcode": postcode,
            "phone_mobile": "07123 456789",
            "email_address": f"{first_name.lower()}@example.com",
        },
    )
    assert resp.status_code == 201, resp.text
    customer = resp.json()

    # 2. Create motor policy for customer
    resp = client.post(
        "/api/policies/motor",
        json={
            "customer_id": customer["id"],
            "policy_number": None,
            "issue_date": "2024-01-01",
            "expiry_date": "2025-01-01",
            "make": "VW",
            "model": "BEETLE",
            "reg_number": "A567WWR",
            "premium": 700,
        },
    )
    assert resp.status_code == 201, resp.text
    policy = resp.json()

    # 3. Create claim for policy
    resp = client.post(
        "/api/claims",
        json={
            "policy_id": policy["id"],
            "number": 10,
            "date": "2024-06-01",
            "value": 5000,
            "cause": "FIRE",
        },
    )
    assert resp.status_code == 201, resp.text

    # 4. Query policies by postcode (WSim-like filter)
    resp = client.get(f"/api/policies?postcode={postcode}&limit=10")
    assert resp.status_code == 200
    policies = resp.json()
    assert any(p["id"] == policy["id"] for p in policies)

    # 5. Detailed endpoint with paging
    resp = client.get("/api/policies/detailed", params={"limit": 5, "page": 1})
    assert resp.status_code == 200
    detailed = resp.json()
    assert any(item["id"] == policy["id"] for item in detailed)

    # 6. Claims listing with paging
    resp = client.get("/api/claims", params={"limit": 5, "page": 1})
    assert resp.status_code == 200
    claim_list = resp.json()
    assert any(c["policy_id"] == policy["id"] for c in claim_list)
