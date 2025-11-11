from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
import datetime as dt


class ClaimCreate(BaseModel):
    policy_id: int
    number: Optional[int] = None
    date: Optional[dt.date] = None
    paid: Optional[int] = None
    value: Optional[int] = None
    cause: Optional[str] = Field(None, max_length=255)
    observations: Optional[str] = Field(None, max_length=255)


class ClaimUpdate(BaseModel):
    number: Optional[int] = None
    date: Optional[dt.date] = None
    paid: Optional[int] = None
    value: Optional[int] = None
    cause: Optional[str] = Field(None, max_length=255)
    observations: Optional[str] = Field(None, max_length=255)


class ClaimOut(BaseModel):
    id: int
    policy_id: int
    number: Optional[int]
    date: Optional[dt.date]
    value: Optional[int]
    model_config = ConfigDict(from_attributes=True)
