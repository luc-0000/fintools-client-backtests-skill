from pydantic import BaseModel, ConfigDict


class SimulatorConfigCreate(BaseModel):
    """Simulator config creation/update parameters"""
    profit_threshold: float = 0
    stop_loss: float = 5
    max_holding_days: int = 5


class SimulatorConfigResponse(BaseModel):
    """Simulator config response"""
    id: int
    profit_threshold: float
    stop_loss: float
    max_holding_days: int
    updated_at: str | None = None

    model_config = ConfigDict(from_attributes=True)
