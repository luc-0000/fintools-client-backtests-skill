#!/usr/bin/python
# coding=utf-8
import math
import datetime
from statistics import mean
from pandas import Timestamp
import numpy as np

from end_points.common.const.consts import INIT_MONEY

MAX_LOSS_PERCENT = 0.05


def format_date(the_date):
    """Format date to ISO 8601 string"""
    if isinstance(the_date, str):
        return the_date
    if isinstance(the_date, (datetime.datetime, datetime.date)):
        return the_date.strftime("%Y-%m-%dT%H:%M:%S")
    if isinstance(the_date, Timestamp):
        return the_date.to_pydatetime().strftime("%Y-%m-%dT%H:%M:%S")
    return the_date


def removeNone(dataset):
    """Remove None values from a list"""
    return list(filter(lambda x: x is not None, dataset))

#TODO: only include sold stocks, not holding update_stocks
def calculate_earn(trading_items, init_money=INIT_MONEY):
    # trading_infos = []
    earns = []
    total_earn = 0
    for item in trading_items:
        # new_item = copy.deepcopy(item)
        buy_date = item.get('buy_date')
        buy_price = item.get('buy_price')
        sell_date = item.get('sell_date')
        sell_price = item.get('sell_price')
        if buy_date and buy_price and sell_date and sell_price:
            # buy point
            money, share, _ = buy(init_money, 0, buy_price)
            # buy_date_format = buy_date.to_pydatetime().strftime("%Y-%m-%dT%H:%M:%S")
            # sell point
            money, share, _ = sell(money, share, sell_price)
            earn = money - init_money
            total_earn += earn
            earns.append(earn)
            # sell_date_diff = (sell_date - buy_date).days
            item['earn'] = round(earn, 2)
                # "dates_diff": sell_date_diff
        # trading_infos.append(new_item)
    cum_earn = round(total_earn * 100 / INIT_MONEY, 2)
    return cum_earn, earns

def is_increasing(dataset):
    increasing = True
    for i in range(len(dataset)):
        if i == 0:
            continue
        if dataset[i] < dataset[i - 1]:
            increasing = False
    return increasing


def buy(money, share, price):
    if price == 0:
        return money, share, 0
    price = round(price, 2)
    new_share = 100 * math.floor(money / price / 100)
    trading_amount = new_share * price
    comission = cal_comission(trading_amount)
    diff_amount = trading_amount + comission - money
    if diff_amount > 0:
        diff_share = math.ceil(diff_amount / price)
        new_share -= diff_share
        trading_amount = new_share * price
        comission = cal_comission(trading_amount)
    money = money - trading_amount - comission
    share += new_share
    trading_amount = round(trading_amount + comission, 2)
    return money, share, trading_amount


def sell(money, share, price):
    price = round(price, 2)
    trading_amount = price * share
    stamp_tax = cal_stamp_tax(trading_amount)
    comission_tax = cal_comission(trading_amount)
    money = money + trading_amount - stamp_tax - comission_tax
    share = 0
    trading_amount = round(trading_amount - stamp_tax - comission_tax, 2)
    return money, share, trading_amount


def cal_stamp_tax(trading_amount):
    rate = 0.001
    tax = rate * trading_amount
    return tax


def cal_comission(trading_amount):
    rate = 0.0001
    tax = rate * trading_amount
    if tax < 5 and trading_amount > 0:
        tax = 5.00
    return tax

def cal_assets(money, share, stock_price):
    result = money + share*stock_price
    return result

def cal_assets_multi_buy(money, bought_items):
    result = money
    for each_item in bought_items:
        share = each_item.get('share')
        price = each_item.get('price')
        result += share * price
    return result

def get_indicating_dates(stock_data, indicators, start_date=None):
    dates = stock_data.date
    indicating_dates = []
    for each_index in range(len(indicators)):
        if indicators[each_index] == True:
            date = dates[each_index]
            if not start_date or date >= start_date:
                indicating_dates.append(date)
    return indicating_dates

def get_trading_items_tech(stock_data, indicator_dates, buying_wait_days=0, selling_wait_days=5):
    trading_items = []
    open_prices = stock_data['open']
    close_prices = stock_data['close']
    dates = stock_data['date']
    data_length = len(dates)

    for each_index in range(data_length):
        date = dates[each_index]
        if date in indicator_dates:
            indicating_price = close_prices[each_index]
            trading_item = {
                "indicating_date": format_date(date),
                "indicating_price": indicating_price,
            }
            buying_index = each_index + buying_wait_days + 1
            if buying_index < data_length:
                wait_dates_close = close_prices[each_index:each_index + buying_wait_days]
                if is_increasing(wait_dates_close.values):
                    buy_date = format_date(dates[buying_index])
                    buy_price = open_prices[buying_index]
                    trading_item.update({
                        "buy_date": buy_date,
                        "buy_price": buy_price,
                    })
                    sell_date = None
                    sell_price = None
                    for j in range(selling_wait_days):
                        selling_index = each_index + 2 + j + buying_wait_days
                        if selling_index < data_length:
                            sell_date = format_date(dates[selling_index])
                            sell_price = open_prices[selling_index]
                            if sell_price > buy_price:
                                break
                            else:
                                loss_percent = (buy_price - sell_price) / buy_price
                                if loss_percent >= MAX_LOSS_PERCENT:
                                    break
                    trading_item.update({
                        "sell_date": sell_date,
                        "sell_price": sell_price,
                    })
            trading_items.append(trading_item)
    return trading_items

def cal_avg(num_ary):
    result = 0
    if num_ary:
        n = len(num_ary)
        result = sum(num_ary) / n
        result = round(result, 2)
    return result

def cal_weighted_avg(num_ary):
    result = 0
    if num_ary:
        n = len(num_ary)
        num_ary = np.array(num_ary)
        weighted_sum = num_ary[::-1].cumsum().sum()
        result = weighted_sum * 2 / n / (n + 1)
        result = round(result, 2)
    return result

# TODO: use EMA instead of mean
def cal_avg_with_wight(num_ary, weight_ary):
    if None in weight_ary:
        num_ary = removeNone(num_ary)
        result = mean(num_ary) if num_ary else None
        return result
    result = None
    total = 0
    if num_ary and weight_ary and len(num_ary)==len(weight_ary):
        for i in range(len(num_ary)):
            if num_ary[i] is None:
                total += 0
                weight_ary[i] = 0
            else:
                total += num_ary[i] * weight_ary[i]
        sum_weight = sum(weight_ary)
        result = round(total/sum_weight, 2) if sum_weight != 0 else None
    return result
