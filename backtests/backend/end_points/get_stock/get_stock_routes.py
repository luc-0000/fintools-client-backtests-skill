from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional

from end_points.get_stock.operations.get_stock_opts import (
    getStockList,
    addStockToPool,
    removeStockFromPool,
    getStockDetail,
    getStockRules
)
from end_points.get_stock.stock_schema import (
    StockListArgs,
    StockArgs,
    AddStockArgs,
    RemoveStockArgs
)
from end_points.common.const.consts import DataBase
from end_points.common.utils.db import get_db


router = APIRouter(
    prefix="/get_stock",
    tags=["stock"]
)


@router.get("/stock_list", response_model=Dict[str, Any])
async def get_stock_list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=1000),
    pool_id: Optional[int] = Query(default=None),
    stock_code: Optional[str] = Query(default=None),
    stock_name: Optional[str] = Query(default=None),
    db=Depends(get_db)
):
    """
    Get list of stocks with optional filters

    Args:
        page: Page number (default: 1)
        page_size: Number of items per page (default: 100)
        pool_id: Filter by pool ID (optional)
        stock_code: Filter by stock code (optional)
        stock_name: Filter by stock name (optional)

    Returns:
        Dictionary with code, data containing total and items
    """
    try:
        args = {
            'page': page,
            'page_size': page_size,
            'pool_id': pool_id,
            'stock_code': stock_code,
            'stock_name': stock_name
        }
        rst = getStockList(db, args)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stock_list", response_model=Dict[str, Any])
async def add_stock_to_pool(
    stock_data: AddStockArgs,
    db=Depends(get_db)
):
    """
    Add a stock to a pool

    Args:
        stock_data: Stock data with code and pool_id

    Returns:
        Dictionary with code and result
    """
    try:
        user_id = None  # TODO: Get from authentication
        args = stock_data.model_dump()
        rst = addStockToPool(db, args, user_id)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{stock_code}", response_model=Dict[str, Any])
async def get_stock_detail(
    stock_code: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=50000),
    bind_key: str = Query(default=DataBase.stocks),
    db=Depends(get_db)
):
    """
    Get stock detail/market data by stock code

    Args:
        stock_code: Stock code
        page: Page number (default: 1)
        page_size: Number of items per page (default: 100)
        bind_key: Database bind key (default: stocks)

    Returns:
        Dictionary with code and stock detail data
    """
    try:
        args = {
            'page': page,
            'page_size': page_size,
            'bind_key': bind_key
        }
        rst = getStockDetail(db, stock_code, args)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/stock/{stock_code}", response_model=Dict[str, Any])
async def remove_stock_from_pool(
    stock_code: str,
    remove_data: RemoveStockArgs,
    db=Depends(get_db)
):
    """
    Remove a stock from a pool

    Args:
        stock_code: Stock code
        remove_data: Data with pool_id

    Returns:
        Dictionary with code and result
    """
    try:
        args = remove_data.model_dump()
        rst = removeStockFromPool(db, stock_code, args)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{stock_code}/rules", response_model=Dict[str, Any])
async def get_stock_rules(
    stock_code: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=1000),
    bind_key: str = Query(default=DataBase.stocks),
    db=Depends(get_db)
):
    """
    Get rules associated with a stock

    Args:
        stock_code: Stock code
        page: Page number (default: 1)
        page_size: Number of items per page (default: 100)
        bind_key: Database bind key (default: stocks)

    Returns:
        Dictionary with code and stock rules data
    """
    try:
        args = {
            'page': page,
            'page_size': page_size,
            'bind_key': bind_key
        }
        rst = getStockRules(db, stock_code, args)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))