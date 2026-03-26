from db.models import PoolRuleEarn, Rule, StockRuleEarn
from end_points.get_earn.earn_schema import EarnSchema
from end_points.get_earn.operations.cal_earn_utils import getStockRuleEarnModel, cal_avg_earn_model
from end_points.get_rule.operations.get_rule_utils import getPoolsForRule
from end_points.common.const.consts import DataBase, INIT_MONEY_PER_STOCK, RuleType
from end_points.get_stock.operations.get_stock_utils import get_stocks_for_pool


def getPoolRuleEarnModel(bind_key):
    """Get the PoolRuleEarn model class

    Note: DH/DQ databases have been removed, all use the same model
    """
    # All bind keys now use the same PoolRuleEarn model
    return PoolRuleEarn

def getStockEarn(db, stock_code, rule_id, bind_key):
    # updated_at = datetime(1900,1,1)
    result = {}
    model_class = getStockRuleEarnModel(bind_key)
    record = db.session.query(model_class) \
        .filter(model_class.rule_id == rule_id) \
        .filter(model_class.stock_code == stock_code).first()
    if record:
        # Use Pydantic to serialize SQLAlchemy objects (FastAPI native way)
        result = EarnSchema.model_validate(record).model_dump()
    return result

def getPoolRuleEarn(db, pool_id, rule_id, bind_key):
    result = {}
    # get pool_rule_earn
    model_class = getPoolRuleEarnModel(bind_key)
    record = db.session.query(model_class) \
        .filter(model_class.rule_id == rule_id) \
        .filter(model_class.pool_id == pool_id).first()
    if record:
        # Use Pydantic to serialize SQLAlchemy objects (FastAPI native way)
        result = EarnSchema.model_validate(record).model_dump()
    return result

def getRuleEarn(db, rule_id, bind_key=DataBase.stocks):
    earn_results = []
    pools = getPoolsForRule(db, rule_id)
    for each_item in pools:
        pool_id = each_item.id
        stock_num = each_item.stocks
        earn_result = getPoolRuleEarn(db, pool_id, rule_id, bind_key)
        earn_result.update({"stock_num": stock_num})
        earn_results.append(earn_result)
    earn, avg_earn, earning_rate, trading_times, updated_at = cal_avg_earn(earn_results)
    rst = {
        "earn": earn,
        "avg_earn": avg_earn,
        'trading_times': trading_times,
        'earning_rate': earning_rate,
        "updated_at": updated_at
    }
    return rst

def updatePoolEarn(db, pool_id, rule_id, bind_key=DataBase.stocks):
    # update value
    earn_results = []
    stocks = get_stocks_for_pool(db.session, pool_id)

    for stock_code in stocks:
        # get updated value
        earn_result = getStockEarn(db, stock_code, rule_id, bind_key)
        earn_results.append(earn_result)

    # Agent system uses model-style earning calculation
    earn, avg_earn, earning_rate, trading_times, updated_at = cal_avg_earn_model(earn_results)

    # update record
    model_class = getPoolRuleEarnModel(bind_key)
    old_record = db.session.query(model_class).filter(model_class.rule_id == rule_id) \
        .filter(model_class.pool_id == pool_id).first()
    if old_record:
        old_record.earn = earn
        old_record.avg_earn = avg_earn
        old_record.trading_times = trading_times
        old_record.earning_rate = earning_rate
        # Don't set updated_at manually - let DB handle it with ON UPDATE CURRENT_TIMESTAMP
        db.session.commit()
    else:
        new_record = model_class(
            pool_id=pool_id,
            rule_id=rule_id,
            earn=earn,
            avg_earn=avg_earn,
            trading_times=trading_times,
            earning_rate=earning_rate
            # updated_at will use DEFAULT CURRENT_TIMESTAMP
        )
        db.session.add(new_record)
        db.session.commit()
    return
