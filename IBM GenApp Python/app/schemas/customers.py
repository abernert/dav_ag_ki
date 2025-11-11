from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional
from datetime import date


class CustomerCreate(BaseModel):
    first_name: str = Field(..., max_length=10)
    last_name: str = Field(..., max_length=20)
    date_of_birth: Optional[date] = None
    house_name: Optional[str] = Field(None, max_length=20)
    house_number: Optional[str] = Field(None, max_length=4)
    postcode: Optional[str] = Field(None, max_length=8)
    phone_mobile: Optional[str] = Field(None, max_length=20)
    phone_home: Optional[str] = Field(None, max_length=20)
    email_address: Optional[EmailStr] = None


class CustomerOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    date_of_birth: Optional[str]
    postcode: Optional[str]
    model_config = ConfigDict(from_attributes=True)


class CustomerUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=10)
    last_name: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    house_name: Optional[str] = Field(None, max_length=20)
    house_number: Optional[str] = Field(None, max_length=4)
    postcode: Optional[str] = Field(None, max_length=8)
    phone_mobile: Optional[str] = Field(None, max_length=20)
    phone_home: Optional[str] = Field(None, max_length=20)
    email_address: Optional[EmailStr] = None


class CustomerSecurityIn(BaseModel):
    customer_pass: Optional[str] = Field(None, max_length=32)
    state_indicator: Optional[str] = Field(None, max_length=1)
    pass_changes: Optional[int] = None


class CustomerSecurityOut(BaseModel):
    customer_number: int
    customer_pass: Optional[str]
    state_indicator: Optional[str]
    pass_changes: Optional[int]
    model_config = ConfigDict(from_attributes=True)
