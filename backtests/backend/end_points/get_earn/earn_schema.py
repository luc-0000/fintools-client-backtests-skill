from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

from end_points.common.const.consts import DataBase


# Query parameter schemas
class EarnArgs(BaseModel):
    """Earn query parameters"""
    bind_key: str = Field(default=DataBase.stocks)
    rule_id: Optional[int] = None
    pool_id: Optional[int] = None
    stock_code: Optional[str] = None
    stock_id: Optional[int] = None
    status: Optional[str] = None
    rule_type: Optional[str] = None


# Model schemas
class EarnSchema(BaseModel):
    """Earn model schema"""
    earn: Optional[float] = None
    avg_earn: Optional[float] = None
    earning_rate: Optional[float] = None
    trading_times: Optional[int] = None
    status: Optional[str] = None
    indicating_date: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class StockRuleEarnSchema(BaseModel):
    """Stock rule earn schema"""
    stock_code: str
    stock_name: Optional[str] = None
    rule_id: Optional[int] = None
    rule_name: Optional[str] = None
    rule_type: Optional[str] = None
    earn: Optional[float] = None
    avg_earn: Optional[float] = None
    earning_rate: Optional[float] = None
    trading_times: Optional[int] = None
    status: Optional[str] = None
    indicating_date: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)