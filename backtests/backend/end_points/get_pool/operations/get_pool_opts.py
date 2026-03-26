import logging
import traceback

from db.models import Pool, PoolStock, RulePool
from end_points.common.const.consts import DataBase
from end_points.common.utils.db import build_one_result, getPoolRuleEarnModel
from end_points.common.utils.http import APIException
from end_points.get_pool.operations.get_pool_utils import update_latest_date
from end_points.get_rule.operations.get_rule_utils import cleanPoolRuleEarnForPool
from end_points.get_stock.operations.get_stock_opts import removeStockFromPool
from end_points.get_pool.pool_schema import PoolSchema


def getPoolList(db):
    try:
        update_latest_date(db)
        query = db.session.query(Pool)
        rows = query.order_by(Pool.id).all()
        total = query.count()
        # Use Pydantic to serialize SQLAlchemy objects (FastAPI native way)
        data = [PoolSchema.model_validate(row).model_dump() for row in rows]
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
        logging.error(err)
        e = APIException('2201')
        rst = e.to_dict()
    return rst

def createPool(db, args, user_id):
    name = args.get('name')
    if name is None:
        rst = {'code': 'FAILURE', 'message': 'need category name!'}
        return rst
    try:
        pool = db.session.query(Pool.name).filter(Pool.name == name).first()
        if pool:
            rst = {'code': 'FAILURE', 'message': 'Pool already exists!'}
            return rst

        record = Pool(
            name=name,
        )
        db.session.add(record)
        db.session.commit()
        rst = {
            'code': 'SUCCESS',
            'data': {
                'id': record.id,
            }
        }
    except Exception as e:
        db.session.rollback()
        err = traceback.format_exc()
        logging.error(err)
        e = APIException('2209')
        rst = e.to_dict()
    return rst

def getPool(db, pool_id):
    try:
        record = db.session.query(Pool.id, Pool.name).filter(Pool.id == pool_id).first()
        if record is None:
            e = APIException('2206')
            rst = e.to_dict()
        else:
            items = ['id', 'name']
            data = build_one_result(record, items)
            rst = {
                'code': 'SUCCESS',
                'data': data
            }
    except Exception as e:
        db.session.rollback()
        err = traceback.format_exc()
        logging.error(err)
        e = APIException('2206')
        rst = e.to_dict()
    return rst

def deletePool(db, pool_id):
    try:
        record = db.session.query(Pool).filter(Pool.id == pool_id).first()
        stocks = db.session.query(PoolStock.stock_code).filter(Pool.id == pool_id).all()
        # record2 = db.session.query(PoolStock).filter(PoolStock.pool_id == pool_id).all()
        record3 = db.session.query(RulePool).filter(RulePool.pool_id == pool_id).all()

        if record is None:
            e = APIException('2208')
            rst = e.to_dict()
        else:
            # clean up stocks for pool
            if stocks:
                for stock in stocks:
                    stock_code = stock[0]
                    removeStockFromPool(db, stock_code, {'pool_id': pool_id})

            # delete pool stock
            # if record2:
            #     for reg in record2:
            #         db.session.delete(reg)
            #     db.session.commit()

            # delete rule pool
            if record3:
                for reg in record3:
                    db.session.delete(reg)
                db.session.commit()

            # clean up rule pool earn
            cleanPoolRuleEarnForPool(db, getPoolRuleEarnModel(DataBase.stocks), pool_id)
            # DH/DQ databases removed - no longer need to clean them up

            # delete pool
            db.session.delete(record)
            db.session.commit()
            rst = {
                'code': 'SUCCESS',
                'data': {
                    'id': pool_id,
                }
            }
    except Exception as e:
        err = traceback.format_exc()
        logging.error(err)
        db.session.rollback()
        e = APIException('2208')
        rst = e.to_dict()
    return rst

def updatePool(db, args, pool_id, user_id):
    name = args.get('name')
    if name is None:
        rst = {'code': 'FAILURE', 'message': 'need pool name!'}
        return rst
    try:
        pool_record = db.session.query(Pool).filter(Pool.id == pool_id).first()
        if pool_record is None:
            e = APIException('2207')
            rst = e.to_dict()
        else:
            pool_record.name = name
            db.session.commit()
            rst = {
                'code': 'SUCCESS',
                'data': {
                    'id': pool_id
                }
            }
    except Exception as e:
        db.session.rollback()
        err = traceback.format_exc()
        logging.error(err)
        e = APIException('2207')
        rst = e.to_dict()
    return rst
