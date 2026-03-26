from datetime import datetime
from db.models import Rule, StockRuleEarn
from end_points.common.const.consts import INIT_MONEY, DataBase, Status
from end_points.get_stock.operations.get_stock_utils import stockDataFrame
from end_points.common.tech_indicators.tech_factors import kdj_macd
from end_points.common.tech_indicators.tech_factors_utils import calculate_earn, cal_weighted_avg, get_indicating_dates, \
    get_trading_items_tech, cal_avg_with_wight


def getRuleFunc(db, rule_id, data):
    rule = db.session.query(Rule).filter(Rule.id == rule_id).first()
    if rule:
        indicator_dates = eval(rule.info)(data)
    else:
        indicator_dates = kdj_macd(data)
    return indicator_dates

def getStockRuleEarnModel(bind_key):
    """Get the StockRuleEarn model class

    Note: DH/DQ databases have been removed, all use the same model
    """
    # All bind keys now use the same StockRuleEarn model
    return StockRuleEarn

def calEarningRate(earns):
    trading_times = len(earns)
    earn_num = 0
    for each in earns:
        if each > 0:
            earn_num += 1
    earning_rate = round(earn_num * 100 / trading_times, 2) if trading_times > 0 else 0
    return trading_times, earning_rate

def cal_avg_earn(earn_results):
    earns = []
    avg_earns = []
    all_trading_times = []
    earning_rates = []
    earn_updates = []
    stock_nums = []
    for earn_result in earn_results:
        updated_at = earn_result.get('updated_at')
        earn_updates.append(updated_at)
        if earn_result:
            earn = earn_result.get('earn')
            avg_earn = earn_result.get('avg_earn')
            trading_times = earn_result.get('trading_times')
            earning_rate = earn_result.get('earning_rate')
            stock_num = earn_result.get('stock_num')
            if trading_times and trading_times > 0:
                earns.append(earn)
                avg_earns.append(avg_earn)
                all_trading_times.append(trading_times)
                earning_rates.append(earning_rate)
                stock_nums.append(stock_num)
    new_earn = cal_avg_with_wight(earns, stock_nums) if earns else None
    new_avg_earn = cal_avg_with_wight(avg_earns, stock_nums) if avg_earns else None
    new_trading_times = cal_avg_with_wight(all_trading_times, stock_nums) if all_trading_times else None
    new_earning_rate = cal_avg_with_wight(earning_rates, stock_nums) if earning_rates else None
    earn_updated_at = min(earn_updates) if (earn_updates and not None in earn_updates) else None
    return new_earn, new_avg_earn, new_earning_rate, new_trading_times, earn_updated_at

def cal_avg_earn_model(earn_results):
    earns = []
    avg_earns = []
    all_trading_times = []
    earning_rates = []
    earn_updates = []
    for earn_result in earn_results:
        if earn_result:
            updated_at = earn_result.get('updated_at')
            earn_updates.append(updated_at)
            earn = earn_result.get('earn')
            avg_earn = earn_result.get('avg_earn')
            trading_times = earn_result.get('trading_times')
            earning_rate = earn_result.get('earning_rate')
            if trading_times and trading_times > 0:
                earns.append(earn)
                avg_earns.append(avg_earn)
                all_trading_times.append(trading_times)
                earning_rates.append(earning_rate)
    new_earn = cal_avg_with_wight(earns, all_trading_times) if earns else None
    new_avg_earn = cal_avg_with_wight(avg_earns, all_trading_times) if avg_earns else None
    new_trading_times = sum(all_trading_times)
    new_earning_rate = cal_avg_with_wight(earning_rates, all_trading_times) if earning_rates else None
    earn_updated_at = min(earn_updates) if (earn_updates and not None in earn_updates) else None
    return new_earn, new_avg_earn, new_earning_rate, new_trading_times, earn_updated_at

def indicating(stock_data, indicator_dates, N=1):
    last_indicating_date = None
    is_indicating = False
    if len(indicator_dates) > 0:
        last_indicating_date = indicator_dates[-1]
    latest_date = get_latest_N_date(stock_data, N)
    for the_date in indicator_dates:
        if the_date >= latest_date:
            is_indicating = True
    return is_indicating, last_indicating_date

def get_latest_N_date(stock_data, N):
    latest_data = stock_data.iloc[-N]
    latest_date = latest_data['date']
    # latest_date = pd.Timestamp(2023, 1, 1, 0)
    return latest_date
