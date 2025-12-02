"""Relative information models."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class RelativeInfo(BaseModel):
    """Model for relative_info - relatives of submitter."""
    relative_id: int
    submitter_id: int
    nacc_id: int
    index: int
    relationship_id: int = Field(..., description="1=Father, 2=Mother, 3=Sibling, 4=Child, 5=SpouseFather, 6=SpouseMother")
    title: Optional[str] = Field(None, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)
    occupation: Optional[str] = Field(None, max_length=200)
    workplace: Optional[str] = Field(None, max_length=500)
    is_deceased: bool = Field(default=False, description="Whether relative is deceased")
    latest_submitted_date: Optional[date] = None
