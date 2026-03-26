from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional
import traceback
import logging

from end_points.get_simulator.operations.get_simulator_opts import (
    getSimulatorList,
    addSimulator,
    getSimulator,
    getSimTrading,
    deleteSimulator,
    runSimulator,
    getParamsForSim
)
from end_points.get_simulator.operations.simulator_config_ops import (
    get_simulator_config,
    update_simulator_config
)
from end_points.get_simulator.simulator_schema import SimulatorCreateArgs
from end_points.get_simulator.simulator_config_schema import SimulatorConfigCreate
from end_points.common.utils.db import get_db


router = APIRouter(
    prefix="/get_simulator",
    tags=["simulator"]
)


@router.get("/simulator_list", response_model=Dict[str, Any])
async def get_simulator_list(
    status: Optional[str] = Query(default=None),
    rule_type: Optional[str] = Query(default=None),
    db=Depends(get_db)
):
    """
    Get simulator list

    Args:
        status: Simulator status filter
        rule_type: Rule type filter

    Returns:
        Dictionary with code and simulator list
    """
    try:
        args = {
            'status': status,
            'rule_type': rule_type
        }
        rst = getSimulatorList(db, args)
        return rst
    except Exception as e:
        err = traceback.format_exc()
        logging.error(f"Error in get_simulator_list: {err}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulator_list", response_model=Dict[str, Any])
async def create_simulator(
    simulator_data: SimulatorCreateArgs,
    db=Depends(get_db)
):
    """
    Create a new simulator

    Args:
        simulator_data: Simulator creation data

    Returns:
        Dictionary with code and simulator ID
    """
    try:
        args = simulator_data.model_dump()
        rst = addSimulator(db, args)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/simulator/{sim_id}", response_model=Dict[str, Any])
async def get_simulator(
    sim_id: int,
    db=Depends(get_db)
):
    """
    Get simulator log data

    Args:
        sim_id: Simulator ID

    Returns:
        Dictionary with code and log data
    """
    try:
        args = {}
        rst = getSimulator(db, sim_id, args)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/simulator/{sim_id}/run", response_model=Dict[str, Any])
async def run_simulator(
    sim_id: int,
    bind_key: Optional[str] = Query(default=None),
    db=Depends(get_db)
):
    """
    Run simulator

    Args:
        sim_id: Simulator ID
        bind_key: Database bind key

    Returns:
        Dictionary with code and result
    """
    try:
        args = {'bind_key': bind_key}
        rst = runSimulator(db, args, sim_id)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/simulator/{sim_id}", response_model=Dict[str, Any])
async def delete_simulator(
    sim_id: int,
    db=Depends(get_db)
):
    """
    Delete simulator

    Args:
        sim_id: Simulator ID

    Returns:
        Dictionary with code and result
    """
    try:
        rst = deleteSimulator(db, sim_id)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/simulator/{sim_id}/trading", response_model=Dict[str, Any])
async def get_simulator_trading(
    sim_id: int,
    page: int = Query(default=1),
    page_size: int = Query(default=100),
    stock: Optional[str] = Query(default=None),
    trading_type: Optional[str] = Query(default=None),
    db=Depends(get_db)
):
    """
    Get simulator trading records

    Args:
        sim_id: Simulator ID
        page: Page number
        page_size: Page size
        stock: Stock code filter
        trading_type: Trading type filter

    Returns:
        Dictionary with code and trading records
    """
    try:
        args = {
            'page': page,
            'page_size': page_size,
            'stock': stock,
            'trading_type': trading_type
        }
        rst = getSimTrading(db, sim_id, args)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/simulator/{sim_id}/params", response_model=Dict[str, Any])
async def get_simulator_params(
    sim_id: int,
    db=Depends(get_db)
):
    """
    Get simulator parameters and earning info

    Args:
        sim_id: Simulator ID

    Returns:
        Dictionary with code and parameters
    """
    try:
        args = {}
        rst = getParamsForSim(db, sim_id, args)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config", response_model=Dict[str, Any])
async def get_config(db=Depends(get_db)):
    """
    Get global simulator configuration

    Returns:
        Dictionary with code and configuration
    """
    try:
        rst = get_simulator_config(db)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config", response_model=Dict[str, Any])
async def update_config(
    config_data: SimulatorConfigCreate,
    db=Depends(get_db)
):
    """
    Update global simulator configuration

    Args:
        config_data: Configuration data to update

    Returns:
        Dictionary with code and updated configuration
    """
    try:
        rst = update_simulator_config(
            db,
            config_data.profit_threshold,
            config_data.stop_loss,
            config_data.max_holding_days
        )
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

