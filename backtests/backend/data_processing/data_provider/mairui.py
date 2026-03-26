import json
import logging
import os
import traceback
from datetime import datetime, date
from time import sleep
import requests
from dateutil.parser import parser

from db.models import Stock, StockIndex
from end_points.common.const.consts import DataBase
from end_points.common.utils.db import update_record
from end_points.common.utils.http import APIException
import dotenv
dotenv.load_dotenv()

md_licence = os.getenv('MAIRUI_TOKEN')

class Mairui:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Mairui, cls).__new__(cls)
        return cls._instance

    def __init__(self, **kwargs,):
        if "period" in kwargs.keys():
            self.period = kwargs["period"]
        else:
            self.period = "daily"

    def addRecord(self, db, class_name, stock_code, se, bind_key, stock_done_record=None):
        time_unit = self.get_time_unit(bind_key)
        updated = False
        print("Start loading record data for: " + stock_code)
        if 's' in stock_code:
            stock_url = 'http://api.mairuiapi.com/hsindex/history/'
            stock_full = stock_code + '.' + se.upper()
            stock_code = stock_code[2:]
            time_unit = 'd'
            r = self.get_my_data(stock_url, stock_code, time_unit)
            for each_data in r:
                date_time = each_data.get('t').split(' ')[0] + ' 00:00:00'
                query = db.session.query(class_name).filter(class_name.date == date_time).first()
                if query:
                    continue
                if stock_done_record and stock_done_record.starting_date is None:
                    stock_done_record.starting_date = date_time
                    db.session.commit()
                change_rate = None
                shake_rate = None
                change_amount = None
                close = each_data.get('c')
                p_close = each_data.get('pc')
                high = each_data.get('h')
                low = each_data.get('l')
                if close and p_close and high and low:
                    shake_rate = round((high-low)*100/p_close, 2)
                    change_rate = round((close-p_close)*100/p_close, 2)
                    change_amount = close - p_close
                record = class_name(
                    date=date_time,
                    open=each_data.get('o'),
                    high=each_data.get('h'),
                    low=each_data.get('l'),
                    close=each_data.get('c'),
                    volume=each_data.get('v'),
                    turnover=each_data.get('a'),
                    shake_rate=shake_rate,
                    change_rate=change_rate,
                    change_amount=change_amount,
                )
                db.session.add(record)
                updated = True
            db.session.commit()
        else:
            stock_url = 'http://api.mairuiapi.com/hsrl/ssjy/'
            # stock_url = 'https://api.mairuiapi.com/hsstock/history/'
            stock_full = stock_code + '.' + se.upper()
            r = [self.get_my_data(stock_url, stock_code, None)]
            for each_data in r:
                date_time = each_data.get('t').split(' ')[0] + ' 00:00:00'
                query = db.session.query(class_name).filter(class_name.date == date_time).first()
                if query:
                    continue
                if stock_done_record and stock_done_record.starting_date is None:
                    stock_done_record.starting_date = date_time
                    db.session.commit()
                # get jlrl and zljlrl
                zj_stock_url = 'http://api.mairuiapi.com/hsstock/history/transaction/'
                zj_r = self.get_my_data(zj_stock_url, stock_code, None)[0]
                if zj_r.get('t') != date_time:
                    raise Exception('Mydata get jlrl and zljlrl failed!')
                jlr = zj_r.get('zmbtdcjl') + zj_r.get('zmbddcjl') + zj_r.get('zmbzdcjl') + zj_r.get('zmbxdcjl') - zj_r.get('zmstdcjl') - zj_r.get('zmsddcjl') - zj_r.get('zmszdcjl') - zj_r.get('zmsxdcjl')
                jlrl = round(jlr * 100 / each_data.get('v'), 2)
                zljlrl = round((zj_r.get('zmbtdcjl') + zj_r.get('zmbddcjl') - zj_r.get('zmstdcjl') - zj_r.get('zmsddcjl')) * 100 / each_data.get('v'), 2)
                # change_rate = None
                # shake_rate = None
                # change_amount = None
                # close = each_data.get('c')
                # p_close = each_data.get('pc')
                # high = each_data.get('h')
                # low = each_data.get('l')
                # if close and p_close and high and low:
                #     shake_rate = (high-low)*100/p_close
                #     change_rate = (close-p_close)*100/p_close
                #     change_amount = close - p_close
                record = class_name(
                    date=date_time,
                    open=each_data.get('o'),
                    high=each_data.get('h'),
                    low=each_data.get('l'),
                    close=each_data.get('p'),
                    volume=each_data.get('v'),
                    turnover=each_data.get('cje'),
                    shake_rate=each_data.get('zf'),
                    turnover_rate=each_data.get('hs'),
                    change_rate=each_data.get('pc'),
                    change_amount=each_data.get('ud'),
                    jlrl=jlrl,
                    zljlrl=zljlrl
                )
                db.session.add(record)
                updated = True
            db.session.commit()
        print("Add record success for: " + stock_full)
        return updated


    def updateZJ(self, db, class_name, stock_code, se, dates_to_fill):
        print("Start loading ZJ data for: " + stock_code)
        stock_zj_url = 'http://api.mairuiapi.com/hsmy/zjlr/'
        r = self.get_my_data(stock_zj_url, stock_code, None)
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

    def update_all_stocks_list(self, db):
        print("Start updating all update_stocks list!")
        stock_url = 'http://api.mairuiapi.com/hslt/list/' + md_licence
        headers = {'content-type': 'application/json'}
        try:
            r = requests.get(stock_url, headers=headers)
            if r.status_code != 200:
                raise Exception('Build norm emr error: status code {}'.format(r.status_code))
            r.encoding = "utf-8"
            results = json.loads(r.text)
            for each_stock in results:
                code = each_stock.get('dm')
                name = each_stock.get('mc')
                se = each_stock.get('jys')

                # Strip suffix from code (e.g., '000001.SZ' -> '000001')
                clean_code = code.split('.')[0] if '.' in code else code

                record = db.session.query(Stock).filter(Stock.code == clean_code).scalar()
                if record:
                    if record.name != name:
                        old_name = record.name
                        record.name = name
                        print("Updated stock: {} {} with new name: {}".format(clean_code, old_name, name))
                    if record.se != se:
                        old_se = record.se
                        record.se = se
                        print("Updated stock: {} {} {} with new se: {}".format(clean_code, record.name, old_se, se))
                else:
                    new_record = Stock(
                        code=clean_code,
                        name=name,
                        se=se,
                        type='s',
                    )
                    db.session.add(new_record)
                    print("Added new stock: {} {}".format(clean_code, name))
                db.session.commit()

            print("Finished update all update_stocks list!")
            print(datetime.now())

        except Exception as e:
            err = traceback.format_exc()
            logging.error(f"{err} error")
            db.session.rollback()
            # e = APIException('2209')
            rst = e
        return


    def get_my_data(self, base_url, stock_code, time_slot, repeat_time=10, cq='n', start_time=None, end_time=None):
        if time_slot is not None:
            url_sucession = stock_code + '/' + time_slot + '/' + cq + '/' + md_licence
        else:
            url_sucession = stock_code + '/' + md_licence


        if start_time is not None:
            url_sucession = url_sucession + '?st=' + start_time
        if end_time is not None:
            url_sucession = url_sucession + '&et=' + end_time

        stock_url = base_url + url_sucession
        headers = {'content-type': 'application/json'}
        # get stock basic
        for i in range(repeat_time):
            sleep(0.5)
            results = None
            r = requests.get(stock_url, headers=headers)
            r.encoding = "utf-8"
            if r.status_code != 200:
                print(r)
                # raise APIException('8801', 'Get data frm mydata server failed with status code: {}.'.format(r.status_code))
            elif r.text == '102' or r.text == '101':
                raise APIException('8802',
                                   'Licence not valid or reached the Limit with status code: {}.'.format(r.status_code))
            else:
                results = json.loads(r.text)
            if results is not None:
                break
        if results == [] or results == {} or results is None:
            print(r)
            raise APIException('8803', 'Stock data is empty with status code: {}.'.format(r.status_code))
        return results


    def get_latest_date(self, stock_code, se, bind_key=DataBase.stocks):
        time_unit = self.get_time_unit(bind_key)
        if 's' in stock_code:
            stock_url = 'https://api.mairuiapi.com/hsindex/latest/'
            stock_code = stock_code[2:]
            time_unit = 'd'
        else:
            stock_url = 'https://api.mairuiapi.com/hsstock/latest/'
        stock_full = stock_code + '.' + se.upper()
        r = self.get_my_data(stock_url, stock_full, time_unit)
        latest_date = r[0].get('t')
        return latest_date


    def get_today_open(self, stock_code, se):
        time_unit = self.get_time_unit()
        if 's' in stock_code:
            stock_url = 'https://api.mairuiapi.com/hsindex/latest/'
            stock_code = stock_code[2:]
            time_unit = 'd'
        else:
            stock_url = 'https://api.mairuiapi.com/hsstock/latest/'
        stock_full = stock_code + '.' + se.upper()
        r = self.get_my_data(stock_url, stock_full, time_unit)
        lastest_date = r[0].get('t')
        lastest_date = parser().parse(lastest_date)
        open_price = float(r[0].get('o'))
        return lastest_date, open_price


    def get_stock_cap(self, stock_code, se):
        if 's' in stock_code:
            # stock_url = 'http://api.mairuiapi.com/hsrl/ssjy/'
            # stock_code = stock_code[2:]
            # time_unit = 'd'
            return 0, 0
        else:
            stock_url = 'http://api.mairuiapi.com/hsrl/ssjy/'
        r =self.get_my_data(stock_url, stock_code, None)
        cap = round(float(r.get('sz')) / 100000000, 2)
        pe = float(r.get('pe'))
        return cap, pe


    def get_time_unit(self, bind_key=DataBase.stocks):
        if bind_key == DataBase.stocks:
            time_unit = 'd'
        elif bind_key == DataBase.stocks:
            time_unit = 'd'
        # DH/DQ databases removed - all use 'd' time unit
        elif bind_key == DataBase.stocks_m:
            time_unit = '5m'
        else:
            time_unit = 'd'
        return time_unit


    def update_index_list(self, db):
        print("Start updating index list!")
        stock_url = 'https://api.mairuiapi.com/hszg/list/' + md_licence
        headers = {'content-type': 'application/json'}
        try:
            r = requests.get(stock_url, headers=headers)
            if r.status_code != 200:
                raise Exception('Build norm emr error: status code {}'.format(r.status_code))
            r.encoding = "utf-8"
            results = json.loads(r.text)
            # Filter for index records (type2=7 for 指数成分, type2=9 for 大盘指数)
            for each_stock in results:
                type2 = each_stock.get('type2', -1)
                isleaf = each_stock.get('isleaf', 0)
                # Only process index leaf nodes
                if type2 not in [7] or isleaf != 1:
                    continue
                code = each_stock.get('code')
                name = each_stock.get('name')
                # For indexes, set default exchange based on type1
                type1 = each_stock.get('type1', 0)
                se = 'sh' if type1 == 0 else 'unknown'  # A股 defaults to sh, can be refined
                record = db.session.query(StockIndex).filter(StockIndex.code == code).scalar()
                if record:
                    if record.name != name:
                        old_name = record.name
                        record.name = name
                        print("Updated index: {} {} with new name: {}".format(code, old_name, name))
                    if record.se != se:
                        old_se = record.se
                        record.se = se
                        print("Updated index: {} {} {} with new se: {}".format(code, record.name, old_se, se))
                else:
                    new_record = StockIndex(
                        code=code,
                        name=name,
                        se=se,
                    )
                    db.session.add(new_record)
                    print("Added new index: {} {}".format(code, name))
                db.session.commit()

            print("Finished update index list!")
            print(datetime.now())

        except Exception as e:
            err = traceback.format_exc()
            logging.error(f"{err} error")
            db.session.rollback()
            # e = APIException('2209')
            rst = e
        return


    def update_stock_index_group(self, db):
        print("Start updating index group!")

        # zhishu_000016 中证50；
        # zhishu_399005 中小100
        # hs300 沪深300
        # zhishu_000905 中证500
        stock_url = 'http://api.mairuiapi.com/hszg/gg/hs300/' + md_licence
        # stock_url = 'http://api.mairuiapi.com/hszg/list/' + md_licence
        headers = {'content-type': 'application/json'}
        try:
            r = requests.get(stock_url, headers=headers)
            if r.status_code != 200:
                raise Exception('Build norm emr error: status code {}'.format(r.status_code))
            r.encoding = "utf-8"
            results = json.loads(r.text)
            for each_stock in results:
                code = each_stock.get('dm')
                name = each_stock.get('mc')
                se = each_stock.get('jys')
                record = db.session.query(StockIndex).filter(StockIndex.code == code).scalar()
                if record:
                    if record.name != name:
                        old_name = record.name
                        record.name = name
                        print("Updated index: {} {} with new name: {}".format(code, old_name, name))
                    if record.se != se:
                        old_se = record.se
                        record.se = se
                        print("Updated index: {} {} {} with new se: {}".format(code, record.name, old_se, se))
                else:
                    new_record = StockIndex(code=code, name=name, se=se)
                    db.session.add(new_record)
                    print("Added new index: {} {}".format(code, name))
                db.session.commit()

            print("Finished update index group!")
            print(datetime.now())

        except Exception as e:
            err = traceback.format_exc()
            logging.error(f"{err} error")
            db.session.rollback()
            # e = APIException('2209')
            rst = e
        return

    def get_stock_history(self, symbol, start_time, end_time, time_slot):
        base_url = "http://api.mairuiapi.com/hsstock/history/"
        results = self.get_my_data(base_url, symbol, time_slot, start_time=start_time, end_time=end_time)
        return results
