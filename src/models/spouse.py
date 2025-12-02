"""Spouse information models."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class SpouseInfo(BaseModel):
    """Model for spouse_info - spouse information."""
    spouse_id: int
    submitter_id: int
    nacc_id: int
    title: Optional[str] = Field(None, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)
    status: Optional[str] = Field(None, max_length=100, description="Marriage status")
    status_date: Optional[str] = Field(None, max_length=10)
    status_month: Optional[str] = Field(None, max_length=10)
    status_year: Optional[str] = Field(None, max_length=10)
    latest_submitted_date: Optional[date] = None


class SpouseOldName(BaseModel):
    """Model for spouse_old_name - previous names of spouse."""
    spouse_id: int
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


class SpousePosition(BaseModel):
    """Model for spouse_position - positions held by spouse."""
    spouse_id: int
    submitter_id: int
    nacc_id: int
    position_period_type_id: int
    index: int
    position: Optional[str] = Field(None, max_length=500)
    position_category_type_id: Optional[str] = Field(None, max_length=200)
    workplace: Optional[str] = Field(None, max_length=500)
    workplace_location: Optional[str] = Field(None, max_length=500)
    date_acquiring_type_id: Optional[int] = None
    start_date: Optional[str] = Field(None, max_length=10)
    start_month: Optional[str] = Field(None, max_length=10)
    start_year: Optional[str] = Field(None, max_length=10)
    date_ending_type_id: Optional[int] = None
    end_date: Optional[str] = Field(None, max_length=10)
    end_month: Optional[str] = Field(None, max_length=10)
    end_year: Optional[str] = Field(None, max_length=10)
    note: Optional[str] = Field(None, max_length=500)
    latest_submitted_date: Optional[date] = None
