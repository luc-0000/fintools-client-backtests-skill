from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class PoolSchema(BaseModel):
    """Pool schema for FastAPI"""
    id: Optional[int] = None
    name: str
    stocks: Optional[int] = None
    latest_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PoolCreateRequest(BaseModel):
    """Request schema for creating a pool"""
    name: str = Field(..., description="Pool name")


class PoolUpdateRequest(BaseModel):
    """Request schema for updating a pool"""
    name: str = Field(..., description="Pool name")


class PoolResponse(BaseModel):
    """Response schema for pool operations"""
    code: str
    data: Optional[dict] = None
    message: Optional[str] = None


class PoolListResponse(BaseModel):
    """Response schema for pool list"""
    code: str
    data: dict
