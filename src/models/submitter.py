"""Submitter information models."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class SubmitterInfo(BaseModel):
    """Model for submitter_info - the person submitting the declaration."""
    submitter_id: int = Field(..., description="Submitter ID in system")
    title: str = Field(..., max_length=100, description="Title (e.g., นาย, นาง)")
    first_name: str = Field(..., max_length=100, description="First name")
    last_name: str = Field(..., max_length=100, description="Last name")
    age: Optional[int] = Field(None, ge=0, le=150, description="Age")
    status: Optional[str] = Field(None, max_length=100, description="Marital status")
    status_date: Optional[str] = Field(None, max_length=10, description="Status date (DD)")
    status_month: Optional[str] = Field(None, max_length=10, description="Status month (MM)")
    status_year: Optional[str] = Field(None, max_length=10, description="Status year (YYYY)")
    sub_district: Optional[str] = Field(None, max_length=100, description="Sub-district")
    district: Optional[str] = Field(None, max_length=100, description="District")
    province: Optional[str] = Field(None, max_length=100, description="Province")
    post_code: Optional[str] = Field(None, max_length=10, description="Post code")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone")
    mobile_number: Optional[str] = Field(None, max_length=20, description="Mobile")
    email: Optional[str] = Field(None, max_length=100, description="Email")
    latest_submitted_date: Optional[date] = None


class SubmitterOldName(BaseModel):
    """Model for submitter_old_name - previous names of submitter."""
    submitter_id: int
    nacc_id: int
    index: int
    title: Optional[str] = Field(None, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    title_en: Optional[str] = Field(None, max_length=100)
    first_name_en: Optional[str] = Field(None, max_length=100)
    last_name_en: Optional[str] = Field(None, max_length=100)
    latest_submitted_date: Optional[date] = None


class SubmitterPosition(BaseModel):
    """Model for submitter_position - positions held by submitter."""
    submitter_id: int
    nacc_id: int
    position_period_type_id: int = Field(..., description="1=Current, 2=Concurrent, 3=Past")
    index: int
    position: str = Field(..., max_length=500, description="Position title")
    position_category_type_id: Optional[str] = Field(None, max_length=200)
    workplace: Optional[str] = Field(None, max_length=500)
    workplace_location: Optional[str] = Field(None, max_length=500)
    date_acquiring_type_id: Optional[int] = Field(None, description="1=Exact, 2=Approx, 3=NotSpec, 4=None")
    start_date: Optional[str] = Field(None, max_length=10)
    start_month: Optional[str] = Field(None, max_length=10)
    start_year: Optional[str] = Field(None, max_length=10)
    date_ending_type_id: Optional[int] = None
    end_date: Optional[str] = Field(None, max_length=10)
    end_month: Optional[str] = Field(None, max_length=10)
    end_year: Optional[str] = Field(None, max_length=10)
    note: Optional[str] = Field(None, max_length=500)
    latest_submitted_date: Optional[date] = None
