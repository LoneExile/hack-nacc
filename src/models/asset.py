"""Asset information models."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class Asset(BaseModel):
    """Model for asset - all types of assets."""
    asset_id: int
    submitter_id: int
    nacc_id: int
    index: int
    asset_type_id: int = Field(..., description="Asset type ID from asset_type enum")
    asset_type_other: Optional[str] = Field(None, max_length=200, description="For 'other' types")
    asset_name: Optional[str] = Field(None, max_length=500)
    date_acquiring_type_id: Optional[int] = Field(None, description="1=Exact, 2=Approx, 3=NotSpec, 4=None")
    acquiring_date: Optional[str] = Field(None, max_length=10)
    acquiring_month: Optional[str] = Field(None, max_length=10)
    acquiring_year: Optional[str] = Field(None, max_length=10)
    date_ending_type_id: Optional[int] = None
    ending_date: Optional[str] = Field(None, max_length=10)
    ending_month: Optional[str] = Field(None, max_length=10)
    ending_year: Optional[str] = Field(None, max_length=10)
    asset_acquisition_type_id: Optional[int] = Field(None, description="How acquired")
    valuation: Optional[float] = Field(None, ge=0)
    owner_by_submitter: bool = False
    owner_by_spouse: bool = False
    owner_by_child: bool = False
    latest_submitted_date: Optional[date] = None


class AssetLandInfo(BaseModel):
    """Model for asset_land_info - land-specific details."""
    asset_id: int
    submitter_id: int
    nacc_id: int
    land_doc_number: Optional[str] = Field(None, max_length=100, description="Document number")
    rai: Optional[float] = Field(None, ge=0, description="Area in rai")
    ngan: Optional[float] = Field(None, ge=0, description="Area in ngan")
    sq_wa: Optional[float] = Field(None, ge=0, description="Area in square wa")
    sub_district: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    latest_submitted_date: Optional[date] = None


class AssetBuildingInfo(BaseModel):
    """Model for asset_building_info - building-specific details."""
    asset_id: int
    submitter_id: int
    nacc_id: int
    building_doc_number: Optional[str] = Field(None, max_length=100)
    sub_district: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    latest_submitted_date: Optional[date] = None


class AssetVehicleInfo(BaseModel):
    """Model for asset_vehicle_info - vehicle-specific details."""
    asset_id: int
    submitter_id: int
    nacc_id: int
    registration_number: Optional[str] = Field(None, max_length=50)
    vehicle_brand: Optional[str] = Field(None, max_length=100)
    vehicle_model: Optional[str] = Field(None, max_length=100)
    registration_province: Optional[str] = Field(None, max_length=100)
    latest_submitted_date: Optional[date] = None


class AssetOtherInfo(BaseModel):
    """Model for asset_other_asset_info - other asset details."""
    asset_id: int
    submitter_id: int
    nacc_id: int
    count: Optional[int] = Field(None, ge=0)
    unit: Optional[str] = Field(None, max_length=50)
    latest_submitted_date: Optional[date] = None
