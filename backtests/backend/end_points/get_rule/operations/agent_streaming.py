import logging
from datetime import datetime
from typing import AsyncGenerator

from db.models import PoolStock, Rule, RulePool
from end_points.common.const.consts import Trade
from end_points.get_rule.operations.agent_utils import update_rule_trading
from end_points.get_rule.operations.skill_agent_adapter import (
    execute_trading_agent_via_skill,
    extract_trading_action,
    stream_trading_agent_via_skill,
)

logger = logging.getLogger(__name__)


def _get_remote_agent_config(info: str) -> str:
    return info


async def stream_agent_execution(db, rule_id: int) -> AsyncGenerator[dict, None]:
    """Stream remote agent execution logs for all stocks in the rule's pools."""
    logger.info("=== Starting agent execution for rule_id=%s ===", rule_id)
    try:
        rule_record = db.session.query(Rule).filter(Rule.id == rule_id).first()
        if not rule_record:
            yield {"type": "error", "message": f"Rule {rule_id} not found"}
            return
        if rule_record.type != "remote_agent":
            yield {
                "type": "error",
                "message": f"Unsupported rule type for backtests: {rule_record.type}",
            }
            return

        yield {
            "type": "start",
            "message": f"Starting execution for rule: {rule_record.name} (ID: {rule_id})",
            "timestamp": datetime.now().isoformat(),
        }

        pool_ids = [
            pool_id
            for (pool_id,) in db.session.query(RulePool.pool_id)
            .filter(RulePool.rule_id == rule_id)
            .distinct()
            .all()
            if pool_id
        ]
        if not pool_ids:
            yield {"type": "warning", "message": "No pools found for this rule"}
            return

        stock_list = [
            stock_code.split(".")[0] if "." in stock_code else stock_code
            for (stock_code,) in db.session.query(PoolStock.stock_code)
            .filter(PoolStock.pool_id.in_(pool_ids))
            .distinct()
            .all()
        ]
        if not stock_list:
            yield {"type": "warning", "message": "No stocks found in pools"}
            return

        yield {
            "type": "info",
            "message": f"Found {len(stock_list)} stocks to process",
            "stocks": stock_list,
        }

        for index, stock_code in enumerate(stock_list, 1):
            yield {
                "type": "stock_start",
                "message": f"[{index}/{len(stock_list)}] Processing {stock_code}...",
                "stock_code": stock_code,
                "progress": f"{index}/{len(stock_list)}",
            }
            try:
                async for log_entry in stream_remote_agent_logs(db, rule_id, stock_code):
                    yield log_entry
            except Exception as exc:
                logger.exception("Error processing stock %s", stock_code)
                yield {
                    "type": "stock_error",
                    "message": f"✗ {stock_code}: {exc}",
                    "stock_code": stock_code,
                    "error": str(exc),
                }

        yield {
            "type": "complete",
            "message": f"Execution complete for rule {rule_id}",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as exc:
        logger.exception("Error in stream_agent_execution")
        yield {"type": "error", "message": f"Fatal error: {exc}"}


async def stream_remote_agent_logs(db, rule_id: int, stock_code: str) -> AsyncGenerator[dict, None]:
    """Stream logs from remote A2A agent execution."""
    rule_record = db.session.query(Rule).filter(Rule.id == rule_id).first()
    if not rule_record:
        yield {"type": "error", "message": f"Rule {rule_id} not found", "stock_code": stock_code}
        return

    base_url = _get_remote_agent_config(rule_record.info)
    logger.info("Using base_url: %s", base_url)

    try:
        yield {
            "type": "log",
            "message": f"Connecting to remote agent at {base_url}...it may take 30~60s...",
            "stock_code": stock_code,
        }

        yield {
            "type": "log",
            "message": f"Using skill agent execution flow for {stock_code}",
            "stock_code": stock_code,
        }
        result = None
        async for adapter_event in stream_trading_agent_via_skill(stock_code, base_url):
            if adapter_event["type"] == "streaming_text":
                yield {
                    "type": "streaming_text",
                    "message": adapter_event["message"],
                    "stock_code": stock_code,
                }
            elif adapter_event["type"] == "result":
                result = adapter_event["result"]

        action = extract_trading_action(result)
        is_indicating = action == Trade.buy

        indicating = Trade.indicating if is_indicating else Trade.not_indicating
        update_rule_trading(db, rule_id, indicating, stock_code, datetime.now().date())

        result_msg = f"Decision: {'INDICATING' if is_indicating else 'NOT INDICATING'}"
        yield {
            "type": "remote_result",
            "message": f"{result_msg} (action={action or 'unknown'})",
            "stock_code": stock_code,
            "indicating": is_indicating,
        }
        yield {
            "type": "stock_complete",
            "message": f"✓ {stock_code}: {result_msg}",
            "stock_code": stock_code,
        }
    except Exception as exc:
        logger.exception("Error running remote agent")
        yield {
            "type": "error",
            "message": f"Remote agent error: {exc}",
            "stock_code": stock_code,
        }


async def stream_single_stock_execution(db, rule_id: int, stock_code: str) -> AsyncGenerator[dict, None]:
    """Stream remote agent execution logs for a single stock."""
    try:
        rule_record = db.session.query(Rule).filter(Rule.id == rule_id).first()
        if not rule_record:
            yield {"type": "error", "message": f"Rule {rule_id} not found"}
            return
        if rule_record.type != "remote_agent":
            yield {
                "type": "error",
                "message": f"Unsupported rule type for backtests: {rule_record.type}",
                "stock_code": stock_code,
            }
            return

        yield {
            "type": "start",
            "message": f"Running {stock_code} for rule: {rule_record.name} (ID: {rule_id})",
            "timestamp": datetime.now().isoformat(),
            "stock_code": stock_code,
        }

        async for log_entry in stream_remote_agent_logs(db, rule_id, stock_code):
            yield log_entry

        yield {
            "type": "complete",
            "message": f"Execution complete for {stock_code}",
            "timestamp": datetime.now().isoformat(),
            "stock_code": stock_code,
        }
    except Exception as exc:
        logger.exception("Error in stream_single_stock_execution")
        yield {
            "type": "error",
            "message": f"Fatal error: {exc}",
            "stock_code": stock_code,
        }
