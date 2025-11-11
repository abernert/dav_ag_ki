from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import date, datetime


class PolicyCreate(BaseModel):
    policy_type: str = Field(..., min_length=1, max_length=1)  # C/E/H/M
    policy_number: Optional[int] = None
    customer_id: int
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    last_changed: Optional[datetime] = None
    broker_id: Optional[int] = None
    brokers_ref: Optional[str] = Field(None, max_length=10)
    payment: Optional[int] = None
    commission: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


class PolicyOut(BaseModel):
    id: int
    policy_type: str
    policy_number: Optional[int]
    customer_id: int
    commission: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


# Type-specific create schemas

class MotorPolicyCreate(BaseModel):
    customer_id: int
    policy_number: Optional[int] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    last_changed: Optional[datetime] = None
    broker_id: Optional[int] = None
    brokers_ref: Optional[str] = Field(None, max_length=10)
    payment: Optional[int] = None

    make: str = Field(..., max_length=15)
    model: str = Field(..., max_length=15)
    value: Optional[int] = None
    reg_number: str = Field(..., max_length=7)
    colour: Optional[str] = Field(None, max_length=8)
    cc: Optional[int] = None
    manufactured: Optional[str] = Field(None, max_length=10)
    premium: Optional[int] = None
    accidents: Optional[int] = None


class PolicyUpdate(BaseModel):
    policy_number: Optional[int] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    last_changed: Optional[datetime] = None
    broker_id: Optional[int] = None
    brokers_ref: Optional[str] = Field(None, max_length=10)
    payment: Optional[int] = None
    commission: Optional[int] = None


class HousePolicyCreate(BaseModel):
    customer_id: int
    policy_number: Optional[int] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    last_changed: Optional[datetime] = None
    broker_id: Optional[int] = None
    brokers_ref: Optional[str] = Field(None, max_length=10)
    payment: Optional[int] = None

    property_type: str = Field(..., max_length=15)
    bedrooms: int
    value: int
    house_name: Optional[str] = Field(None, max_length=20)
    house_number: Optional[str] = Field(None, max_length=4)
    postcode: str = Field(..., max_length=8)


class EndowmentPolicyCreate(BaseModel):
    customer_id: int
    policy_number: Optional[int] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    last_changed: Optional[datetime] = None
    broker_id: Optional[int] = None
    brokers_ref: Optional[str] = Field(None, max_length=10)
    payment: Optional[int] = None

    with_profits: Optional[str] = Field(None, max_length=1)
    equities: Optional[str] = Field(None, max_length=1)
    managed_fund: Optional[str] = Field(None, max_length=1)
    fund_name: str = Field(..., max_length=10)
    term: int
    sum_assured: int
    life_assured: Optional[str] = Field(None, max_length=31)


class CommercialPolicyCreate(BaseModel):
    customer_id: int
    policy_number: Optional[int] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    last_changed: Optional[datetime] = None
    broker_id: Optional[int] = None
    brokers_ref: Optional[str] = Field(None, max_length=10)
    payment: Optional[int] = None

    address: str = Field(..., max_length=255)
    postcode: str = Field(..., max_length=8)
    latitude: Optional[str] = Field(None, max_length=11)
    longitude: Optional[str] = Field(None, max_length=11)
    customer: Optional[str] = Field(None, max_length=255)
    prop_type: Optional[str] = Field(None, max_length=255)
    fire_peril: Optional[int] = None
    fire_premium: Optional[int] = None
    crime_peril: Optional[int] = None
    crime_premium: Optional[int] = None
    flood_peril: Optional[int] = None
    flood_premium: Optional[int] = None
    weather_peril: Optional[int] = None
    weather_premium: Optional[int] = None
    status: Optional[int] = None
    reject_reason: Optional[str] = Field(None, max_length=255)
