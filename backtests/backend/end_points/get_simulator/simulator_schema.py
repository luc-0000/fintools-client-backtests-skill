from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date


# Query parameter schemas
class SimArgs(BaseModel):
    """Simulator query parameters"""
    status: Optional[str] = None
    rule_type: Optional[str] = None
    page: int = Field(default=1)
    page_size: int = Field(default=100)
    stock: Optional[str] = None
    trading_type: Optional[str] = None


class SimulatorCreateArgs(BaseModel):
    """Simulator creation parameters"""
    stock_code: Optional[str] = None
    rule_id: int
    init_money: Optional[float] = None
    start_date: date


# Model schemas
class SimulatorSchema(BaseModel):
    """Simulator model schema"""
    id: Optional[int] = None
    stock_code: Optional[str] = None
    stock_name: Optional[str] = None
    rule_id: Optional[int] = None
    rule_name: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[date] = None
    init_money: Optional[float] = None
    cum_earn: Optional[float] = None
    avg_earn: Optional[float] = None
    earning_rate: Optional[float] = None
    trading_times: Optional[int] = None
    current_money: Optional[float] = None
    current_shares: Optional[str] = None
    indicating_date: Optional[datetime] = None
    earning_info: Optional[str] = None
    updated_at: Optional[datetime] = None
    type: Optional[str] = None

    # Additional computed fields
    annual_earn: Optional[float] = None
    first_trade_date: Optional[str] = None
    max_drawback: Optional[float] = None
    sharpe: Optional[float] = None
    r_cum_earn_after: Optional[float] = None
    r_earn_rate_after: Optional[float] = None
    r_avg_earn_after: Optional[float] = None
    r_trading_times: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class SimTradingSchema(BaseModel):
    """Simulator trading schema"""
    id: int
    sim_id: int
    stock: Optional[str] = None
    stock_name: Optional[str] = None
    trading_date: datetime
    trading_type: Optional[str] = None
    trading_amount: Optional[float] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)