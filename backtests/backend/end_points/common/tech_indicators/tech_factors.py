#!/usr/bin/python
# coding=utf-8
import numpy

from end_points.common.tech_indicators.libs.mytt import *
from end_points.common.tech_indicators.libs.mytt_indicators import *


def cal_qrr_day(dataset, n=5):
    """Calculate Quality Relative Ratio for volume"""
    result_qrrs = []
    volums = dataset['volume'].values
    ma = MA(volums, n)
    for i in range(len(dataset)):
        if ma[i] is None or ma[i] == 0:
            qrr = None
        else:
            qrr = volums[i] / ma[i]
            qrr = round(qrr, 2)
        result_qrrs.append(qrr)
    return result_qrrs


# KDJ + MACD strategy - used by cal_earn_utils.py
def kdj_macd(stock_data):
    """KDJ and MACD combined strategy"""
    # data used
    close = stock_data['close'].values
    high = stock_data['high'].values
    low = stock_data['low'].values
    dif, dea, macd = MACD(close)
    k, d, j = KDJ(close, high, low)

    # conditions
    cond1 = CROSS(dif, dea)
    cond2 = CROSS(k, d)
    cond3 = dif > 0
    result = cond1 & cond2 & cond3
    return result