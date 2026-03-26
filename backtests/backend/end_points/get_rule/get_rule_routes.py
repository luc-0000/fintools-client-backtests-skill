from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional
import json
import logging

from end_points.get_rule.operations.get_rule_opts import (
    getRuleList,
    deleteRule,
    editRule,
    getPoolListForRule,
    addPoolToRule,
    removePoolFromRule,
    getStockListForRule,
    getParamsForRule,
    addRule,
    runRuleAgent,
    getAgentTradingList,
    getRuleStocksIndicating,
    runAgentForStock
)
from end_points.get_rule.operations.agent_streaming import stream_agent_execution, stream_single_stock_execution
from end_points.get_rule.operations.execution_manager import execution_manager

logger = logging.getLogger(__name__)
from end_points.get_rule.rule_schema import (
    # RuleArgs,
    EarnArgs,
    RuleSchema,
    RulePoolArgs,
    RulePoolsArgs,
    RuleCreateArgs
)
from end_points.common.const.consts import DataBase
from end_points.common.utils.db import get_db


router = APIRouter(
    prefix="/get_rule",
    tags=["rule"]
)


@router.get("/rule_list", response_model=Dict[str, Any])
async def get_rule_list(
    bind_key: str = Query(default=DataBase.stocks),
    rule_id: Optional[int] = Query(default=None),
    pool_id: Optional[int] = Query(default=None),
    stock_code: Optional[str] = Query(default=None),
    stock_id: Optional[int] = Query(default=None),
    status: Optional[str] = Query(default=None),
    rule_type: Optional[str] = Query(default=None),
    db=Depends(get_db)
):
    """
    Get list of rules

    Returns:
        Dictionary with code and rules data
    """
    try:
        args = {
            'bind_key': bind_key,
            'rule_id': rule_id,
            'pool_id': pool_id,
            'stock_code': stock_code,
            'stock_id': stock_id,
            'status': status,
            'rule_type': rule_type
        }
        rst = getRuleList(db, args)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rule_list", response_model=Dict[str, Any])
async def create_rule(
    rule_data: RuleCreateArgs,
    db=Depends(get_db)
):
    """
    Create a new rule

    Args:
        rule_data: Rule creation data

    Returns:
        Dictionary with code and created rule data
    """
    try:
        args = rule_data.model_dump()
        rst = addRule(db, args)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rule/{rule_id}", response_model=Dict[str, Any])
async def get_rule_by_id(
    rule_id: int,
    db=Depends(get_db)
):
    """
    Get a specific rule by ID

    Args:
        rule_id: Rule ID

    Returns:
        Dictionary with code and rule data
    """
    try:
        # Note: This endpoint might need implementation in get_rule_opts.py
        # For now, using getRuleList with rule_id filter
        args = {'rule_id': rule_id}
        rst = getRuleList(db, args)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rule/{rule_id}", response_model=Dict[str, Any])
async def delete_rule_by_id(
    rule_id: int,
    db=Depends(get_db)
):
    """
    Delete a rule by ID

    Args:
        rule_id: Rule ID to delete

    Returns:
        Dictionary with code and result
    """
    try:
        rst = deleteRule(db, rule_id)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rule/{rule_id}", response_model=Dict[str, Any])
async def update_rule(
    rule_id: int,
    rule_data: RuleSchema,
    db=Depends(get_db)
):
    """
    Update a rule

    Args:
        rule_id: Rule ID
        rule_data: Rule update data

    Returns:
        Dictionary with code and result
    """
    try:
        args = rule_data.model_dump(exclude_none=True)
        rst = editRule(db, args, rule_id)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rule/{rule_id}/pools", response_model=Dict[str, Any])
async def get_pools_for_rule(
    rule_id: str,
    bind_key: str = Query(default=DataBase.stocks),
    pool_id: Optional[int] = Query(default=None),
    stock_code: Optional[str] = Query(default=None),
    db=Depends(get_db)
):
    """
    Get pools associated with a rule

    Args:
        rule_id: Rule ID (or "NaN" for all rules)
        bind_key: Database bind key
        pool_id: Optional pool ID filter
        stock_code: Optional stock code filter

    Returns:
        Dictionary with code and pools data
    """
    try:
        # Convert rule_id to int, treat "NaN" or invalid values as 0 (all rules)
        try:
            rule_id_int = int(rule_id)
        except (ValueError, TypeError):
            rule_id_int = 0

        args = {
            'bind_key': bind_key,
            'pool_id': pool_id,
            'stock_code': stock_code
        }
        rst = getPoolListForRule(db, rule_id_int, args)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rule/{rule_id}/pools", response_model=Dict[str, Any])
async def add_pools_to_rule(
    rule_id: int,
    pool_data: RulePoolsArgs,
    db=Depends(get_db)
):
    """
    Add pools to a rule

    Args:
        rule_id: Rule ID
        pool_data: Pool IDs to add

    Returns:
        Dictionary with code and result
    """
    try:
        args = pool_data.model_dump()
        rst = addPoolToRule(db, rule_id, args)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rule/{rule_id}/pools", response_model=Dict[str, Any])
async def remove_pool_from_rule(
    rule_id: int,
    pool_data: RulePoolArgs,
    db=Depends(get_db)
):
    """
    Remove a pool from a rule

    Args:
        rule_id: Rule ID
        pool_data: Pool ID to remove

    Returns:
        Dictionary with code and result
    """
    try:
        args = pool_data.model_dump()
        rst = removePoolFromRule(db, rule_id, args)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rule/{rule_id}/stocks", response_model=Dict[str, Any])
async def get_stocks_for_rule(
    rule_id: str,
    bind_key: str = Query(default=DataBase.stocks),
    pool_id: Optional[int] = Query(default=None),
    stock_code: Optional[str] = Query(default=None),
    db=Depends(get_db)
):
    """
    Get stocks associated with a rule

    Args:
        rule_id: Rule ID (or "NaN" for all rules)
        bind_key: Database bind key
        pool_id: Optional pool ID filter
        stock_code: Optional stock code filter

    Returns:
        Dictionary with code and stocks data
    """
    try:
        # Convert rule_id to int, treat "NaN" or invalid values as 0 (all rules)
        try:
            rule_id_int = int(rule_id)
        except (ValueError, TypeError):
            rule_id_int = 0

        args = {
            'bind_key': bind_key,
            'pool_id': pool_id,
            'stock_code': stock_code
        }
        rst = getStockListForRule(db, rule_id_int, args)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rule/{rule_id}/params", response_model=Dict[str, Any])
async def get_params_for_rule(
    rule_id: int,
    bind_key: str = Query(default=DataBase.stocks),
    pool_id: Optional[int] = Query(default=None),
    db=Depends(get_db)
):
    """
    Get parameters for a rule

    Args:
        rule_id: Rule ID
        bind_key: Database bind key
        pool_id: Optional pool ID filter

    Returns:
        Dictionary with code and params data
    """
    try:
        args = {
            'bind_key': bind_key,
            'pool_id': pool_id
        }
        rst = getParamsForRule(db, rule_id, args)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rule/run/{rule_id}", response_model=Dict[str, Any])
async def run_rule_agent(
    rule_id: int,
    db=Depends(get_db)
):
    """
    Run an agent-type rule

    Args:
        rule_id: Rule ID

    Returns:
        Dictionary with code and result
    """
    try:
        rst = runRuleAgent(db, rule_id)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rule/{rule_id}/trading", response_model=Dict[str, Any])
async def get_rule_trading(
    rule_id: int,
    page: int = Query(default=1),
    page_size: int = Query(default=50),
    db=Depends(get_db)
):
    """
    Get trading records for a rule

    Args:
        rule_id: Rule ID
        page: Page number
        page_size: Page size

    Returns:
        Dictionary with code and trading data
    """
    try:
        rst = getAgentTradingList(db, rule_id, page, page_size)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rule/{rule_id}/stocks_indicating", response_model=Dict[str, Any])
async def get_rule_stocks_indicating(
    rule_id: str,
    db=Depends(get_db)
):
    """
    Get all stocks for a rule with their today's indicating status

    Args:
        rule_id: Rule ID

    Returns:
        Dictionary with stocks and their indicating status for today
    """
    try:
        rule_id_int = int(rule_id)
        rst = getRuleStocksIndicating(db, rule_id_int)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rule/{rule_id}/run_stock", response_model=Dict[str, Any])
async def run_agent_for_stock(
    rule_id: str,
    stock_code: str = Query(..., description="Stock code"),
    db=Depends(get_db)
):
    """
    Run agent for a single stock

    Args:
        rule_id: Rule ID
        stock_code: Stock code to run

    Returns:
        Dictionary with result of the agent run
    """
    try:
        rule_id_int = int(rule_id)
        rst = runAgentForStock(db, rule_id_int, stock_code)
        return rst
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rule/{rule_id}/start")
async def start_rule_execution_endpoint(
    rule_id: int,
    db=Depends(get_db)
):
    """
    Start agent execution for all stocks in the rule's pools.

    Returns:
        execution_id to use with /stream endpoint
    """
    logger.info(f"=== Starting execution for rule_id={rule_id} ===")

    # Create execution
    execution = execution_manager.create_execution(rule_id, stock_code=None)

    # Start execution in background
    import asyncio
    import threading

    def run_in_background():
        async def _run():
            await execution_manager.execute_and_capture(
                execution,
                stream_agent_execution,
                db,
                rule_id
            )
        asyncio.run(_run())

    thread = threading.Thread(target=run_in_background, daemon=True)
    thread.start()

    return {
        'code': 'SUCCESS',
        'execution_id': execution.execution_id,
        'rule_id': rule_id
    }


@router.post("/rule/{rule_id}/stock/{stock_code}/start")
async def start_single_stock_execution_endpoint(
    rule_id: int,
    stock_code: str,
    db=Depends(get_db)
):
    """
    Start agent execution for a single stock.

    Returns:
        execution_id to use with /stream endpoint
    """
    logger.info(f"=== Starting execution for rule_id={rule_id}, stock_code={stock_code} ===")

    # Create execution
    execution = execution_manager.create_execution(rule_id, stock_code=stock_code)

    # Start execution in background
    import asyncio
    import threading

    def run_in_background():
        async def _run():
            await execution_manager.execute_and_capture(
                execution,
                stream_single_stock_execution,
                db,
                rule_id,
                stock_code
            )
        asyncio.run(_run())

    thread = threading.Thread(target=run_in_background, daemon=True)
    thread.start()

    return {
        'code': 'SUCCESS',
        'execution_id': execution.execution_id,
        'rule_id': rule_id,
        'stock_code': stock_code
    }


@router.get("/rule/{rule_id}/stream")
async def stream_agent_logs(
    rule_id: int,
    execution_id: str = Query(..., description="Execution ID from /start endpoint"),
    db=Depends(get_db)
):
    """
    Stream agent execution logs via Server-Sent Events (SSE)

    IMPORTANT: This endpoint ONLY streams logs, does NOT trigger execution.
    Call POST /rule/{rule_id}/start first to get an execution_id.

    Args:
        rule_id: Rule ID
        execution_id: Execution ID from start endpoint

    Returns:
        StreamingResponse with SSE events
    """
    logger.info(f"=== SSE stream requested for rule_id={rule_id}, execution_id={execution_id} ===")

    async def event_generator():
        """Generate SSE events from execution logs"""
        try:
            logger.info(f"=== Starting event generator for execution_id={execution_id} ===")
            async for log_entry in execution_manager.stream_execution_logs(execution_id):
                # Convert to SSE format
                data = json.dumps(log_entry, ensure_ascii=False)
                logger.debug(f"Yielding SSE event: {log_entry.get('type', 'unknown')}")
                yield f"data: {data}\n\n"
        except Exception as e:
            logger.error(f"Error in event generator: {e}")
            error_data = json.dumps({
                "type": "error",
                "message": f"Stream error: {str(e)}"
            }, ensure_ascii=False)
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/rule/{rule_id}/stock/{stock_code}/stream")
async def stream_single_stock_logs(
    rule_id: int,
    stock_code: str,
    execution_id: str = Query(..., description="Execution ID from /start endpoint"),
    db=Depends(get_db)
):
    """
    Stream agent execution logs for a single stock via Server-Sent Events (SSE)

    IMPORTANT: This endpoint ONLY streams logs, does NOT trigger execution.
    Call POST /rule/{rule_id}/stock/{stock_code}/start first to get an execution_id.

    Args:
        rule_id: Rule ID
        stock_code: Stock code
        execution_id: Execution ID from start endpoint

    Returns:
        StreamingResponse with SSE events
    """
    logger.info(f"=== SSE stream requested for rule_id={rule_id}, stock_code={stock_code}, execution_id={execution_id} ===")

    async def event_generator():
        """Generate SSE events for single stock execution"""
        try:
            logger.info(f"=== Starting event generator for execution_id={execution_id} ===")
            async for log_entry in execution_manager.stream_execution_logs(execution_id):
                data = json.dumps(log_entry, ensure_ascii=False)
                logger.debug(f"Yielding SSE event: {log_entry.get('type', 'unknown')}")
                yield f"data: {data}\n\n"
        except Exception as e:
            logger.error(f"Error in event generator: {e}")
            error_data = json.dumps({
                "type": "error",
                "message": f"Stream error: {str(e)}"
            }, ensure_ascii=False)
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

