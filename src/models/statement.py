"""Financial statement models."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class Statement(BaseModel):
    """Model for statement - financial summary."""
    nacc_id: int
    statement_type_id: int = Field(..., description="1=Cash, 2=Deposits, 3=Loans, 4=Assets, 5=Liabilities")
    valuation_submitter: Optional[float] = Field(None, ge=0)
    submitter_id: int
    valuation_spouse: Optional[float] = Field(None, ge=0)
    valuation_child: Optional[float] = Field(None, ge=0)
    latest_submitted_date: Optional[date] = None


class StatementDetail(BaseModel):
    """Model for statement_detail - detailed financial breakdown."""
    statement_detail_id: int
    submitter_id: int
    nacc_id: int
    statement_type_id: int
    statement_detail_type_id: int
    index: int
    detail_name: Optional[str] = Field(None, max_length=500)
    account_number: Optional[str] = Field(None, max_length=100)
    bank_name: Optional[str] = Field(None, max_length=200)
    branch: Optional[str] = Field(None, max_length=200)
    date_acquiring_type_id: Optional[int] = None
    acquiring_date: Optional[str] = Field(None, max_length=10)
    acquiring_month: Optional[str] = Field(None, max_length=10)
    acquiring_year: Optional[str] = Field(None, max_length=10)
    date_ending_type_id: Optional[int] = None
    ending_date: Optional[str] = Field(None, max_length=10)
    ending_month: Optional[str] = Field(None, max_length=10)
    ending_year: Optional[str] = Field(None, max_length=10)
    valuation_submitter: Optional[float] = Field(None, ge=0)
    valuation_spouse: Optional[float] = Field(None, ge=0)
    valuation_child: Optional[float] = Field(None, ge=0)
    note: Optional[str] = Field(None, max_length=1000)
    latest_submitted_date: Optional[date] = None
