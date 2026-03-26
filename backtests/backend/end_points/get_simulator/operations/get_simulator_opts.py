import json
import logging
import traceback
import pandas as pd

from end_points.common.const.consts import INIT_MONEY, DataBase, RuleType
from sqlalchemy import and_
from end_points.common.utils.http import APIException
from end_points.get_rule.operations.agent_utils import run_sim_agent
from end_points.get_simulator.simulator_schema import SimulatorSchema, SimTradingSchema
from end_points.get_simulator.operations.get_simulator_utils import write_sim_log, read_sim_log, delete_sim_log, \
    clean_sim_trading, max_drawback, sharpe, get_last_month_stats, cal_annual_earn
from db.models import Simulator, Stock, Rule, SimTrading
from end_points.get_stock.operations.get_stock_utils import stockDataFrame

def getSimulatorList(db, args):
    status = args.get("status")
    rule_type = args.get("rule_type")
    filter_all = list()
    try:
        query = db.session.query(Simulator.id, Simulator.stock_code, Simulator.status, Simulator.start_date,
                                     Simulator.init_money, Simulator.earning_info,
                                     Simulator.current_money, Simulator.current_shares, Simulator.cum_earn,
                                     Simulator.avg_earn, Simulator.earning_rate, Simulator.trading_times, Simulator.rule_id, Simulator.indicating_date,
                                     Simulator.updated_at, Rule.name.label("rule_name"), Rule.type) \
                .join(Rule, Rule.id == Simulator.rule_id)
        if rule_type:
            filter_all.append(Rule.type == rule_type)
        query = query.filter(and_(*filter_all))
        rows = query.order_by(Simulator.status.desc()).order_by(Simulator.cum_earn.desc()).all()
        total = query.count()
        # Use Pydantic to serialize SQLAlchemy objects (FastAPI native way)
        # Convert Row objects to dictionaries first
        data = [SimulatorSchema.model_validate(row._asdict()).model_dump() for row in rows]
        # calculate max drop back and last month stats
        if rule_type in [RuleType.agent, RuleType.remote_agent]:
            for i in range(len(data)):
                earning_info = data[i].get('earning_info')
                rule_id = data[i].get('rule_id')
                earning_dict = json.loads(earning_info) if earning_info is not None else {}
                earns = earning_dict.get('earns')
                cum_earn = data[i].get('cum_earn')
                if earning_dict != {}:
                    bought_dates = earning_dict.get('bought_dates', [])
                    if bought_dates and len(bought_dates) > 0:
                        first_buy_date = bought_dates[0]
                        annual_earn = cal_annual_earn(first_buy_date, cum_earn)
                        data[i].update({'annual_earn':annual_earn, 'first_trade_date':first_buy_date})
                if earns is not None and len(earns) > 0:
                    update_date = data[i].get('updated_at')
                    r_cum_earn_after, r_earn_rate_after, r_avg_earn_after, r_trading_times = get_last_month_stats(earning_dict, update_date)
                    result = {
                        "max_drawback": max_drawback(earns),
                        "sharpe": sharpe(earns),
                        "r_cum_earn_after": r_cum_earn_after,
                        "r_earn_rate_after": r_earn_rate_after,
                        "r_avg_earn_after": r_avg_earn_after,
                        "r_trading_times": r_trading_times,
                        }
                    data[i].update(result)
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
        logging.error(f"Error in getSimulatorList: {err}")
        e = APIException('2201')
        rst = e.to_dict()
    return rst


def addSimulator(db, args):
    stock_code = args.get('stock_code')
    rule_id = args.get('rule_id')
    init_money = args.get('init_money') if args.get('init_money') else INIT_MONEY
    start_date = args.get('start_date')

    try:
        # verify rule and stock
        rule_record = db.session.query(Rule).filter(Rule.id == rule_id).first()
        if not rule_record:
            raise Exception("rule or stock doesn't exist")
        if stock_code:
            stock_record = db.session.query(Stock).filter(Stock.code == stock_code).first()
            if not stock_record:
                raise Exception("rule or stock doesn't exist")

        # verify sim record
        sim_query = db.session.query(Simulator).filter(Simulator.rule_id == rule_id).filter(Simulator.start_date == start_date)
        if stock_code:
            sim_query = sim_query.filter(Simulator.stock_code == stock_code)
        sim_record = sim_query.first()
        if sim_record:
            raise Exception("simulator already exist")

        sim_record = Simulator(
            stock_code=stock_code,
            rule_id=rule_id,
            init_money=init_money,
            current_money=init_money,
            current_shares=0,
            start_date=start_date
        )
        db.session.add(sim_record)
        db.session.commit()
        # write log
        sim_id = sim_record.id
        message = "Sim {} start running!".format(sim_id)
        try:
            write_sim_log(sim_id, message, 'DodgerBlue', sim_record.start_date)
        except Exception:
            logging.exception("Failed to write initial simulator log for sim_id=%s", sim_id)

        rst = {
            'code': 'SUCCESS',
            'data': sim_id
        }

    except Exception as e:
        db.session.rollback()
        err = traceback.format_exc()
        logging.error(f"Error in addSimulator: {err}")
        e = APIException('2209')
        rst = e.to_dict()
    return rst

def getSimulator(db, sim_id, args):
    try:
        log_data = read_sim_log(sim_id)
        rst = {
            'code': 'SUCCESS',
            'log_data': log_data,
        }
    except Exception as e:
        err = traceback.format_exc()
        logging.error(f"Error in getSimulator: {err}")
        db.session.rollback()
        e = APIException('2208')
        rst = e.to_dict()
    return rst

def getSimTrading(db, sim_id, args):
    page = 1 if args.get("page") is None else args.get("page")
    page_size = 100 if args.get("page_size") is None else args.get("page_size")
    stock = args.get("stock")
    trading_type = args.get("trading_type")
    filter_all = list()
    try:
        query = db.session.query(SimTrading).filter(SimTrading.sim_id == sim_id)
        if stock != '' and stock is not None:
            filter_all.append(SimTrading.stock == stock)
        if trading_type != '' and trading_type is not None:
            filter_all.append(SimTrading.trading_type == trading_type)
        query = query.filter(and_(*filter_all))
        offset = (page - 1) * page_size
        new_rows = query.order_by(SimTrading.trading_date.desc()).offset(offset).limit(page_size).all()
        total = query.count()
        # Use Pydantic to serialize SQLAlchemy objects (FastAPI native way)
        data = [SimTradingSchema.model_validate(row).model_dump() for row in new_rows]
        stocks = db.session.query(SimTrading.stock).filter(SimTrading.sim_id == sim_id).all()
        stocks = sorted(set([x for (x,) in stocks]))  # Use sorted for deterministic order
        for i in range(len(data)):
            stock_code = data[i].get('stock')
            stock_name = db.session.query(Stock.name).filter(Stock.code == stock_code).scalar()
            data[i].update({'stock_name':stock_name})
        rst = {
            'code': 'SUCCESS',
            'data': {
                'total': total,
                'items': data,
                'stocks': stocks
            }
        }
    except Exception as e:
        db.session.rollback()
        err = traceback.format_exc()
        logging.error(f"Error in getSimTrading: {err}")
        e = APIException('2206')
        rst = e.to_dict()
    return rst

def deleteSimulator(db, sim_id):
    try:
        record = db.session.query(Simulator).filter(Simulator.id == sim_id).first()

        if record is None:
            rst = {'code': 'FAILURE', 'message': 'record does not exist!'}
            return rst
        else:
            # #clean up tradings
            clean_sim_trading(db, sim_id)

            # delete record
            db.session.delete(record)
            db.session.commit()

            # remove log file
            delete_sim_log(sim_id)

            rst = {
                'code': 'SUCCESS',
                'data': {
                    'sim_id': sim_id,
                }
            }
    except Exception as e:
        err = traceback.format_exc()
        logging.error(f"Error in deleteSimulator: {err}")
        db.session.rollback()
        rst = APIException('2208')
    return rst

def runSimulator(db, args, sim_id):
    try:
        sim_record = db.session.query(Simulator).filter(Simulator.id == sim_id).first()
        if sim_record is None:
            e = APIException('2207')
            rst = e.to_dict()
        else:
            # Agent system - run agent simulation
            run_sim_agent(db, sim_id)

            # Use Pydantic to serialize SQLAlchemy object (FastAPI native way)
            data = SimulatorSchema.model_validate(sim_record).model_dump()
            rst = {
                'code': 'SUCCESS',
                'data': data
            }
    except Exception as e:
        db.session.rollback()
        # terminate_thread(sim_id)
        err = traceback.format_exc()
        logging.error(f"Error in runSimulator: {err}")
        e = APIException('2207')
        rst = e.to_dict()
    return rst

def getParamsForSim(db, sim_id, args):
    try:
        earning_info = db.session.query(Simulator.earning_info).filter(Simulator.id == sim_id).scalar()
        earning_dict = json.loads(earning_info) if earning_info is not None else {}

        # Only calculate growth rates if data exists
        assets = earning_dict.get('assets')
        if assets and len(assets) > 0:
            earning_dict.update({'assets': calculate_growth_rate(assets)})

        bought_dates = earning_dict.get('bought_dates')
        if bought_dates and len(bought_dates) > 0:
            index_close = get_index_data_for_dates(db, bought_dates)
            if index_close and len(index_close) > 0:
                earning_dict.update({'index_close': calculate_growth_rate(index_close)})

        rst = {
            'code': 'SUCCESS',
            'data': {
                'items': earning_dict
            }
        }
    except Exception as e:
        db.session.rollback()
        err = traceback.format_exc()
        logging.error(f"Error in getParamsForSim: {err}")
        e = APIException('2201')
        rst = e.to_dict()
    return rst

def get_index_data_for_dates(db, bought_dates, index_code='sh000001'):
    index_df = stockDataFrame(db, index_code)
    bought_dates_df = pd.DataFrame(bought_dates, columns=['date'])
    bought_dates_df['date'] = pd.to_datetime(bought_dates_df['date'])
    index_df_on_date = index_df.merge(bought_dates_df, on=['date'], how='right')
    close_on_date = list(index_df_on_date.close.values)
    return close_on_date

def calculate_growth_rate(data):
    base = data[0]
    growth_rate = [ 0 if base == 0 else ((value - base) / base) * 100 for value in data]
    return growth_rate
