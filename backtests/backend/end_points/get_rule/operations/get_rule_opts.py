import json
import logging
import traceback
from sqlalchemy import and_, func
from db.models import *
from end_points.common.utils.http import APIException
from end_points.common.utils.utils import sort_dict_with_none
from end_points.get_earn.operations.get_earn_utils import *
from end_points.get_pool.pool_schema import PoolSchema
from end_points.get_rule.rule_schema import RuleSchema
from end_points.get_rule.operations.get_rule_utils import *
from end_points.get_simulator.operations.get_simulator_opts import deleteSimulator
from end_points.get_stock.stock_schema import StockSchema
RETURN_THRESHOULD = 1.5


def getRuleList(db, args):
    rule_type = args.get("rule_type")
    filter_all = list()
    try:
        # get rules
        query = db.session.query(Rule)
        if rule_type:
            filter_all.append(Rule.type == rule_type)
        query = query.filter(and_(*filter_all))
        rows = query.all()
        total = query.count()
        # Use Pydantic to serialize SQLAlchemy objects (FastAPI native way)
        data = [RuleSchema.model_validate(row).model_dump() for row in rows]

        # get pools for each rule
        for i in range(len(data)):
            rule_id = data[i].get('id')
            pool_names = getPoolNamesForRule(db, rule_id)
            data[i]['pools'] = pool_names

            # get total stocks count for this rule (sum of stocks from all pools)
            total_stocks = 0
            pools_for_rule = db.session.query(Pool).join(RulePool, RulePool.pool_id == Pool.id) \
                .filter(RulePool.rule_id == rule_id).all()
            for pool in pools_for_rule:
                if pool.stocks:
                    total_stocks += pool.stocks
            data[i]['stocks'] = total_stocks

        data = sort_dict_with_none(data, 'earn', True)

        rst = {
            'code': 'SUCCESS',
            'data': {
                'total': total,
                'items': data
            }
        }
    except Exception as e:
        db.session.rollback()
        err = traceback.format_exc()
        logging.error(f"Error: {err}")
        e = APIException('2201')
        rst = e.to_dict()
    return rst


def deleteRule(db, rule_id):
    try:
        record = db.session.query(Rule).filter(Rule.id == rule_id).first()
        pools = db.session.query(Pool).join(RulePool, RulePool.pool_id == Pool.id) \
            .filter(RulePool.rule_id == rule_id).all()
        sims = db.session.query(Simulator).filter(Simulator.rule_id == rule_id).all()

        if record is None:
            e = APIException('2208')
            rst = e.to_dict()
        else:
            # clean up pools for rule
            if pools:
                for pool in pools:
                    pool_id = pool.id
                    removePoolFromRule(db, rule_id, {'pool_id': pool_id})

            # clean up agent trading records
            agent_tradings = db.session.query(AgentTrading).filter(AgentTrading.rule_id == rule_id).all()
            if agent_tradings:
                for trading in agent_tradings:
                    db.session.delete(trading)

            # clean up rule stock earn record
            cleanStockRuleEarnForRule(db, getStockRuleEarnModel(DataBase.stocks), rule_id)

            # clean up pool rule earn record
            cleanPoolRuleEarnForRule(db, getPoolRuleEarnModel(DataBase.stocks), rule_id)

            # clean up sims for rule
            if sims:
                for sim in sims:
                    sim_id = sim.id
                    deleteSimulator(db, sim_id)

            # clean up rule
            db.session.delete(record)
            db.session.commit()

            rst = {
                'code': 'SUCCESS',
                'data': {
                    'id': rule_id,
                }
            }
    except Exception as e:
        err = traceback.format_exc()
        logging.error(f"Error: {err}")
        db.session.rollback()
        e = APIException('2208')
        rst = e.to_dict()
    return rst


def getPoolListForRule(db, rule_id, args):
    bind_key = DataBase.stocks if args.get("bind_key") is None else args.get("bind_key")
    rule_type = args.get("rule_type")
    try:
        if rule_id == 0:
            query = db.session.query(Pool)
            if rule_type:
                query = query.join(RulePool, RulePool.pool_id == Pool.id) \
                    .join(Rule, Rule.id == RulePool.rule_id) \
                    .filter(Rule.type == rule_type)
        else:
            query = db.session.query(Pool) \
                .join(RulePool, RulePool.pool_id == Pool.id) \
                .filter(RulePool.rule_id == rule_id)

        rows = query.all()
        total = query.count()
        # Use Pydantic to serialize SQLAlchemy objects (FastAPI native way)
        data = [PoolSchema.model_validate(row).model_dump() for row in rows]

        for i in range(len(data)):
            pool_id = data[i].get('id')
            if rule_id == 0 and rule_type:
                # Model pool return logic removed - Agent system doesn't use this
                earn_result = {}
            else:
                # update pool_rule_earn
                updatePoolEarn(db, pool_id, rule_id, bind_key)
                # get pool_rule_earn
                earn_result = getPoolRuleEarn(db, pool_id, rule_id, bind_key)
            data[i].update(earn_result)
        data = sort_dict_with_none(data, 'earn', True)
        rst = {
            'code': 'SUCCESS',
            'data': {
                'total': total,
                'items': data
            }
        }
    except Exception as e:
        db.session.rollback()
        err = traceback.format_exc()
        logging.error(f"Error: {err}")
        e = APIException('2201')
        rst = e.to_dict()
    return rst


def addPoolToRule(db, rule_id, args):
    pool_ids = args.get('pool_ids')
    result_pool_ids = []
    try:
        rule_record = db.session.query(Rule).filter(Rule.id == rule_id).first()
        if not rule_record:
            rst = {'code': 'FAILURE', 'message': "pool or rule doesn't exist"}
            return rst
        for each_pool_id in pool_ids:
            # check if register already exsits
            result = db.session.query(RulePool).filter(RulePool.pool_id == each_pool_id).filter(
                RulePool.rule_id == rule_id).first()
            if result:
                continue

            pool_register = RulePool(
                pool_id=each_pool_id,
                rule_id=rule_id,
            )
            db.session.add(pool_register)
            db.session.commit()
            result_pool_ids.append(each_pool_id)
        rst = {
            'code': 'SUCCESS',
            'data': {'pool_id': result_pool_ids}
        }

    except Exception as e:
        db.session.rollback()
        err = traceback.format_exc()
        logging.error(f"Error: {err}")
        e = APIException('2209')
        rst = e.to_dict()
    return rst


def removePoolFromRule(db, rule_id, args):
    pool_id = args.get('pool_id')
    try:
        record = db.session.query(Pool).filter(Pool.id == pool_id).first()
        rule_pool_record = db.session.query(RulePool) \
            .filter(RulePool.rule_id == rule_id) \
            .filter(RulePool.pool_id == pool_id).all()
        if record is None or rule_pool_record is None:
            rst = {'code': 'FAILURE', 'message': 'record does not exist!'}
            return rst
        else:
            # clean up rule pool record
            if rule_pool_record:
                for i in rule_pool_record:
                    db.session.delete(i)
                db.session.commit()

            # clean up rule pool earn record
            cleanPoolRuleEarnForRulePool(db, getPoolRuleEarnModel(DataBase.stocks), rule_id, pool_id)
            # DH/DQ databases removed - all use the same pool_rule_earn table

            rst = {
                'code': 'SUCCESS',
                'data': {
                    'pool_id': pool_id,
                }
            }
    except Exception as e:
        err = traceback.format_exc()
        logging.error(f"Error: {err}")
        db.session.rollback()
        rst = APIException('2208')
    return rst


def getStockListForRule(db, rule_id, args):
    pool_id = args.get('pool_id')
    filter_all = list()
    try:
        query = db.session.query(Stock) \
            .join(PoolStock, PoolStock.stock_code.like(Stock.code + '%')) \
            .join(RulePool, RulePool.pool_id == PoolStock.pool_id)

        if rule_id:
            filter_all.append(RulePool.rule_id == rule_id)
        if pool_id:
            filter_all.append(PoolStock.pool_id == pool_id)

        query = query.filter(and_(*filter_all)).group_by(Stock.code)
        rows = query.all()
        total = query.count()
        # Use Pydantic to serialize SQLAlchemy objects (FastAPI native way)
        data = [StockSchema.model_validate(row).model_dump() for row in rows]

        rst = {
            'code': 'SUCCESS',
            'data': {
                'total': total,
                'items': data
            }
        }
    except Exception as e:
        db.session.rollback()
        err = traceback.format_exc()
        logging.error(f"Error: {err}")
        e = APIException('2201')
        rst = e.to_dict()
    return rst


def getParamsForRule(db, rule_id, args):
    try:
        rst = {
            'code': 'SUCCESS',
            'data': {
                'items': {}
            }
        }
    except Exception as e:
        db.session.rollback()
        err = traceback.format_exc()
        logging.error(f"Error: {err}")
        e = APIException('2201')
        rst = e.to_dict()
    return rst


def editRule(db, args, rule_id):
    name = args.get('name')
    description = args.get('description')
    info = args.get('info')
    threshould = args.get('threshould')
    model_location = args.get('model_location')
    scaler_location = args.get('scaler_location')
    encoder_location = args.get('encoder_location')
    split = args.get('split')
    try:
        rule_record = db.session.query(Rule).filter(Rule.id == rule_id).first()
        if rule_record is None:
            e = APIException('2207')
            rst = e.to_dict()
        else:
            if name is not None:
                rule_record.name = name
            if description is not None:
                rule_record.description = description
            # Handle info field - for agents, it's a simple string (path or URL)
            # For other rule types, it's a JSON object
            if info is not None:
                # Check if it's already a JSON object or a simple string
                try:
                    # Try to parse as JSON first
                    json.loads(info)
                    # If successful, it's already JSON, use as-is
                    rule_record.info = info
                except (json.JSONDecodeError, TypeError):
                    # Not JSON, treat as simple string
                    rule_record.info = info
            if threshould is not None:
                rule_info = json.loads(rule_record.info)
                rule_info['other']['threshould'] = threshould
                rule_record.info = json.dumps(rule_info)
            if model_location is not None:
                rule_info = json.loads(rule_record.info)
                rule_info['model'] = model_location
                rule_record.info = json.dumps(rule_info)
            if scaler_location is not None:
                rule_info = json.loads(rule_record.info)
                rule_info['scaler'] = scaler_location
                rule_record.info = json.dumps(rule_info)
            if encoder_location is not None:
                rule_info = json.loads(rule_record.info)
                rule_info['encoder'] = encoder_location
                rule_record.info = json.dumps(rule_info)
            if split is not None:
                rule_info = json.loads(rule_record.info)
                rule_info['other']['split'] = split
                rule_record.info = json.dumps(rule_info)
            db.session.commit()
            rst = {
                'code': 'SUCCESS',
                'data': {
                    'id': rule_id
                }
            }
    except Exception as e:
        db.session.rollback()
        err = traceback.format_exc()
        logging.error(f"Error: {err}")
        e = APIException('2207')
        rst = e.to_dict()
    return rst


def addRule(db, args):
    name = args.get('name')
    rule_type = args.get('type') if args.get('type') else RuleType.agent
    description = args.get('description')
    if description is None:
        description = ''
    info = args.get('info', '{}')
    agent_id = str(args.get('agent_id')).strip() if args.get('agent_id') is not None else None
    if not name:
        rst = {'code': 'FAILURE', 'message': 'Rule name is required!'}
        return rst

    try:
        # Check if rule with same name already exists
        existing_rule = db.session.query(Rule).filter(Rule.name == name).first()
        if existing_rule:
            rst = {'code': 'FAILURE', 'message': 'Rule with this name already exists!'}
            return rst

        if rule_type == RuleType.remote_agent and agent_id:
            existing_rule_by_agent_id = db.session.query(Rule).filter(Rule.agent_id == agent_id).first()
            if existing_rule_by_agent_id:
                rst = {'code': 'FAILURE', 'message': 'Rule with this Agent ID already exists!'}
                return rst

        # Create new rule
        new_rule = Rule(
            name=name,
            type=rule_type,
            description=description,
            info=info,
            agent_id=agent_id,
        )
        db.session.add(new_rule)
        db.session.commit()

        rst = {
            'code': 'SUCCESS',
            'data': {
                'id': new_rule.id,
                'name': new_rule.name,
                'type': new_rule.type
            }
        }
    except Exception as e:
        db.session.rollback()
        err = traceback.format_exc()
        logging.error(f"Error creating rule: {err}")
        e = APIException('2209')
        rst = e.to_dict()
    return rst


# Turbulence functionality removed - not used by Agent system

def runRuleAgent(db, rule_id):
    """Run an agent-type rule"""
    from end_points.get_rule.operations.agent_utils import run_agent
    try:
        run_agent(db, rule_id)
        rst = {
            'code': 'SUCCESS',
            'data': {
                'id': rule_id,
            }
        }
    except Exception as e:
        err = traceback.format_exc()
        logging.error(f"Error running rule agent: {err}")
        db.session.rollback()
        e = APIException('2209')
        rst = e.to_dict()
    return rst


def getAgentTradingList(db, rule_id, page=1, page_size=50):
    """Get rule trading list by rule_id"""
    try:
        query = db.session.query(AgentTrading).filter(AgentTrading.rule_id == rule_id)
        total = query.count()
        rows = query.order_by(AgentTrading.trading_date.desc()).offset((page - 1) * page_size).limit(page_size).all()

        data = []
        for row in rows:
            data.append({
                'id': row.id,
                'rule_id': row.rule_id,
                'stock': row.stock,
                'trading_date': row.trading_date.isoformat() if row.trading_date else None,
                'trading_type': row.trading_type,
                'trading_amount': row.trading_amount,
                'created_at': row.created_at.isoformat() if row.created_at else None,
                'updated_at': row.updated_at.isoformat() if row.updated_at else None,
            })

        rst = {
            'code': 'SUCCESS',
            'data': {
                'total': total,
                'items': data
            }
        }
    except Exception as e:
        err = traceback.format_exc()
        logging.error(f"Error: {err}")
        db.session.rollback()
        e = APIException('2201')
        rst = e.to_dict()
    return rst


def runAgentForStock(db, rule_id, stock_code):
    """Run agent for a single stock"""
    from end_points.get_rule.operations.agent_utils import run_agent_for_stock
    try:
        result = run_agent_for_stock(db, rule_id, stock_code)
        if result.get('success'):
            rst = {
                'code': 'SUCCESS',
                'data': result
            }
        else:
            rst = {
                'code': 'ERROR',
                'errMsg': result.get('error', 'Failed to run agent for stock')
            }
    except Exception as e:
        err = traceback.format_exc()
        logging.error(f"Error: {err}")
        db.session.rollback()
        e = APIException('2201')
        rst = e.to_dict()
    return rst


def getRuleStocksIndicating(db, rule_id):
    """Get all stocks for a rule with their today's indicating status"""
    from datetime import date
    try:
        # Get all stocks from pools that belong to this rule
        pool_ids = db.session.query(RulePool.pool_id)\
            .filter(RulePool.rule_id == rule_id)\
            .distinct()\
            .all()

        pool_ids = [p[0] for p in pool_ids if p[0]]

        if not pool_ids:
            rst = {
                'code': 'SUCCESS',
                'data': {
                    'items': [],
                    'last_run_time': None
                }
            }
            return rst

        # Get all unique stock codes for these pool_ids
        # PoolStock.stock_code has suffix (e.g., '000001.SZ'), but Stock.code is now clean (e.g., '000001')
        pool_stocks = db.session.query(PoolStock.stock_code)\
            .filter(PoolStock.pool_id.in_(pool_ids))\
            .distinct()\
            .all()

        # Strip suffix from stock codes to match with Stock.code
        stock_codes_with_suffix = [s[0] for s in pool_stocks]
        clean_stock_codes = list(set([s.split('.')[0] if '.' in s else s for s in stock_codes_with_suffix]))

        # Query Stock table using clean codes
        stocks_query = db.session.query(Stock.code, Stock.name)\
            .filter(Stock.code.in_(clean_stock_codes))\
            .distinct()\
            .all()

        stock_list = [{'code': s[0], 'name': s[1]} for s in stocks_query]

        # Use clean codes for AgentTrading query
        actual_stock_codes = clean_stock_codes

        # Get today's date
        today = date.today()

        # Get the last run time from Rule's updated_at
        rule_record = db.session.query(Rule).filter(Rule.id == rule_id).first()
        last_run_time = rule_record.updated_at.isoformat() if rule_record and rule_record.updated_at else None

        # Get today's indicating status for each stock
        stock_codes = [s['code'] for s in stock_list]
        logging.info(f"Querying AgentTrading for rule_id={rule_id}, stock_codes={stock_codes}, today={today}")

        tradings_query = db.session.query(AgentTrading)\
            .filter(AgentTrading.rule_id == rule_id)\
            .filter(AgentTrading.stock.in_(stock_codes))\
            .filter(func.date(AgentTrading.trading_date) == today)\
            .all()

        logging.info(f"Found {len(tradings_query)} AgentTrading records")

        # Latest run time (overall) per stock based on updated_at
        last_run_query = db.session.query(
            AgentTrading.stock,
            func.max(AgentTrading.updated_at)
        )\
            .filter(AgentTrading.rule_id == rule_id)\
            .filter(AgentTrading.stock.in_(stock_codes))\
            .group_by(AgentTrading.stock)\
            .all()

        last_run_dict = {s: (dt.isoformat() if dt else None) for s, dt in last_run_query}

        # Create a dict for quick lookup of today's latest run
        trading_dict = {}
        for t in tradings_query:
            created_at = t.created_at.isoformat() if t.created_at else None
            if t.stock not in trading_dict:
                trading_dict[t.stock] = {
                    'trading_type': t.trading_type,
                    'created_at': created_at
                }
            else:
                # Keep the latest created_at for today
                existing = trading_dict[t.stock].get('created_at')
                if existing is None or (created_at and created_at > existing):
                    trading_dict[t.stock] = {
                        'trading_type': t.trading_type,
                        'created_at': created_at
                    }

        # Merge data
        result = []
        executed_count = 0
        for stock in stock_list:
            code = stock['code']
            if code in trading_dict:
                stock['indicating'] = trading_dict[code]['trading_type'] == 'indicating'
                stock['executed_at'] = trading_dict[code]['created_at']
                executed_count += 1
            else:
                stock['indicating'] = None  # Not executed yet today
                stock['executed_at'] = None
            stock['last_executed_at'] = last_run_dict.get(code)
            result.append(stock)

        rst = {
            'code': 'SUCCESS',
            'data': {
                'items': result,
                'last_run_time': last_run_time,
                'executed_count': executed_count,
                'total_count': len(result)
            }
        }
    except Exception as e:
        err = traceback.format_exc()
        logging.error(f"Error: {err}")
        db.session.rollback()
        e = APIException('2201')
        rst = e.to_dict()
    return rst
