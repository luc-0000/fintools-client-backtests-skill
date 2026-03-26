from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from end_points.get_pool.operations.get_pool_opts import (
    getPoolList,
    createPool,
    getPool,
    deletePool,
    updatePool
)
from end_points.get_pool.pool_schema import (
    PoolCreateRequest,
    PoolUpdateRequest,
    PoolResponse,
    PoolListResponse
)
from end_points.common.utils.db import get_db


router = APIRouter(
    prefix="/get_pool",
    tags=["pool"]
)


@router.get("/pool_list", response_model=Dict[str, Any])
async def get_pool_list(db=Depends(get_db)):
    """
    Get list of all pools

    Returns:
        Dictionary with code, data containing total and items
    """
    try:
        rst = getPoolList(db)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pool_list", response_model=Dict[str, Any])
async def create_pool(
    pool_data: PoolCreateRequest,
    db=Depends(get_db)
):
    """
    Create a new pool

    Args:
        pool_data: Pool creation data with name

    Returns:
        Dictionary with code and created pool data
    """
    try:
        # Note: user_id is hardcoded as None for this example
        # In production, you should get this from authentication
        user_id = None
        args = pool_data.model_dump()
        rst = createPool(db, args, user_id)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pool/{pool_id}", response_model=Dict[str, Any])
async def get_pool_by_id(
    pool_id: int,
    db=Depends(get_db)
):
    """
    Get a specific pool by ID

    Args:
        pool_id: The pool ID

    Returns:
        Dictionary with code and pool data
    """
    try:
        rst = getPool(db, pool_id)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/pool/{pool_id}", response_model=Dict[str, Any])
async def delete_pool_by_id(
    pool_id: int,
    db=Depends(get_db)
):
    """
    Delete a specific pool by ID

    Args:
        pool_id: The pool ID to delete

    Returns:
        Dictionary with code and deleted pool ID
    """
    try:
        rst = deletePool(db, pool_id)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/pool/{pool_id}", response_model=Dict[str, Any])
async def update_pool_by_id(
    pool_id: int,
    pool_data: PoolUpdateRequest,
    db=Depends(get_db)
):
    """
    Update a specific pool by ID

    Args:
        pool_id: The pool ID to update
        pool_data: Pool update data with name

    Returns:
        Dictionary with code and updated pool ID
    """
    try:
        # Note: user_id is hardcoded as None for this example
        # In production, you should get this from authentication
        user_id = None
        args = pool_data.model_dump()
        rst = updatePool(db, args, pool_id, user_id)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))