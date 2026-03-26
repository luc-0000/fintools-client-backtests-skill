import pandas
import pandas as pd
from end_points.common.const.consts import DataBase
from db.models import Stock, Pool, PoolStock, RulePool, StocksInPool
from db.models_dynamic import get_stock_model


def get_stocks_for_pool(session, pool_id):
    stocks = session.query(Stock.code) \
        .join(PoolStock, PoolStock.stock_code == Stock.code) \
        .filter(PoolStock.pool_id == pool_id).all()
    all_stock_codes = [x for (x,) in stocks]
    return all_stock_codes

def updateStockNumForPool(db, pool_id):
    record = db.session.query(Pool).filter(Pool.id == pool_id).first()
    stocks = db.session.query(Stock).join(PoolStock, PoolStock.stock_code == Stock.code).filter(PoolStock.pool_id == pool_id)
    stocks_num = stocks.count()
    record.stocks = stocks_num
    db.session.commit()
    return

def stockDataFrame(db, stock_code, bind_key=DataBase.stocks):
    engine = db.get_engine(bind_key=bind_key)
    stock_data = pandas.read_sql_table(stock_code, engine)
    stock_data = stock_data.drop(columns=['id']).sort_values(by='date')
    return stock_data

def get_pool_names(db, stock_code):
    pool_names = ''
    pools = db.session.query(Pool.name).join(PoolStock, Pool.id==PoolStock.pool_id).filter(PoolStock.stock_code==stock_code).all()
    for each_pool in pools:
        pool_names += each_pool[0] + ' '
    return pool_names

def get_stock_cap(db, stock_code):
    cap = None
    cap_query = db.session.query(StocksInPool).filter(StocksInPool.code == stock_code).first()
    if cap_query:
        cap = cap_query.cap
    return cap


def stockDataFrameFromTushare(stock_code: str, se: str = None, start_date: str = None, end_date: str = None):
    """
    使用 Tushare API 获取股票数据，返回与数据库格式兼容的 DataFrame

    Args:
        stock_code: 股票代码（如：000001）
        se: 交易所代码（sh/sz），如果不提供则自动判断
        start_date: 开始日期（YYYYMMDD格式）
        end_date: 结束日期（YYYYMMDD格式）

    Returns:
        DataFrame: 包含以下列的股票数据：
            - date: 交易日期 (datetime类型)
            - open: 开盘价
            - high: 最高价
            - low: 最低价
            - close: 收盘价
            - volume: 成交量
            - turnover: 成交额
            - turnover_rate: 换手率
            - shake_rate: 振幅
            - change_rate: 涨跌幅
            - change_amount: 涨跌额

    Example:
        # 使用自动判断交易所
        stock_data = stockDataFrameFromTushare('000001')

        # 指定交易所
        stock_data = stockDataFrameFromTushare('600000', 'sh')

        # 指定日期范围
        stock_data = stockDataFrameFromTushare('000001', start_date='20200101', end_date='20231231')
    """
    from data_processing.data_provider.tushare import Tushare

    # 自动判断交易所
    if se is None:
        if stock_code.startswith('6'):
            se = 'sh'  # 上海证券交易所
        elif stock_code.startswith(('0', '3')):
            se = 'sz'  # 深圳证券交易所
        elif stock_code.startswith('8'):
            se = 'bj'  # 北京证券交易所
        else:
            se = 'sz'  # 默认深圳

    ts_client = Tushare()
    return ts_client.get_stock_dataframe(stock_code, se, start_date, end_date)
