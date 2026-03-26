from datetime import datetime
import asyncio
import pandas as pd
import logging

from db.models import Simulator, AgentTrading, Rule, RulePool, PoolStock
from end_points.common.const.consts import Trade
from end_points.get_simulator.operations.get_simulator_utils import update_sim_model
from end_points.get_rule.operations.skill_agent_adapter import (
    execute_trading_agent_via_skill,
    extract_trading_action,
)

logger = logging.getLogger(__name__)


def get_agent_buying_stocks(db, rule_id):
    """
    Get all stocks from pools that belong to this rule.

    Args:
        db: Database session
        rule_id: Rule ID

    Returns:
        List of stock codes (strings) without exchange suffix
    """
    # Get distinct pool_ids for this rule_id
    pool_ids = db.session.query(RulePool.pool_id)\
        .filter(RulePool.rule_id == rule_id)\
        .distinct()\
        .all()

    pool_ids = [p[0] for p in pool_ids if p[0]]

    if not pool_ids:
        return []

    # Get all stock codes for these pool_ids
    stocks = db.session.query(PoolStock.stock_code)\
        .filter(PoolStock.pool_id.in_(pool_ids))\
        .distinct()\
        .all()

    # Strip exchange suffix (e.g., '000001.SZ' -> '000001')
    stock_list = [s.split('.')[0] if '.' in s else s for (s,) in stocks]
    return stock_list

def update_rule_trading(db, rule_id, trade_type, stock_code, trade_date):
    """
    Update trading record for a rule/stock/date.
    Uses merge() to handle concurrent updates safely.
    """
    from sqlalchemy import exc
    from sqlalchemy.orm.attributes import flag_modified

    # Strip stock exchange suffix before storing in database
    stock_code = stock_code.split('.')[0] if '.' in stock_code else stock_code

    # First try to get existing record
    existing_record = db.session.query(AgentTrading)\
        .filter(AgentTrading.rule_id == rule_id)\
        .filter(AgentTrading.stock == stock_code)\
        .filter(AgentTrading.trading_date == trade_date)\
        .with_for_update()\
        .first()

    if existing_record:
        # Update existing record and explicitly mark as modified
        existing_record.trading_type = trade_type
        flag_modified(existing_record, 'trading_type')
    else:
        # Insert new record (will fail if concurrent insert happened)
        new_record = AgentTrading(
            rule_id=rule_id,
            trading_type=trade_type,
            stock=stock_code,
            trading_date=trade_date,
        )
        db.session.add(new_record)

    try:
        db.session.commit()
    except exc.IntegrityError:
        # Handle concurrent insert: retry by getting and updating
        db.session.rollback()
        existing_record = db.session.query(AgentTrading)\
            .filter(AgentTrading.rule_id == rule_id)\
            .filter(AgentTrading.stock == stock_code)\
            .filter(AgentTrading.trading_date == trade_date)\
            .first()
        if existing_record:
            existing_record.trading_type = trade_type
            flag_modified(existing_record, 'trading_type')
            db.session.commit()
        else:
            # Should not happen, but fallback to insert
            new_record = AgentTrading(
                rule_id=rule_id,
                trading_type=trade_type,
                stock=stock_code,
                trading_date=trade_date,
            )
            db.session.add(new_record)
            db.session.commit()
    return

def run_sim_agent(db, agent_sim_id):
    agent_rule_id = db.session.query(Simulator.rule_id).filter(Simulator.id == agent_sim_id).scalar()
    record = db.session.query(AgentTrading).filter(AgentTrading.rule_id == agent_rule_id).all()
    indicating_items = []
    for each_item in record:
        stock_code = each_item.stock
        indicating_date = pd.Timestamp(each_item.trading_date)
        indi_item = {
            'stock_code': stock_code,
            'indicating_date': indicating_date,
        }
        indicating_items.append(indi_item)

    indicating_date = update_sim_model(db, agent_sim_id, indicating_items)
    return indicating_date


def run_async(coro):
    """Run async code in a separate thread to avoid event-loop conflicts."""
    import concurrent.futures

    def run_in_thread():
        return asyncio.run(coro)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_in_thread)
        return future.result()


def run_agent_for_stock(db, rule_id, stock_code):
    """
    Run a remote agent rule for a single stock.

    Args:
        db: Database session
        rule_id: Remote agent rule ID
        stock_code: Stock code to analyze

    Returns:
        dict: {
            'success': bool,
            'stock_code': str,
            'indicating': str,
            'result': bool,
            'error': str (if failed)
        }
    """
    indicating_date = datetime.now().date()
    print(f'Start running agent {rule_id} for {stock_code}...')

    # Get rule information to check type
    rule_record = db.session.query(Rule).filter(Rule.id == rule_id).first()
    if not rule_record:
        return {
            'success': False,
            'stock_code': stock_code,
            'error': f'Rule {rule_id} not found'
        }

    rule_type = rule_record.type

    if rule_type != 'remote_agent':
        return {
            'success': False,
            'stock_code': stock_code,
            'error': f'Unsupported rule type for backtests: {rule_type}'
        }

    base_url = rule_record.info
    if not base_url:
        return {
            'success': False,
            'stock_code': stock_code,
            'error': 'Remote agent must have a base_url in info field'
        }

    try:
        clean_stock_code = stock_code.split('.')[0] if '.' in stock_code else stock_code
        result = run_async(
            execute_agent_with_skill_adapter(clean_stock_code, base_url)
        )
        action = extract_trading_action(result)
        is_indicating = action == Trade.buy
        indicating = Trade.indicating if is_indicating else Trade.not_indicating

        update_rule_trading(db, rule_id, indicating, stock_code, indicating_date)
        print(f'Result from Remote Agent {rule_id}: {stock_code} is {indicating}!')

        rule_record.updated_at = datetime.now()
        db.session.commit()

        return {
            'success': True,
            'stock_code': stock_code,
            'indicating': indicating,
            'result': is_indicating,
            'action': action,
        }

    except Exception as e:
        print(f'Error running remote agent {rule_id} for stock {stock_code}: {e}')
        import traceback
        traceback.print_exc()

        indicating = Trade.not_indicating
        update_rule_trading(db, rule_id, indicating, stock_code, indicating_date)
        db.session.commit()

        return {
            'success': False,
            'stock_code': stock_code,
            'error': str(e)
        }


def run_agent(db, rule_id):
    """
    Run an agent-type rule for all stocks in its pools.

    Args:
        db: Database session
        rule_id: Agent rule ID
    """
    buying_stocks_list = get_agent_buying_stocks(db, rule_id)
    print(f'Buying stocks for today are: {buying_stocks_list}')

    for stock_code in buying_stocks_list:
        run_agent_for_stock(db, rule_id, stock_code)


async def execute_agent_with_skill_adapter(stock_code, base_url):
    return await execute_trading_agent_via_skill(stock_code, base_url)
