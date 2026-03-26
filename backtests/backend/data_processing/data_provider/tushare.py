import os
import time
from datetime import datetime, timedelta
from typing import List, Dict
import numpy as np
import pandas as pd
from dateutil.parser import parser
from dateutil.relativedelta import relativedelta
from tqdm import tqdm
import tushare as ts


import dotenv

from db.models import Stock
from end_points.common.utils.db import update_record, get_bind_session

dotenv.load_dotenv()

class Tushare:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Tushare, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        time_interval='1d',
        **kwargs,
    ):
        if not self._initialized:
            # super().__init__(data_source, start_date, end_date, time_interval, **kwargs)
            ts_token = os.getenv('TUSHARE_TOKEN')
            self.token = ts_token
            self.time_interval = time_interval
            self.pro = ts.pro_api(ts_token)
            ts.set_token(ts_token)
            # self.pro = ts.pro_api()
            if "adj" in kwargs.keys():
                self.adj = kwargs["adj"]
                print(f"Using {self.adj} method.")
            else:
                self.adj = None
            Tushare._initialized = True

    def get_data(self, id) -> pd.DataFrame:
        # df1 = ts.pro_bar(ts_code=id, start_date=self.start_date,end_date='20180101')
        # dfb=pd.concat([df, df1], ignore_index=True)
        # print(dfb.shape)
        return ts.pro_bar(
            ts_code=id,
            start_date=self.start_date,
            end_date=self.end_date,
            adj=self.adj,
        )

    def download_data(self, ticker_list: List[str]):
        assert self.time_interval == "1d", "Not supported currently"

        self.ticker_list = ticker_list
        ts.set_token(self.token)

        self.dataframe = pd.DataFrame()
        for i in tqdm(ticker_list, total=len(ticker_list)):
            # nonstandard_id = self.transfer_standard_ticker_to_nonstandard(i)
            # df_temp = self.get_data(nonstandard_id)
            df_temp = self.get_data(i)
            # self.dataframe = self.dataframe.append(df_temp)
            self.dataframe = pd.concat([self.dataframe, df_temp])
            # print("{} ok".format(i))
            time.sleep(0.25)

        self.dataframe.columns = [
            "tic",
            "time",
            "open",
            "high",
            "low",
            "close",
            "pre_close",
            "change",
            "pct_chg",
            "volume",
            "amount",
        ]
        self.dataframe.sort_values(by=["time", "tic"], inplace=True)
        self.dataframe.reset_index(drop=True, inplace=True)

        self.dataframe = self.dataframe[
            ["tic", "time", "open", "high", "low", "close", "volume"]
        ]
        # self.dataframe.loc[:, 'tic'] = pd.DataFrame((self.dataframe['tic'].tolist()))
        self.dataframe["time"] = pd.to_datetime(self.dataframe["time"], format="%Y%m%d")
        self.dataframe["day"] = self.dataframe["time"].dt.dayofweek
        self.dataframe["time"] = self.dataframe.time.apply(
            lambda x: x.strftime("%Y-%m-%d")
        )

        self.dataframe.dropna(inplace=True)
        self.dataframe.sort_values(by=["time", "tic"], inplace=True)
        self.dataframe.reset_index(drop=True, inplace=True)

        # self.save_data(save_path)

        print(
            f"Download complete! \nShape of DataFrame: {self.dataframe.shape}"
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
        # "600000.XSHG" -> "600000.SH"
        # "000612.XSHE" -> "000612.SZ"
        n, alpha = ticker.split(".")
        assert alpha in ["XSHG", "XSHE"], "Wrong alpha"
        if alpha == "XSHG":
            nonstandard_ticker = n + ".SH"
        elif alpha == "XSHE":
            nonstandard_ticker = n + ".SZ"
        return nonstandard_ticker

    def save_data(self, path):
        if ".csv" in path:
            path = path.split("/")
            filename = path[-1]
            path = "/".join(path[:-1] + [""])
        else:
            if path[-1] == "/":
                filename = "dataset.csv"
            else:
                filename = "/dataset.csv"

        os.makedirs(path, exist_ok=True)
        self.dataframe.to_csv(path + filename, index=False)

    def load_data(self, path):
        assert ".csv" in path  # only support csv format now
        self.dataframe = pd.read_csv(path)
        columns = self.dataframe.columns
        assert (
            "tic" in columns and "time" in columns and "close" in columns
        )  # input file must have "tic","time" and "close" columns

    def addRecord(self, db, class_name, stock_code, se, bind_key, stock_done_record=None):
        print("Start loading record data for: " + stock_code + '......')
        updated = False

        with get_bind_session(db, bind_key) as session:
            if 's' in stock_code:
                stock_code = stock_code[2:]
                symbol = stock_code + '.' + se.upper()
                df = self.pro.index_daily(ts_code=symbol).sort_values(by=['trade_date'])
                for index, each_data in df.iterrows():
                    date_time = each_data['trade_date']
                    # date_time = '1992-10-20 00:00:00'
                    query = session.query(class_name).filter(class_name.date == date_time).first()
                    if query:
                        continue
                    if stock_done_record and stock_done_record.starting_date is None:
                        stock_done_record.starting_date = date_time
                        db.session.commit()
                    shake_rate = round((each_data.high - each_data.low) * 100 / each_data.pre_close, 2)
                    df2 = self.pro.index_dailybasic(ts_code=symbol, trade_date=date_time).squeeze()
                    record = class_name(
                        date=date_time,
                        open=each_data.open,
                        high=each_data.high,
                        low=each_data.low,
                        close=each_data.close,
                        volume=each_data.vol,
                        turnover=each_data.amount*1000,
                        turnover_rate=df2.turnover_rate if df2.empty == False else None,
                        shake_rate=shake_rate,
                        change_rate=each_data.pct_chg,
                        change_amount=each_data.change,
                    )
                    session.add(record)
                    session.commit()
                    updated = True
            else:
                symbol = stock_code + '.' + se.upper()
                # df = self.pro.daily(ts_code=symbol).sort_values(by=['trade_date'])
                df = ts.pro_bar(ts_code=symbol, factors=['tor', 'vr'])
                df2 = self.pro.moneyflow(ts_code=symbol)
                df = df.merge(df2, on='trade_date')
                df['zl'] = df.buy_elg_amount - df.sell_elg_amount + df.buy_lg_amount - df.sell_lg_amount
                df['jlrl'] = df.net_mf_vol * 100 / df.vol
                df['zljlrl'] = df.zl * 1000 / df.amount
                df = df.sort_values(by=['trade_date']).round({'jlrl': 2, 'zljlrl': 2})
                # df.fillna(0)
                df = df.replace({np.nan: None})#replace all nan to None, and colume dtype became object
                for _, each_data in df.iterrows():
                    date_time = each_data['trade_date']
                    query = session.query(class_name).filter(class_name.date == date_time).first()
                    if query:
                        continue
                    if stock_done_record and stock_done_record.starting_date is None:
                        stock_done_record.starting_date = date_time
                        db.session.commit()
                    if each_data.high is None or each_data.low is None or each_data.pre_close is None:
                        shake_rate = None
                    else:
                        shake_rate = round((each_data.high - each_data.low) * 100 / each_data.pre_close, 2)
                    # df2 = self.pro.daily_basic(ts_code=symbol, trade_date=date_time).squeeze()
                    record = class_name(
                        date=date_time,
                        open=each_data.open,
                        high=each_data.high,
                        low=each_data.low,
                        close=each_data.close,
                        volume=each_data.vol,
                        turnover=each_data.amount * 1000,
                        turnover_rate=each_data.turnover_rate,
                        shake_rate=shake_rate,
                        jlrl=each_data.jlrl,
                        zljlrl=each_data.zljlrl,
                        change_rate=each_data.pct_chg,
                        change_amount=each_data.change,
                    )
                    session.add(record)
                    updated = True
            session.commit()
            print("Add record success for: " + stock_code)

        return updated

    def updateZJ(self, db, class_name, stock_code, se, dates_to_fill):
        print("Start loading ZJ data for: " + stock_code)
        symbol = stock_code + '.' + se.upper()
        df = self.pro.moneyflow(ts_code=symbol)
        df['zl'] = df.buy_elg_amount - df.sell_elg_amount + df.buy_lg_amount - df.sell_lg_amount
        df2 = self.pro.daily(ts_code=symbol)
        df = df.merge(df2, on='trade_date')
        df_new = pd.DataFrame([])
        df_new['date'] = df['trade_date']
        df_new['jlrl'] = df.net_mf_vol*100/df.vol
        df_new['zljlrl'] = df.zl * 1000 / df.amount

        df_new = df_new.sort_values(by=['date']).round({'jlrl': 2, 'zljlrl': 2})
        updated = False
        for _, each_data in df_new.iterrows():
            date_time = each_data['date']
            compare_date = parser().parse(date_time)
            if compare_date in dates_to_fill and each_data.isna().any() == False:
                query = db.session.query(class_name).filter(class_name.date == date_time).first()
                if not query:
                    continue
                items = ['jlrl', 'zljlrl']
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

    def updateZJ_All(self, db, class_name, stock_code, se):
        print("Start loading ZJ data for: " + stock_code)
        symbol = stock_code + '.' + se.upper()
        df = self.pro.moneyflow(ts_code=symbol)
        df['zl'] = df.buy_elg_amount - df.sell_elg_amount + df.buy_lg_amount - df.sell_lg_amount
        df2 = self.pro.daily(ts_code=symbol)
        df = df.merge(df2, on='trade_date')
        df_new = pd.DataFrame([])
        df_new['date'] = df['trade_date']
        df_new['jlrl'] = df.net_mf_vol*100/df.vol
        df_new['zljlrl'] = df.zl * 1000 / df.amount

        df_new = df_new.sort_values(by=['date']).round({'jlrl': 2, 'zljlrl': 2})
        updated = False
        for _, each_data in df_new.iterrows():
            date_time = each_data['date']
            if each_data.isna().any() == False:
                query = db.session.query(class_name).filter(class_name.date == date_time).first()
                if not query:
                    continue
                items = ['jlrl', 'zljlrl']
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


    def get_latest_date(self, stock_code, se):
        if 's' in stock_code:
            stock_code = stock_code[2:]
        symbol = stock_code + '.' + se.upper()
        r = ts.realtime_quote(ts_code=symbol).squeeze()
        latest_date = r.DATE
        if r.PRICE == r.HIGH == 0:
            r_last = self.pro.daily(ts_code=symbol, start_date=self.get_start_date(6)).iloc[0]
            latest_date = parser().parse(r_last.trade_date)
        return latest_date

    def get_stock_cap(self, stock_code, se):
        start_date = self.get_start_date()
        cap = None
        pe = None
        if 's' in stock_code:
            stock_code = stock_code[2:]
            symbol = stock_code + '.' + se.upper()
            r = self.pro.index_dailybasic(ts_code=symbol, start_date=start_date)
        else:
            symbol = stock_code + '.' + se.upper()
            r = self.pro.daily_basic(ts_code=symbol, start_date=start_date)
        if len(r) > 0:
            r = r.iloc[0]
            if r.total_mv is not None and np.isnan(r.total_mv) == False:
                cap = round(r.total_mv/10000, 2)
            if r.pe_ttm is not None and np.isnan(r.pe_ttm) == False:
                pe = r.pe_ttm
        return cap, pe

    def get_start_date(self, months=1):
        now = datetime.now()
        one_month_ago = now - relativedelta(months=months)
        start_date = one_month_ago.strftime('%Y%m%d')
        return start_date

    def get_today_open(self, stock_code, se):
        symbol = stock_code + '.' + se.upper()
        # symbol = '300280.SZ'
        r = ts.realtime_quote(ts_code=symbol,src='dc').squeeze()
        latest_date = parser().parse(r.DATE)
        open_price = float(r.OPEN)
        if r.PRICE == r.HIGH == 0:
            r_last = self.pro.daily(ts_code=symbol, start_date=self.get_start_date(6)).iloc[0]
            latest_date = parser().parse(r_last.trade_date)
            open_price = float(r_last.open)
        return latest_date, open_price

    def get_chips(self, stock_code, se):
        symbol = stock_code + '.' + se.upper()
        chips_df = self.pro.cyq_perf(ts_code=symbol)
        chips_df['date'] = pd.to_datetime(chips_df['trade_date'])
        return chips_df


    def get_stock_info(self, symbol: str) -> Dict:
        """
        获取股票基本信息

        Args:
            symbol: 股票代码

        Returns:
            Dict: 股票基本信息
        """
        try:
            ts_code = self._normalize_symbol(symbol)

            # 获取股票基本信息
            print(f"🔍 [股票代码追踪] 调用 Tushare API stock_basic，传入参数: ts_code='{ts_code}'")
            basic_info = self.pro.stock_basic(
                ts_code=ts_code,
                fields='ts_code,symbol,name,area,industry,market,list_date'
            )

            if basic_info is not None and not basic_info.empty:
                print(f"🔍 [股票代码追踪] 返回数据内容: {basic_info.to_dict('records')}")

            if basic_info is not None and not basic_info.empty:
                info = basic_info.iloc[0]
                return {
                    'symbol': symbol,
                    'ts_code': info['ts_code'],
                    'name': info['name'],
                    'area': info.get('area', ''),
                    'industry': info.get('industry', ''),
                    'market': info.get('market', ''),
                    'list_date': info.get('list_date', ''),
                    'source': 'tushare'
                }
            else:
                return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'unknown'}

        except Exception as e:
            print(f"❌ 获取{symbol}股票信息失败: {e}")
            return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'unknown'}

    def get_stock_daily(self, symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        获取股票日线数据

        Args:
            symbol: 股票代码（如：000001.SZ）
            start_date: 开始日期（YYYYMMDD）
            end_date: 结束日期（YYYYMMDD）

        Returns:
            DataFrame: 日线数据
        """

        try:
            # 标准化股票代码
            ts_code = self._normalize_symbol(symbol)
            if end_date is None:
                end_date = datetime.now().strftime('%Y%m%d')
            else:
                end_date = end_date.replace('-', '')

            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            else:
                start_date = start_date.replace('-', '')

            print(f"🔄 从Tushare获取{ts_code}数据 ({start_date} 到 {end_date})...")

            try:
                data = self.pro.daily(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date
                )

            except Exception as api_error:
                print(api_error)
                raise api_error

            if data is not None and not data.empty:
                # 数据预处理
                data = data.sort_values('trade_date')
                data['trade_date'] = pd.to_datetime(data['trade_date'])

                # 计算前复权价格（基于pct_chg重新计算连续价格）
                # data = self._calculate_forward_adjusted_prices(data)

                print(f"🔍 [Tushare详细日志] get_stock_daily 执行成功，返回数据")
                return data
            else:
                print(f"⚠️ Tushare返回空数据: {ts_code}")
                return pd.DataFrame()

        except Exception as e:
            print(f"❌ 获取{symbol}数据失败: {e}")
            import traceback
            print(f"❌ [Tushare详细日志] 异常堆栈: {traceback.format_exc()}")
            return pd.DataFrame()

    def get_stock_cash_flow(self, symbol: str, start_date:str, end_date:str) -> Dict:
        try:
            ts_code = self._normalize_symbol(symbol)
            start_date = start_date.replace('-', '')
            end_date = end_date.replace('-', '')
            cash_flow_data = self.pro.moneyflow(ts_code=ts_code, start_date=start_date, end_date=end_date)

            if cash_flow_data is not None and not cash_flow_data.empty:
                cash_flow_data = cash_flow_data.iloc[0]
                cash_flow_dict = cash_flow_data.to_dict()
                return cash_flow_dict
            else:
                return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'unknown'}

        except Exception as e:
            print(f"❌ 获取{symbol}股票信息失败: {e}")
            return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'unknown'}

    def _normalize_symbol(self, symbol: str) -> str:

        # 移除可能的前缀
        symbol = symbol.replace('sh.', '').replace('sz.', '')

        if '.' in symbol:
            return symbol

        # 根据代码判断交易所
        if symbol.startswith('6'):
            result = f"{symbol}.SH"  # 上海证券交易所
            return result
        elif symbol.startswith(('0', '3')):
            result = f"{symbol}.SZ"  # 深圳证券交易所
            return result
        elif symbol.startswith('8'):
            result = f"{symbol}.BJ"  # 北京证券交易所
            return result
        else:
            # 默认深圳
            result = f"{symbol}.SZ"
            return result

    def get_stock_tech(self, symbol: str, start_date:str, end_date:str) -> Dict:
        try:
            ts_code = self._normalize_symbol(symbol)
            start_date = start_date.replace('-', '')
            end_date = end_date.replace('-', '')
            tech_data = self.pro.stk_factor(ts_code=ts_code, start_date=start_date, end_date=end_date)

            if tech_data is not None and not tech_data.empty:
                tech_data = tech_data.iloc[0]
                tech_dict = tech_data.to_dict()
                return tech_dict
            else:
                return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'unknown'}

        except Exception as e:
            print(f"❌ 获取{symbol}股票信息失败: {e}")
            return {'symbol': symbol, 'name': f'股票{symbol}', 'source': 'unknown'}

    def get_financial_data(self, symbol: str) -> Dict:
        try:
            ts_code = self._normalize_symbol(symbol)

            financials = {}
            end_date = datetime.now().date().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(weeks=30)).strftime('%Y%m%d')

            # 获取资产负债表
            try:
                balance_sheet = self.pro.balancesheet(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,total_assets,total_liab,total_hldr_eqy_exc_min_int,money_cap,trad_asset,st_borr,undistr_porfit,accounts_receiv,inventories,acct_payable'
                )
                financials['balance_sheet'] = balance_sheet.to_dict(
                    'records') if balance_sheet is not None and not balance_sheet.empty else []
            except Exception as e:
                print(e)
                financials['balance_sheet'] = []

            # 获取利润表
            try:
                income_statement = self.pro.income(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,total_revenue,total_cogs,operate_profit,total_profit,n_income,net_after_nr_lp_correct,rd_exp,basic_eps,diluted_eps,total_profit'
                )
                financials['income_statement'] = income_statement.to_dict(
                    'records') if income_statement is not None and not income_statement.empty else []
            except Exception as e:
                print(f"⚠️ 获取利润表失败: {e}")
                financials['income_statement'] = []

            # 获取现金流量表
            try:
                cash_flow = self.pro.cashflow(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,net_profit,finan_exp,c_fr_sale_sg,c_paid_goods_s,n_cashflow_act,n_cash_flows_fnc_act,free_cashflow,n_cashflow_inv_act'
                )
                financials['cash_flow'] = cash_flow.to_dict('records') if cash_flow is not None and not cash_flow.empty else []
            except Exception as e:
                print(f"⚠️ 获取现金流量表失败: {e}")
                financials['cash_flow'] = []
            return financials

        except Exception as e:
            print(f"❌ 获取{symbol}财务数据失败: {e}")
            return {}

    def update_all_stocks_list(self, db):
        """
        使用 Tushare API 更新所有股票列表到数据库
        功能与 Mairui 的 update_all_stocks_list 相同
        """
        print("Start updating all stocks list!")
        try:
            # 获取所有股票列表
            stock_list = self.pro.stock_basic(
                exchange='',
                list_status='L',  # L上市 D退市 P暂停上市
                fields='ts_code,symbol,name,area,industry,market,market,list_date'
            )

            if stock_list is None or stock_list.empty:
                print("⚠️ 未获取到股票列表")
                return

            print(f"📊 获取到 {len(stock_list)} 只股票")

            # 遍历股票列表，更新到数据库
            for _, each_stock in stock_list.iterrows():
                ts_code = each_stock.get('ts_code')  # 如: 000001.SZ
                name = each_stock.get('name')

                # 解析交易所和代码
                if '.' in ts_code:
                    clean_code, suffix = ts_code.split('.')
                    # 将后缀转换为小写 (.SH -> sh, .SZ -> sz)
                    se = suffix.lower()
                else:
                    clean_code = ts_code
                    # 根据代码推断交易所
                    if clean_code.startswith('6'):
                        se = 'sh'
                    elif clean_code.startswith(('0', '3')):
                        se = 'sz'
                    else:
                        se = 'unknown'

                # 检查数据库中是否已存在该股票
                record = db.session.query(Stock).filter(Stock.code == clean_code).scalar()

                if record:
                    # 记录存在，更新名称和交易所
                    if record.name != name:
                        old_name = record.name
                        record.name = name
                        print("Updated stock: {} {} with new name: {}".format(clean_code, old_name, name))
                    if record.se != se:
                        old_se = record.se
                        record.se = se
                        print("Updated stock: {} {} {} with new se: {}".format(clean_code, record.name, old_se, se))
                else:
                    # 记录不存在，添加新记录
                    new_record = Stock(
                        code=clean_code,
                        name=name,
                        se=se,
                        type='s',
                    )
                    db.session.add(new_record)
                    print("Added new stock: {} {}".format(clean_code, name))

                db.session.commit()

            print("Finished update all stocks list!")
            print(datetime.now())

        except Exception as e:
            import traceback
            err = traceback.format_exc()
            print(f"❌ Error updating stocks list: {err}")
            db.session.rollback()
            raise e
        return

    def get_stock_dataframe(self, stock_code: str, se: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        获取股票历史K线数据，返回与数据库格式兼容的DataFrame

        Args:
            stock_code: 股票代码（如：000001）
            se: 交易所代码（sh/sz）
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
        """
        # 构造完整的股票代码
        symbol = stock_code + '.' + se.upper()

        # 设置默认日期范围（默认获取最近3年数据）
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y%m%d')

        try:
            # 获取日线数据
            df = self.pro.daily(
                ts_code=symbol,
                start_date=start_date,
                end_date=end_date
            )

            # 获取日线基本面数据（包含换手率）
            df_basic = self.pro.daily_basic(
                ts_code=symbol,
                start_date=start_date,
                end_date=end_date,
                fields='ts_code,trade_date,turnover_rate'
            )

            # 合并数据
            if df_basic is not None and not df_basic.empty:
                df = df.merge(df_basic, on=['ts_code', 'trade_date'], how='left')

            if df is None or df.empty:
                print(f"⚠️ 未获取到股票数据: {symbol}")
                return pd.DataFrame()

            # 计算振幅 (shake_rate)
            # shake_rate = (high - low) / pre_close * 100
            df['shake_rate'] = ((df['high'] - df['low']) / df['pre_close'] * 100).round(2)

            # 转换日期格式为datetime（重要：后续计算需要对比datetime）
            df['date'] = pd.to_datetime(df['trade_date'])

            # 重命名列以匹配数据库格式
            df = df.rename(columns={
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'vol': 'volume',
                'amount': 'turnover',
                'pct_chg': 'change_rate',
                'change': 'change_amount'
            })

            # 选择需要的列（与数据库格式一致）
            columns_to_keep = [
                'date', 'open', 'high', 'low', 'close', 'volume',
                'turnover', 'turnover_rate', 'shake_rate',
                'change_rate', 'change_amount'
            ]

            result_df = df[columns_to_keep].copy()

            # 按日期排序
            result_df = result_df.sort_values('date').reset_index(drop=True)

            print(f"✅ 成功获取 {symbol} 数据，共 {len(result_df)} 条记录")
            return result_df

        except Exception as e:
            print(f"❌ 获取股票 {symbol} 数据失败: {e}")
            import traceback
            print(f"❌ 异常堆栈: {traceback.format_exc()}")
            return pd.DataFrame()

    # def _calculate_forward_adjusted_prices(self, data: pd.DataFrame) -> pd.DataFrame:
    #     """
    #     基于pct_chg计算前复权价格
    #
    #     Tushare的daily接口返回除权价格，在除权日会出现价格跳跃。
    #     使用pct_chg（涨跌幅）重新计算连续的前复权价格，确保价格序列的连续性。
    #
    #     Args:
    #         data: 包含除权价格和pct_chg的DataFrame
    #
    #     Returns:
    #         DataFrame: 包含前复权价格的数据
    #     """
    #     if data.empty or 'pct_chg' not in data.columns:
    #         print("⚠️ 数据为空或缺少pct_chg列，无法计算前复权价格")
    #         return data
    #
    #     try:
    #         # 复制数据避免修改原始数据
    #         adjusted_data = data.copy()
    #
    #         # 确保数据按日期排序
    #         adjusted_data = adjusted_data.sort_values('trade_date').reset_index(drop=True)
    #
    #         # 保存原始价格列（用于对比）
    #         adjusted_data['close_raw'] = adjusted_data['close'].copy()
    #         adjusted_data['open_raw'] = adjusted_data['open'].copy()
    #         adjusted_data['high_raw'] = adjusted_data['high'].copy()
    #         adjusted_data['low_raw'] = adjusted_data['low'].copy()
    #
    #         # 从最新的收盘价开始，向前计算前复权价格
    #         # 使用最后一天的收盘价作为基准
    #         latest_close = float(adjusted_data.iloc[-1]['close'])
    #
    #         # 计算前复权收盘价
    #         adjusted_closes = [latest_close]
    #
    #         # 从倒数第二天开始向前计算
    #         for i in range(len(adjusted_data) - 2, -1, -1):
    #             pct_change = float(adjusted_data.iloc[i + 1]['pct_chg']) / 100.0  # 转换为小数
    #
    #             # 前一天的前复权收盘价 = 今天的前复权收盘价 / (1 + 今天的涨跌幅)
    #             prev_close = adjusted_closes[0] / (1 + pct_change)
    #             adjusted_closes.insert(0, prev_close)
    #
    #         # 更新收盘价
    #         adjusted_data['close'] = adjusted_closes
    #
    #         # 计算其他价格的调整比例
    #         for i in range(len(adjusted_data)):
    #             if adjusted_data.iloc[i]['close_raw'] != 0:  # 避免除零
    #                 # 计算调整比例
    #                 adjustment_ratio = adjusted_data.iloc[i]['close'] / adjusted_data.iloc[i]['close_raw']
    #
    #                 # 应用调整比例到其他价格
    #                 adjusted_data.iloc[i, adjusted_data.columns.get_loc('open')] = adjusted_data.iloc[i]['open_raw'] * adjustment_ratio
    #                 adjusted_data.iloc[i, adjusted_data.columns.get_loc('high')] = adjusted_data.iloc[i]['high_raw'] * adjustment_ratio
    #                 adjusted_data.iloc[i, adjusted_data.columns.get_loc('low')] = adjusted_data.iloc[i]['low_raw'] * adjustment_ratio
    #
    #         # 添加标记表示这是前复权价格
    #         adjusted_data['price_type'] = 'forward_adjusted'
    #
    #         return adjusted_data
    #
    #     except Exception as e:
    #         print(f"❌ 前复权价格计算失败: {e}")
    #         return data
