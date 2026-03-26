from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

from end_points.common.const.consts import DataBase


# Query parameter schemas
class StockListArgs(BaseModel):
    """Stock list query parameters"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=100, ge=1, le=1000)
    pool_id: Optional[int] = None
    stock_code: Optional[str] = None
    stock_name: Optional[str] = None


class StockArgs(BaseModel):
    """Stock query parameters"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=100, ge=1, le=1000)
    bind_key: str = Field(default=DataBase.stocks)


class AddStockArgs(BaseModel):
    """Add stock to pool request"""
    code: str = Field(..., description="Stock code")
    pool_id: int = Field(..., description="Pool ID")


class RemoveStockArgs(BaseModel):
    """Remove stock from pool request"""
    pool_id: int = Field(..., description="Pool ID")


# Model schemas
class StockSchema(BaseModel):
    """Stock model schema"""
    code: str
    name: str
    se: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PoolStockSchema(BaseModel):
    """Pool stock relationship schema"""
    pool_id: int
    stock_code: str

    model_config = ConfigDict(from_attributes=True)


class StockDetailSchema(BaseModel):
    """Stock detail/market data schema"""
    date: datetime
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None
    turnover: Optional[float] = None
    turnover_rate: Optional[float] = None
    shake_rate: Optional[float] = None
    change_rate: Optional[float] = None
    change_amount: Optional[float] = None
    k: Optional[float] = None
    d: Optional[float] = None
    j: Optional[float] = None
    diff: Optional[float] = None
    dea: Optional[float] = None
    macd: Optional[float] = None
    ema12: Optional[float] = None
    ema26: Optional[float] = None
    ma3: Optional[float] = None
    ma5: Optional[float] = None
    ma10: Optional[float] = None
    ma15: Optional[float] = None
    ma20: Optional[float] = None
    ma30: Optional[float] = None
    ma60: Optional[float] = None
    ma120: Optional[float] = None
    ma200: Optional[float] = None
    ma250: Optional[float] = None
    boll_u: Optional[float] = None
    boll_d: Optional[float] = None
    boll_m: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class RuleSchema(BaseModel):
    """Rule schema for FastAPI"""
    id: Optional[int] = None
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    info: Optional[str] = None
    avg_return: Optional[float] = None
    threshould: Optional[float] = None
    model_location: Optional[str] = None
    scaler_location: Optional[str] = None
    encoder_location: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)