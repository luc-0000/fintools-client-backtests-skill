from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
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


class RulePoolArgs(BaseModel):
    """Rule pool arguments"""
    pool_id: int = Field(..., description="Pool ID")
    rule_id: Optional[int] = None


class RulePoolsArgs(BaseModel):
    """Rule multiple pools arguments"""
    pool_ids: List[int] = Field(..., description="List of pool IDs")
    rule_id: Optional[int] = None


class RuleCreateArgs(BaseModel):
    """Rule creation arguments"""
    name: str = Field(..., description="Rule name", min_length=1, max_length=255)
    type: str = Field(None, description="Rule type (tech, mclose, mopen, rl, combo, agent)")
    description: Optional[str] = Field(None, description="Rule description", min_length=1, max_length=255)
    info: Optional[str] = Field(None, description="Rule info in JSON format")
    agent_id: Optional[str] = Field(None, description="Remote agent identifier")
    threshould: Optional[float] = Field(None, description="Threshold value")
    split: Optional[int] = Field(None, description="split value")
    model_location: Optional[str] = Field(None, description="Model file location")
    scaler_location: Optional[str] = Field(None, description="Scaler file location")
    encoder_location: Optional[str] = Field(None, description="Encoder file location")

    @field_validator("description", mode="before")
    @classmethod
    def normalize_blank_description(cls, value):
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return value


# Model schemas
class RuleSchema(BaseModel):
    """Rule model schema"""
    id: Optional[int] = None
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    info: Optional[str] = None
    agent_id: Optional[str] = None
    avg_return: Optional[float] = None
    threshould: Optional[float] = None
    split: Optional[int] = None
    model_location: Optional[str] = None
    scaler_location: Optional[str] = None
    encoder_location: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EarnSchema(BaseModel):
    """Earn schema"""
    earn: Optional[float] = None
    avg_earn: Optional[float] = None
    earning_rate: Optional[float] = None
    trading_times: Optional[int] = None
    status: Optional[str] = None
    indicating_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
