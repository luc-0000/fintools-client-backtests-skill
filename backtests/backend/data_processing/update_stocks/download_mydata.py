import logging
import traceback
from datetime import datetime, timedelta, date
from time import sleep
import pandas as pd
import akshare as ak

from data_processing.update_stocks.download_mydata_util import create_stock_table
from db.models import UpdatingStock, Stock, StocksInPool
from end_points.common.const.consts import DataBase
from end_points.get_stock.operations.get_stock_utils import get_stock_cap
from end_points.common.utils.db import get_bind_session

ZJ_START_DATE = pd.Timestamp(2010, 1, 1, 0)

def update_stocks_for_bind(db, data_tool, all_stocks, bind_key):
    print("Start updating stocks for database {}!".format(bind_key))
    for stock_code, se in all_stocks:
        update_stock_record(db, data_tool, stock_code, se, bind_key)
        print(datetime.now())
    print("Stocks updating done for database {}!".format(bind_key))
    return


def update_stock_record(db, data_tool, stock_code, se, bind_key, repeat_time=10):
    print("Start checking status for: " + stock_code)
    req_update = None  # Initialize req_update
    for i in range(repeat_time):
        sleep(0.1)
        try:
            req_update = need_update(db, data_tool, stock_code, se, bind_key)
            if req_update != None:
                break
        except Exception as e:
            print(e)
            db.session.rollback()

    # If all retries failed, assume we need to update
    if req_update is None:
        print(f"Could not check update status for {stock_code}, will attempt to create/update table")
        req_update = True

    if req_update == False:
        print("Record data is up to date for stock:" + stock_code)
        return

    stock_class = create_stock_table(db, stock_code, bind_key)
    updated = data_tool.addRecord(db, stock_class, stock_code, se, bind_key)
    if updated == True:
        the_stock = db.session.query(Stock).filter(Stock.code == stock_code).first()
        the_stock.updated_at = datetime.now()
        db.session.commit()
    return

def need_update(db, data_tool, stock_code, se, bind_key):
    latest_date = data_tool.get_latest_date(stock_code, se)
    stock_class = create_stock_table(db, stock_code, bind_key)

    try:
        with get_bind_session(db, bind_key) as session:
            row_exist = session.query(stock_class).filter(stock_class.date == latest_date).first()
    except Exception as e:
        # Table might not exist yet, so we need to update
        print(f"Table {stock_code} does not exist or error querying: {e}")
        return True

    updating = db.session.query(UpdatingStock).filter(UpdatingStock.stock_code == stock_code).first()
    if row_exist and not updating:
        req_update = False
    else:
        req_update = True
    return req_update

def update_stocks_jlrl(db, data_tool, all_stocks, bind_key):
    print("Start updating jlrl for database {}!".format(bind_key))
    for stock_code, se in all_stocks:
        stock_class = create_stock_table(db, stock_code, bind_key)
        data_tool.updateZJ_All(db, stock_class, stock_code, se)
        print(datetime.now())
    print("JLRL updating done for database {}!".format(bind_key))
    return


def remove_staled_stocks_in_pool(db, all_stocks, bind_key=DataBase.stocks):
    print("Start updating stocks in pool!")
    try:
        engine = db.get_engine(bind_key=bind_key)
        engine.get_tables()
        for each_stock in all_stocks:
            print("Updating stock: {} ...".format(each_stock))
            cap, pe = get_stock_cap(each_stock)
            record = db.session.query(StocksInPool).filter(StocksInPool.code == each_stock).scalar()
            if record:
                record.cap = cap
                record.pe = pe
            else:
                new_record = StocksInPool(code=each_stock, cap=cap, pe=pe)
                db.session.add(new_record)
            db.session.commit()
        print("Finished update stocks in pool!")
        print(datetime.now())
    except Exception as e:
        err = traceback.format_exc()
        logging.error(err, 'error')
        db.session.rollback()
    return

def update_stocks_in_pool(db, data_tool, all_stocks):
    print("Start updating stocks in pool!")
    try:
        for each_stock, se in all_stocks:
            print("Updating stock: {} ...".format(each_stock))
            cap, pe = data_tool.get_stock_cap(each_stock, se)
            record = db.session.query(StocksInPool).filter(StocksInPool.code == each_stock).scalar()
            if record:
                if cap is not None:
                    record.cap = cap
                if pe is not None:
                    record.pe = pe
            else:
                new_record = StocksInPool(
                    code=each_stock,
                    cap=cap,
                    pe=pe,
                )
                db.session.add(new_record)
            db.session.commit()
        print("Finished update stocks in pool!")
        print(datetime.now())
    except Exception as e:
        err = traceback.format_exc()
        logging.error(err, 'error')
        db.session.rollback()
    return

def update_future_index(db):
    data = ak.futures_hist_em(symbol="沪深主连")
    return

def update_a50(db):
    # data = ak.index_option_300etf_qvix()
    # data2 =  ak.index_news_sentiment_scope()
    # index_data = stockDataFrame(db, 'sh000300')
    # dates_ary = index_data.date
    # dates_ary = [x.strftime("%Y%m%d") for x in dates_ary]
    # start_date = pd.Timestamp(2001, 1, 1, 0)
    start_date = datetime(2012, 1, 1)
    end_date = datetime.now() + timedelta(days=1)
    date_ary = get_dates_ary(start_date, end_date)
    for each_date in date_ary:
        # start_date = datetime(2013, 1, 1)
        each_date='20250301'
        a50_data = ak.futures_settlement_price_sgx(each_date)
        a50_data = a50_data[a50_data['COM'].str.startswith('CN')]

        print("")
    return

def get_dates_ary(start_date, end_date):
    new_date = start_date
    dates_ary = []
    while new_date <= end_date:
        new_date += timedelta(days=1)
        dates_ary.append(new_date.strftime("%Y%m%d"))
    return dates_ary
