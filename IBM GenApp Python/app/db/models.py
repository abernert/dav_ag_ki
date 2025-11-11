from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, UTC

from .session import Base


def _utc_now() -> datetime:
    return datetime.now(UTC)


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    # Analoger Zähler zu Named Counter Server
    customer_number = Column(Integer, unique=True, index=True, nullable=False)
    first_name = Column(String(10), nullable=False)
    last_name = Column(String(20), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    house_name = Column(String(20), nullable=True)
    house_number = Column(String(4), nullable=True)
    postcode = Column(String(8), nullable=True)
    phone_mobile = Column(String(20), nullable=True)
    phone_home = Column(String(20), nullable=True)
    email_address = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=_utc_now)

    policies = relationship("Policy", back_populates="customer", cascade="all, delete-orphan")


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    policy_type = Column(String(1), nullable=False)  # C/E/H/M
    policy_number = Column(Integer, nullable=False)

    # Common policy details (subset for skeleton)
    issue_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    last_changed = Column(DateTime, nullable=True)
    broker_id = Column(Integer, nullable=True)
    brokers_ref = Column(String(10), nullable=True)
    payment = Column(Integer, nullable=True)
    commission = Column(Integer, nullable=True)

    # Flexible details for type-specific fields (JSON serialized as Text)
    details = Column(Text, nullable=True)

    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    customer = relationship("Customer", back_populates="policies")

    created_at = Column(DateTime, nullable=False, default=_utc_now)

    __table_args__ = (
        UniqueConstraint("policy_type", "customer_id", "policy_number", name="uq_policy_type_customer_number"),
    )


# Type-specific policy tables (1-1 with Policy)

class MotorPolicy(Base):
    __tablename__ = "policies_motor"

    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey("policies.id", ondelete="CASCADE"), unique=True, nullable=False)

    make = Column(String(15))
    model = Column(String(15))
    value = Column(Integer)
    reg_number = Column(String(7))
    colour = Column(String(8))
    cc = Column(Integer)
    manufactured = Column(String(10))
    premium = Column(Integer)
    accidents = Column(Integer)


class HousePolicy(Base):
    __tablename__ = "policies_house"

    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey("policies.id", ondelete="CASCADE"), unique=True, nullable=False)

    property_type = Column(String(15))
    bedrooms = Column(Integer)
    value = Column(Integer)
    house_name = Column(String(20))
    house_number = Column(String(4))
    postcode = Column(String(8))


class EndowmentPolicy(Base):
    __tablename__ = "policies_endowment"

    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey("policies.id", ondelete="CASCADE"), unique=True, nullable=False)

    with_profits = Column(String(1))
    equities = Column(String(1))
    managed_fund = Column(String(1))
    fund_name = Column(String(10))
    term = Column(Integer)
    sum_assured = Column(Integer)
    life_assured = Column(String(31))


class CommercialPolicy(Base):
    __tablename__ = "policies_commercial"

    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey("policies.id", ondelete="CASCADE"), unique=True, nullable=False)

    address = Column(String(255))
    postcode = Column(String(8))
    latitude = Column(String(11))
    longitude = Column(String(11))
    customer = Column(String(255))
    prop_type = Column(String(255))
    fire_peril = Column(Integer)
    fire_premium = Column(Integer)
    crime_peril = Column(Integer)
    crime_premium = Column(Integer)
    flood_peril = Column(Integer)
    flood_premium = Column(Integer)
    weather_peril = Column(Integer)
    weather_premium = Column(Integer)
    status = Column(Integer)
    reject_reason = Column(String(255))


class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, index=True)
    number = Column(Integer, nullable=True)
    date = Column(Date)
    paid = Column(Integer)
    value = Column(Integer)
    cause = Column(String(255))
    observations = Column(String(255))

    policy = relationship("Policy")


class Counter(Base):
    __tablename__ = "counters"

    name = Column(String(64), primary_key=True)
    value = Column(Integer, nullable=False, default=0)


class CustomerSecure(Base):
    __tablename__ = "customer_secure"

    # Mirror Db2 semantics: key by customerNumber (unique in customers)
    customer_number = Column(Integer, ForeignKey("customers.customer_number", ondelete="CASCADE"), primary_key=True)
    customer_pass = Column(String(32), nullable=True)
    state_indicator = Column(String(1), nullable=True)
    pass_changes = Column(Integer, nullable=True, default=0)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, nullable=False, default=_utc_now)
    source = Column(String(64), nullable=False)
    level = Column(String(16), nullable=False, default="INFO")
    message = Column(Text, nullable=False)
