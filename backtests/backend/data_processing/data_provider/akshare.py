import logging
import time
import traceback
from datetime import datetime
from typing import List
import pandas as pd
from dateutil.parser import parser
from tqdm import tqdm
import akshare as ak

from db.models import Stock, StocksInPool
from end_points.common.const.consts import DataBase
from end_points.common.utils.db import update_record
from micro_models.rl_models.training.utils.trademaster.trademaster_utils import get_attr


START_DATE="20250401"

class Akshare:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Akshare, cls).__new__(cls)
        return cls._instance

    def __init__(self, **kwargs):
        # super().__init__(data_source, start_date, end_date, self.time_interval, **kwargs)
        self.time_interval = get_attr(kwargs, "time_interval", None)
        self.data_source = get_attr(kwargs, "data_source", None)
        self.start_date = get_attr(kwargs, "start_date", None)
        self.end_date = get_attr(kwargs, "end_date", None)


        if "adj" in kwargs.keys():
            self.adj = kwargs["adj"]
            print(f"Using {self.adj} method.")
        else:
            self.adj = ""

        if "period" in kwargs.keys():
            self.period = kwargs["period"]
        else:
            self.period = "daily"

    def get_data(self, id) -> pd.DataFrame:
        return ak.stock_zh_a_hist(
            symbol=id,
            period=self.time_interval,
            start_date=self.start_date,
            end_date=self.end_date,
            adjust=self.adj,
        )

    def download_data(
        self, ticker_list: List[str], save_path: str = "./data/dataset.csv"
    ):
        """
        `pd.DataFrame`
            7 columns: A tick symbol, time, open, high, low, close and volume
            for the specified stock ticker
        """
        assert self.time_interval in [
            "daily",
            "weekly",
            "monthly",
        ], "Not supported currently"

        self.ticker_list = ticker_list

        self.dataframe = pd.DataFrame()
        for i in tqdm(ticker_list, total=len(ticker_list)):
            nonstandard_id = self.transfer_standard_ticker_to_nonstandard(i)
            df_temp = self.get_data(nonstandard_id)
            df_temp["tic"] = i
            # df_temp = self.get_data(i)
            self.dataframe = pd.concat([self.dataframe, df_temp])
            # self.dataframe = self.dataframe.append(df_temp)
            # print("{} ok".format(i))
            time.sleep(0.25)

        self.dataframe.columns = [
            "time",
            "code",
            "open",
            "close",
            "high",
            "low",
            "volume",
            "amount",
            "amplitude",
            "pct_chg",
            "change",
            "turnover",
            "tic",
        ]

        self.dataframe.sort_values(by=["time", "tic"], inplace=True)
        self.dataframe.reset_index(drop=True, inplace=True)

        self.dataframe = self.dataframe[
            ["tic", "time", "open", "high", "low", "close", "volume"]
        ]
        # self.dataframe.loc[:, 'tic'] = pd.DataFrame((self.dataframe['tic'].tolist()))
        self.dataframe["time"] = pd.to_datetime(
            self.dataframe["time"], format="%Y-%m-%d"
        )
        self.dataframe["day"] = self.dataframe["time"].dt.dayofweek
        self.dataframe["time"] = self.dataframe.time.apply(
            lambda x: x.strftime("%Y-%m-%d")
        )

        self.dataframe.dropna(inplace=True)
        self.dataframe.sort_values(by=["time", "tic"], inplace=True)
        self.dataframe.reset_index(drop=True, inplace=True)

        self.save_data(save_path)

        print(
            f"Download complete! Dataset saved to {save_path}. \nShape of DataFrame: {self.dataframe.shape}"
        )

    def data_split(self, df, start, end, target_date_col="time"):
        """
        split the dataset into training or testing using time
        :param data: (df) pandas dataframe, start, end
        :return: (df) pandas dataframe
        """
        data = df[(df[target_date_col] >= start) & (df[target_date_col] < end)]
        data = data.sort_values([target_date_col, "tic"], ignore_index=True)
        data.index = data[target_date_col].factorize()[0]
        return data

    def transfer_standard_ticker_to_nonstandard(self, ticker: str) -> str:
        # "600000.XSHG" -> "600000"
        # "000612.XSHE" -> "000612"
        # "600000.SH" -> "600000"
        # "000612.SZ" -> "000612"
        if "." in ticker:
            n, alpha = ticker.split(".")
            # assert alpha in ["XSHG", "XSHE"], "Wrong alpha"
        return n

    def transfer_date(self, time: str) -> str:
        if "-" in time:
            time = "".join(time.split("-"))
        elif "." in time:
            time = "".join(time.split("."))
        elif "/" in time:
            time = "".join(time.split("/"))
        return time

    def addRecord(self, db, class_name, stock_code, se, bind_key, stock_done_record=None):
        print("Start loading record data for: " + stock_code)
        if 's' in stock_code:
            # r = ak.stock_zh_a_daily(symbol=stock_code)
            r = ak.stock_zh_a_hist_tx(symbol=stock_code)
            for index, each_data in r.iterrows():
                date_time = each_data['date']
                query = db.session.query(class_name).filter(class_name.date == date_time).first()
                if query:
                    continue
                if stock_done_record and stock_done_record.starting_date is None:
                    stock_done_record.starting_date = date_time
                    db.session.commit()
                shake_rate = None
                change_rate = None
                change_amount = None
                if index > 0:
                    p_close = r.iloc[index-1]['close']
                    high = each_data['open']
                    low = each_data['low']
                    close = each_data['close']
                    shake_rate = round((high - low) * 100 / p_close, 2)
                    change_amount = close - p_close
                    change_rate = round((close - p_close) * 100 / p_close, 2)
                # volume = int(each_data['volume']/100)
                record = class_name(
                    date=date_time,
                    open=each_data['open'],
                    high=each_data['high'],
                    low=each_data['low'],
                    close=each_data['close'],
                    volume=each_data['amount'],
                    turnover=None,
                    turnover_rate=None,
                    shake_rate=shake_rate,
                    change_rate=change_rate,
                    change_amount=change_amount,
                )
                db.session.add(record)
                db.session.commit()
        else:
            r = ak.stock_zh_a_hist(symbol=stock_code, period='daily')
            for _, each_data in r.iterrows():
                date_time = each_data['日期']
                query = db.session.query(class_name).filter(class_name.date == date_time).first()
                if query:
                    continue
                if stock_done_record and stock_done_record.starting_date is None:
                    stock_done_record.starting_date = date_time
                    db.session.commit()
                record = class_name(
                    date=date_time,
                    open=each_data['开盘'],
                    high=each_data['最高'],
                    low=each_data['最低'],
                    close=each_data['收盘'],
                    volume=each_data['成交量'],
                    turnover=each_data['成交额'],
                    shake_rate=each_data['振幅'],
                    turnover_rate=each_data['换手率'],
                    change_rate=each_data['涨跌幅'],
                    change_amount=each_data['涨跌额'],
                )
                db.session.add(record)
        db.session.commit()
        print("Add record success for: " + stock_code)

    def updateZJ(self, db, class_name, stock_code, se, dates_to_fill):
        print("Start loading ZJ data for: " + stock_code)
        r = ak.stock_individual_fund_flow(stock=stock_code, market=se)
        updated = False
        for each_data in r:
            date_time = each_data.get('t')
            compare_date = parser().parse(date_time)
            if compare_date in dates_to_fill:
                query = db.session.query(class_name).filter(class_name.date == date_time).first()
                if not query:
                    continue
                items = ['jlrl', 'zljlrl', 'hyjlrl']
                update_record(query, items, each_data)
                updated = True
        db.session.commit()
        if updated == True:
            the_stock = db.session.query(Stock).filter(Stock.code == stock_code).first()
            the_stock.updated_at = datetime.now()
            db.session.commit()
            print("ZJ update success for stock: " + stock_code)
        else:
            print("No ZJ data to update for stock:" + stock_code)

    def get_latest_date(self, stock_code, se, bind_key=DataBase.stocks, ):
        symbol = se+stock_code
        r = ak.stock_zh_a_daily(symbol=symbol, start_date=START_DATE)
        # ak.stock_individual_spot_xq(symbol="SZ000034")
        latest_date = r.iloc[-1]['date']
        return latest_date

    def get_today_open(self, stock_code):
        if 's' in stock_code:
            stock_url = 'http://api.mairuiapi.com/zs/sssj/'
        else:
            stock_url = 'http://api.mairuiapi.com/hsrl/ssjy/'
        r = self.get_my_data(stock_url, stock_code, None)
        open_price = float(r.get('o'))
        lastest_date = r.get('t')
        # lastest_date = parser().parse(lastest_date)
        return lastest_date, open_price

    def get_stock_cap(self, stock_code):
        r = ak.stock_individual_info_em(symbol=stock_code)
        cap = round(float(r.get('sz')) / 100000000, 2)
        pe = float(r.get('pe'))
        return cap, pe

    def update_stocks_in_pool(db, data_tool, all_stocks):
        print("Start updating stocks in pool!")
        try:
            stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
            for each_stock in all_stocks:
                print("Updating stock: {} ...".format(each_stock))
                cap, pe = data_tool.get_stock_cap(each_stock)
                record = db.session.query(StocksInPool).filter(StocksInPool.code == each_stock).scalar()
                if record:
                    record.cap = cap
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
