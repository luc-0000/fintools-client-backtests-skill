import logging
import traceback

from sqlalchemy import and_

from end_points.common.const.consts import DataBase
from end_points.common.utils.http import APIException
from end_points.common.utils.utils import sort_dict_with_none
from end_points.get_earn.operations.get_earn_utils import getStockEarn, getStockRuleEarnModel
from end_points.get_rule.operations.get_rule_utils import cleanStockRuleEarnForStock
from end_points.get_stock.operations.get_stock_utils import updateStockNumForPool, get_pool_names, get_stock_cap
from end_points.get_stock.stock_schema import StockSchema, StockDetailSchema, RuleSchema
from db.models import PoolStock, Stock, Pool, Rule
from data_processing.update_stocks.download_mydata_util import get_stock_table


def getStockList(db, args):
    pool_id = args.get('pool_id')
    stock_code = args.get('stock_code')
    stock_name = args.get('stock_name')
    filter_all = list()
    try:
        query = db.session.query(Stock)
        if pool_id:
            query = query.join(PoolStock, PoolStock.stock_code == Stock.code)
            if pool_id != -1:
                filter_all.append(PoolStock.pool_id == pool_id)
        if stock_code:
            filter_all.append(Stock.code.like(stock_code + "%"))
        if stock_name:
            filter_all.append(Stock.name.like(stock_name + "%"))
        query = query.filter(and_(*filter_all)).group_by(Stock.code)
        total = query.count()
        rows = query.all()
        # Use Pydantic to serialize SQLAlchemy objects (FastAPI native way)
        data = [StockSchema.model_validate(row).model_dump() for row in rows]
        if pool_id is not None:
            for each_stock in data:
                stock_code = each_stock.get('code')
                pool_names = get_pool_names(db, stock_code)
                each_stock.update({'pools': pool_names})
                cap = get_stock_cap(db, stock_code)
                each_stock.update({'cap': cap})

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
        logging.error(f"Error in getStockList: {err}")
        e = APIException('2201')
        rst = e.to_dict()
    return rst

def addStockToPool(db, args,user_id):
    code = args.get("code")
    pool_id = args.get("pool_id")
    try:
        #validate pool id
        record = db.session.query(Pool).filter(Pool.id == pool_id).first()
        if not record:
            rst = {'code': 'FAILURE', 'message': "pool doesn't exist"}
            return rst
        #validate stock
        stock = db.session.query(Stock).filter(Stock.code == code).first()
        if not stock:
            rst = {'code': 'FAILURE', 'message': "stock doesn't exist"}
            return rst
        stock_code = stock.code
        result = db.session.query(PoolStock)\
            .filter(PoolStock.pool_id == pool_id)\
            .filter(PoolStock.stock_code == stock_code).first()
        if result:
            rst = {'code': 'FAILURE', 'message': 'Registration already exists!'}
            return rst

        stockReg = PoolStock(
            pool_id=pool_id,
            stock_code=stock_code,
        )
        db.session.add(stockReg)
        db.session.commit()

        # update stock numbers for pool
        updateStockNumForPool(db, pool_id)

        rst = {
            'code': 'SUCCESS',
            'data': stock_code
        }
    except Exception as e:
        db.session.rollback()
        err = traceback.format_exc()
        logging.error(f"Error in addStockToPool: {err}")
        e = APIException('2209')
        rst = e.to_dict()
    return rst

def removeStockFromPool(db, stock_code, args):
    pool_id = args.get('pool_id')
    try:
        stock_record = db.session.query(Stock).filter(Stock.code == stock_code).first()
        if stock_record is None:
            rst = {'code': 'FAILURE', 'message': 'record does not exist!'}
            return rst
        else:
            pool_stock_query = db.session.query(PoolStock).filter(PoolStock.stock_code == stock_code)
            if pool_id != -1:
                pool_stock_records = pool_stock_query.filter(PoolStock.pool_id == pool_id).all()
            else:
                pool_stock_records = pool_stock_query.all()
            #clean up stock pool table
            if pool_stock_records:
                for i in pool_stock_records:
                    p_id = i.pool_id
                    db.session.delete(i)
                    db.session.commit()
                    # update stock numbers for pool
                    updateStockNumForPool(db, p_id)

            belong_to_other_pool = db.session.query(PoolStock).filter(PoolStock.stock_code == stock_code).first()
            if not belong_to_other_pool:
                # clean up stock_rule_earn records
                cleanStockRuleEarnForStock(db, getStockRuleEarnModel(DataBase.stocks), stock_code)
                # DH/DQ databases removed - all use the same stock_rule_earn table

            rst = {
                'code': 'SUCCESS',
                'data': {
                    'code': stock_code,
                }
            }
    except Exception as e:
        err = traceback.format_exc()
        logging.error(f"Error in removeStockFromPool: {err}")
        db.session.rollback()
        e = APIException('2208')
        rst = e.to_dict()
    return rst

def getStockDetail(db, stock_code, args):
    page = 1 if args.get("page") is None else args.get("page")
    page_size = 100 if args.get("page_size") is None else args.get("page_size")
    bind_key = DataBase.stocks if args.get("bind_key") is None else args.get('bind_key')
    try:
        st = get_stock_table(db, stock_code, bind_key)
        offset = (page - 1) * page_size

        # Get the correct engine for the bind_key
        engine = db.get_engine(bind_key)

        # Create a session bound to the correct engine
        from sqlalchemy.orm import Session
        with Session(engine) as session:
            new_rows = session.query(st).order_by(st.date.desc()).offset(offset).limit(page_size).all()
            total = session.query(st).count()
            # Use Pydantic to serialize SQLAlchemy objects (FastAPI native way)
            # Must do this within the session context
            data = [StockDetailSchema.model_validate(row).model_dump() for row in new_rows]
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
        logging.error(f"Error in getStockDetail: {err}")
        e = APIException('2206')
        rst = e.to_dict()
    return rst
def getStockRules(db, stock_code, args):
    bind_key = DataBase.stocks if args.get("bind_key") is None else args.get('bind_key')
    rule_items = []
    try:
        query = db.session.query(Rule)
        record = query.all()
        # Use Pydantic to serialize SQLAlchemy objects (FastAPI native way)
        data = [RuleSchema.model_validate(row).model_dump() for row in record]
        total = query.count()
        for each_rule in data:
            rule_id = each_rule.get('id')
            earn_result = getStockEarn(db, stock_code, rule_id, bind_key)
            each_rule.update(earn_result)
            rule_items.append(each_rule)
        rule_items = sort_dict_with_none(rule_items, 'avg_earn', True)
        rst = {
            'code': 'SUCCESS',
            'data': {
                "items": rule_items,
                "total": total
            },
        }
    except Exception as e:
        db.session.rollback()
        err = traceback.format_exc()
        logging.error(f"Error in getStockRules: {err}")
        e = APIException('2206')
        rst = e.to_dict()
    return rst
