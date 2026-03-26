# import threading
import json
from datetime import datetime, date
import codecs
import os
import logging

from pandas import Timestamp
import numpy as np
from end_points.common.const.consts import DataBase, INIT_MONEY, Trade, Status, INIT_MONEY_PER_STOCK, RuleType
from end_points.get_earn.operations.cal_earn_utils import indicating
HIGH_LIMIT = 0.095
LOW_LIMIT = -0.095
MAX_LOSS_PERCENT = 0.05

def format_date(the_date):
    """Format date to ISO 8601 string"""
    if isinstance(the_date, str):
        return the_date
    if isinstance(the_date, (datetime, date)):
        return the_date.strftime("%Y-%m-%dT%H:%M:%S")
    if isinstance(the_date, Timestamp):
        return the_date.to_pydatetime().strftime("%Y-%m-%dT%H:%M:%S")
    return the_date


def _sim_log_dir() -> str:
    dirname = os.path.dirname(__file__)
    return os.path.join(dirname, 'sim_logs')


def _sim_log_path(sim_id) -> str:
    return os.path.join(_sim_log_dir(), f'{sim_id}.html')


# DL model inference removed
# DL model utils removed
from db.models import SimTrading, Simulator, Stock, Rule
from end_points.common.tech_indicators.tech_factors_utils import get_indicating_dates, get_trading_items_tech, \
    cal_assets_multi_buy, buy, cal_weighted_avg, cal_assets, sell
from end_points.get_stock.operations.get_stock_utils import stockDataFrameFromTushare


# def update_sim_model(db, sim_id, indicating_items, top_stocks):
#     """
#     Simplified version - update sim without DL model inference.
#     Agent system uses pre-calculated signals from StockRuleEarn table.
#     indicating_items: list of dicts with stock_code, indicating_date, sims
#     top_stocks: list of stock code strings
#     """
#     sim_record = db.session.query(Simulator).filter(Simulator.id == sim_id).first()
#     if not sim_record:
#         return None
#
#     # Update sim status based on indicating_items
#     if indicating_items and len(indicating_items) > 0:
#         sim_record.status = Status.indicating
#         # Get the latest indicating date
#         latest_date = max([item.get('indicating_date') for item in indicating_items
#                           if item.get('indicating_date')])
#         if isinstance(latest_date, pd.Timestamp):
#             latest_date = latest_date.to_pydatetime()
#         sim_record.indicating_date = latest_date
#     else:
#         sim_record.status = Status.running
#
#     sim_record.updated_at = datetime.now()
#     db.session.commit()
#     return sim_record.indicating_date

def update_sim_model(db, sim_id, indicating_items):
    """
    Update simulator model with trading results.

    Args:
        db: Database session
        sim_id: Simulator ID
        indicating_items: List of dicts with 'stock_code' and 'indicating_date'
        top_stocks: DEPRECATED - now extracted from indicating_items automatically
    """
    sim_record = db.session.query(Simulator).filter(Simulator.id == sim_id).first()
    init_money = sim_record.init_money
    rule_type = db.session.query(Rule.type).join(Simulator, Simulator.rule_id == Rule.id)\
        .filter(Simulator.id == sim_id).scalar()

    # Get sell condition parameters from database config
    from db.models import SimulatorConfig
    config = db.session.query(SimulatorConfig).filter(SimulatorConfig.id == 1).first()
    if config:
        profit_threshold = config.profit_threshold if config.profit_threshold is not None else 0
        stop_loss = config.stop_loss if config.stop_loss is not None else 5
        max_holding_days = config.max_holding_days if config.max_holding_days is not None else 5
    else:
        # Fallback to defaults if config not exists
        profit_threshold = 0
        stop_loss = 5
        max_holding_days = 5

    # Extract unique stock codes from indicating_items (sorted for deterministic order)
    top_stocks = sorted(set(item['stock_code'] for item in indicating_items))

    if_indicating = False
    all_indicating_dates = []
    all_sim_items = []
    for each_stock in top_stocks:
        trading_items, is_indicating, last_indicating_date = get_stock_trading_items_model(
            db, each_stock, indicating_items, rule_type,
            profit_threshold=profit_threshold,
            stop_loss=stop_loss,
            max_holding_days=max_holding_days
        )
        if is_indicating:
            if_indicating = True
        if last_indicating_date is not None:
            all_indicating_dates.append(last_indicating_date)
        sim_trading_items = get_sim_trading_items(trading_items, each_stock)
        all_sim_items += sim_trading_items

    cum_earn, avg_earn, earning_rate, trading_times, money, bought_items, earning_info = cal_sim_earn_multi_buy(db, sim_id, all_sim_items, init_money)
    if if_indicating:
        sim_record.status = Status.indicating
    elif len(bought_items) > 0:
        sim_record.status = Status.holding
    else:
        sim_record.status = Status.running

    if len(all_indicating_dates) > 0:
        all_indicating_dates.sort()
        sim_record.indicating_date = all_indicating_dates[-1]

    # update record
    sim_record.current_money = money
    sim_record.current_shares = json.dumps(bought_items, ensure_ascii=False)
    sim_record.earning_info = json.dumps(earning_info)
    sim_record.cum_earn = cum_earn
    sim_record.avg_earn = avg_earn
    sim_record.earning_rate = earning_rate
    sim_record.trading_times = trading_times
    sim_record.updated_at = datetime.now()
    db.session.commit()
    return

def get_stock_trading_items_model(db, stock_code, indicating_items, rule_type=RuleType.agent,
                                  profit_threshold=0, stop_loss=5, max_holding_days=5):
    stock_data = stockDataFrameFromTushare(stock_code)
    indicating_dates = []
    for each_item in indicating_items:
        if each_item['stock_code'] == stock_code:
            indicating_dates.append(each_item['indicating_date'])
    indicating_dates = align_indicator_dates_to_market_dates(stock_data, indicating_dates)
    trading_items = get_trading_items_model(stock_data, indicating_dates,
                                             profit_threshold=profit_threshold,
                                             stop_loss=stop_loss,
                                             max_holding_days=max_holding_days,
                                             rule_type=rule_type)
    is_indicating, last_indicating_date = indicating(stock_data, indicating_dates)
    return trading_items, is_indicating, last_indicating_date
    trading_items = get_trading_items_model(stock_data, indicating_dates, rule_type=rule_type)
    is_indicating, last_indicating_date = indicating(stock_data, indicating_dates)
    return trading_items, is_indicating, last_indicating_date

def write_sim_log(sim_id, message, color='black', date=None):
    file = None
    try:
        os.makedirs(_sim_log_dir(), exist_ok=True)
        file_path = _sim_log_path(sim_id)
        date_time = datetime.now() if date is None else date
        message = format_date(date_time) + ":    " + message
        file = open(file_path, 'a', encoding='utf-8')
        formatted_message = """<p style="color: {}; font-family: 'Liberation Sans',sans-serif">{}</p>""".format(color, message)
        file.write(formatted_message)
    except Exception as e:
        logging.exception("Failed to write simulator log for sim_id=%s: %s", sim_id, e)
    finally:
        if file is not None:
            file.close()

def read_sim_log(sim_id):
    data = None
    file = None
    try:
        file_path = _sim_log_path(sim_id)
        if not os.path.exists(file_path):
            return None
        file = codecs.open(file_path, 'r', 'utf-8')
        data = file.read()
        data = data.replace('\n', '')
    except Exception as e:
        logging.exception("Failed to read simulator log for sim_id=%s: %s", sim_id, e)
    finally:
        if file is not None:
            file.close()
        return data

def delete_sim_log(sim_id):
    try:
        file_path = _sim_log_path(sim_id)
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logging.exception("Failed to delete simulator log for sim_id=%s: %s", sim_id, e)
        return e

def get_sim_trading_items(trading_items, stock_code):
    sim_trading_items = []
    for item in trading_items:
        indicating_date = item.get('indicating_date')
        indicating_price = item.get('indicating_price')
        buy_date = item.get('buy_date')
        buy_price = item.get('buy_price')
        sell_date = item.get('sell_date')
        sell_price = item.get('sell_price')
        fail_to_buy_date = item.get('fail_to_buy_date')
        fail_to_buy_close = item.get('fail_to_buy_close')
        fail_to_sell_items = item.get('fail_to_sell_items')

        indicating_item = {
            'stock': stock_code,
            "date": indicating_date,
            "type": Trade.indicating,
            "indicating_price": indicating_price
        }
        sim_trading_items.append(indicating_item)

        if fail_to_buy_date and fail_to_buy_close:
            fb_trading_item = {
                'stock': stock_code,
                "date": fail_to_buy_date,
                "fail_to_buy_close": fail_to_buy_close,
                "type": Trade.fail_to_buy,
            }
            sim_trading_items.append(fb_trading_item)

        if buy_date and buy_price:
            trading_item = {
                'stock': stock_code,
                "date": buy_date,
                "price": buy_price,
                "type": Trade.buy,
            }
            sim_trading_items.append(trading_item)

            if fail_to_sell_items:
                for fs_item in fail_to_sell_items:
                    fail_to_sell_date = fs_item.get('fail_to_sell_date')
                    fail_to_sell_price = fs_item.get('fail_to_sell_price')
                    last_close = fs_item.get('last_close')

                    fs_trading_item = {
                        'stock': stock_code,
                        "date": fail_to_sell_date,
                        "fail_to_sell_price": fail_to_sell_price,
                        "last_close": last_close,
                        "type": Trade.fail_to_sell,
                    }
                    sim_trading_items.append(fs_trading_item)

            if sell_date and sell_price:
                sell_trading_item = {
                    'stock': stock_code,
                    "date": sell_date,
                    "bought_date": buy_date,
                    "price": sell_price,
                    "type": Trade.sell,
                }
                sim_trading_items.append(sell_trading_item)
    # sim_trading_items.sort(key=lambda x: x.get('date'))
    return sim_trading_items

def cal_sim_earn_multi_buy(db, sim_id, sim_trading_items, init_money=INIT_MONEY, buy_slippage=0.001, sell_slippage=0.001):
    sim_trading_items.sort(key=lambda x: x.get('date'))
    assets = init_money
    assets_memory = [init_money]
    money = init_money
    indicating_items = []
    bought_items = []
    earns = []
    earn_dates = []
    bought_dates = []
    for item in sim_trading_items:
        stock_code = item.get('stock')
        trade_date = item.get('date')
        trade_price = item.get('price')
        trade_type = item.get('type')
        stock_name = db.session.query(Stock.name).filter(Stock.code == stock_code).scalar()
        if trade_type == Trade.indicating:
            indicating_items.append(item)
            indicating_price = item.get('indicating_price')
            add_sim_trading_record(db, sim_id, trade_date, Trade.indicating, 0, stock_code,price=indicating_price)
        elif trade_type == Trade.fail_to_buy:
            fail_close = item.get('fail_to_buy_close')
            add_sim_trading_record(db, sim_id, trade_date, Trade.fail_to_buy, 0, stock_code, fail_close)
        elif trade_type == Trade.buy:
            if INIT_MONEY_PER_STOCK >= 100*trade_price and money >= INIT_MONEY_PER_STOCK:
                slippage = min(round(trade_price * buy_slippage, 2), 0.01)
                trade_price += slippage
                remain_money, new_share, trading_amount_buy = buy(INIT_MONEY_PER_STOCK, 0, trade_price)
                money += remain_money - INIT_MONEY_PER_STOCK
                bought_item = {'stock': stock_code,
                               'name': stock_name,
                               'price': trade_price,
                               'share': new_share,
                               'bought_date': trade_date,
                               'bought_amount': trading_amount_buy}
                bought_items.append(bought_item)
                assets = cal_assets_multi_buy(money, bought_items)
                add_sim_trading_record(db, sim_id, trade_date, Trade.buy, trading_amount_buy, stock_code, trade_price)
            else:
                add_sim_trading_record(db, sim_id, trade_date, Trade.not_sufficient_to_buy, 0, stock_code, trade_price, cash=round(money, 2))
                # print(f'{trade_date} Cash: {money}, not sufficient to buy {stock_code} {stock_name} with price {trade_price}.')
        elif trade_type == Trade.fail_to_sell:
            for each_item in bought_items:
                if stock_code == each_item.get('stock'):
                    fail_close = item.get('fail_to_sell_price')
                    last_close = item.get('last_close')
                    add_sim_trading_record(db, sim_id, trade_date, Trade.fail_to_sell, 0, stock_code, fail_close, last_close=last_close)
        elif trade_type == Trade.sell:
            bought_date = item.get('bought_date')
            for each_item in bought_items:
                check_bought_date = each_item.get('bought_date')
                if stock_code == each_item.get('stock') and bought_date == check_bought_date:
                    bought_amount = each_item.get('bought_amount')
                    share = each_item.get('share')
                    trade_price = item.get('price')
                    # earn_raw = (trade_price - bought_price) * share
                    slippage = min(round(trade_price * sell_slippage, 2), 0.01)
                    trade_price -= slippage
                    money, share, trading_amount = sell(money, share, trade_price)
                    if share == 0:
                        bought_items.remove(each_item)
                    assets = cal_assets_multi_buy(money, bought_items)
                    earn = (assets - assets_memory[-1]) * 100 / bought_amount
                    earns.append(round(earn, 2))
                    earn_dates.append((trade_date))
                    bought_dates.append(bought_date)
                    assets_memory.append(assets)
                    add_sim_trading_record(db, sim_id, trade_date, Trade.sell, trading_amount, stock_code, trade_price, earn, bought_date)
        else:
            print(trade_date, trade_type, stock_code, stock_name, trade_price)
    total_earn = round((assets - init_money)*100/init_money, 2)
    avg_earn = cal_weighted_avg(earns)
    num_earns = sum(x > 0 for x in earns)
    trade_times = len(earns)
    earning_rate = round(num_earns * 100 / trade_times, 2) if trade_times > 0 else 0
    earn_rates_after, cum_earns_after, avg_earns_after = get_cum_earning_rate(earns)
    earning_info = {
        'earns': earns,
        'sell_dates': earn_dates,
        'bought_dates': bought_dates,
        'earn_rates_after': earn_rates_after,
        'cum_earns_after': cum_earns_after,
        'avg_earns_after': avg_earns_after,
        'assets': assets_memory[1:]
    }
    return total_earn, avg_earn, earning_rate, trade_times, money, bought_items, earning_info


def add_sim_trading_record(db, sim_id, trade_date, trade_type, trading_amount, stock_code, price=None, earn=0, bought_at='', last_close=None, cash=None):
    if isinstance(trade_date, str):
        trade_date = datetime.fromisoformat(trade_date.replace("Z", ""))
    elif isinstance(trade_date, Timestamp):
        trade_date = trade_date.to_pydatetime()
    query = db.session.query(SimTrading).filter(SimTrading.sim_id == sim_id) \
        .filter(SimTrading.stock == stock_code) \
        .filter(SimTrading.trading_date == trade_date)\
        .filter(SimTrading.trading_type == trade_type).first()
    if query:
        return
    record = SimTrading(
        sim_id=sim_id,
        stock=stock_code,
        trading_date=trade_date,
        trading_type=trade_type,
        trading_amount=trading_amount
    )
    db.session.add(record)
    db.session.commit()
    stock_name = db.session.query(Stock.name).filter(Stock.code==stock_code).scalar()
    if trade_type == Trade.buy:
        message = "Buying {} for {} {} with close price {}!".format(trading_amount, stock_code, stock_name, round(price,2))
        write_sim_log(sim_id, message, 'ForestGreen', trade_date)
    elif trade_type == Trade.fail_to_buy:
        message = "Failed to buy {} {} with close price {}!".format(stock_code, stock_name, price)
        write_sim_log(sim_id, message, 'coffee', trade_date)
    elif trade_type == Trade.not_sufficient_to_buy:
        message = "Cash: {}, less than INIT_MONEY_PER_STOCK or not sufficient to buy {} {} with close price {}!".format(cash, stock_code, stock_name, price)
        write_sim_log(sim_id, message, 'silver', trade_date)
    elif trade_type == Trade.fail_to_sell:
        message = "Failed to sell {} {} with price {} and last close price {}!".format(stock_code, stock_name, price, last_close)
        write_sim_log(sim_id, message, 'coffee', trade_date)
    elif trade_type == Trade.sell:
        message = "Selling {} for {} {} bought at {} with price {}!  Earned: {}%!".format(trading_amount, stock_code, stock_name, bought_at, price, round(earn, 2))
        write_sim_log(sim_id, message, 'tomato', trade_date)
    elif trade_type == Trade.indicating:
        message = "Stock {} {} is indicating with close price {}!".format(stock_code, stock_name, price)
        write_sim_log(sim_id, message, 'darkorange', trade_date)
    return

# def terminate_thread(sim_id):
#     threads = threading.enumerate()
#     for each_thead in threads:
#         if each_thead.name == str(sim_id):
#             each_thead._wait_for_tstate_lock()
#             each_thead._stop()
#     return

def clean_sim_trading(db, sim_id):
    records = db.session.query(SimTrading).filter(SimTrading.sim_id == sim_id).all()
    for each_record in records:
        db.session.delete(each_record)
    db.session.commit()
    return

def get_cum_earning_rate(earns):
    earning = np.array(earns) > 0
    cum_earning_rev = np.cumsum(np.flip(earning))
    earning_rates_rev = cum_earning_rev * 100 / (np.arange(len(earns))+1)
    earning_rates = np.round(np.flip(earning_rates_rev),2)

    cum_earns_rev = np.cumsum(np.flip(earns))
    cum_earns = np.round(np.flip(cum_earns_rev),2)
    avg_earns = np.round(np.flip(cum_earns_rev/(np.arange(len(earns))+1)),2)

    return list(earning_rates), list(cum_earns), list(avg_earns)


def align_indicator_dates_to_market_dates(stock_data, indicator_dates):
    """
    Align raw signal dates to the next available market date in stock data.

    Remote-agent signals may be written on weekends/non-trading days.
    The simulator should treat them as signals for the next trading day,
    otherwise exact-date matching produces no simulated trades.
    """
    if stock_data is None or len(stock_data) == 0 or not indicator_dates:
        return indicator_dates

    market_dates = []
    for value in stock_data['date'].tolist():
        ts = Timestamp(value)
        market_dates.append(ts.normalize())
    market_dates = sorted(set(market_dates))

    aligned_dates = []
    for raw_date in indicator_dates:
        target = Timestamp(raw_date).normalize()
        matched = None
        for market_date in market_dates:
            if market_date >= target:
                matched = market_date
                break
        if matched is not None:
            aligned_dates.append(matched)
    return aligned_dates

def max_drawback(earns):
    max_drawback = 0
    if earns is not None and len(earns) > 0:
        min_earns = min(earns)
        if min_earns < 0:
            max_drawback = round(min_earns, 2)
    return max_drawback

def sharpe(earns, risk_free_rate=0.02, days_per_year=252):
    sharpe_year = None
    if len(earns) > 1:
        returns = np.array(earns)
        mu = np.mean(returns)
        sig = np.std(returns)
        sharpe_day = (mu-risk_free_rate/days_per_year)/sig
        sharpe_year = sharpe_day * np.sqrt(days_per_year)
        sharpe_year = round(sharpe_year, 2)
    return sharpe_year


# Turbulence functions removed - not used by Agent system

def get_last_month_stats(earning_dict, update_date):
    # cut_date_timestamp = datetime.strptime(update_date, "%Y-%m-%dT%H:%M:%S").timestamp() - 30*24*3600
    cut_date_timestamp = update_date.timestamp() - 30 * 24 * 3600
    cut_date = datetime.fromtimestamp(cut_date_timestamp)
    cum_earn_after, earn_rate_after, avg_earn_after, trading_times = None, None, None, None
    earning_dates = earning_dict.get('sell_dates')
    if earning_dates is not None:
        recent_dates = list(filter(lambda i: i > str(cut_date), earning_dates))
        trading_times = len(recent_dates)
        if trading_times > 0:
            cum_earn_after = round(earning_dict.get('cum_earns_after')[-trading_times], 2)
            avg_earn_after = round(earning_dict.get('avg_earns_after')[-trading_times], 2)
            earn_rate_after = round(earning_dict.get('earn_rates_after')[-trading_times], 2)
    return cum_earn_after, earn_rate_after, avg_earn_after, trading_times


def cal_annual_earn(first_buy_date, cum_earn):
    today_date = datetime.now().date()
    # Convert first_buy_date string to date object
    if isinstance(first_buy_date, str):
        first_buy_date = datetime.strptime(first_buy_date, '%Y-%m-%dT00:00:00').date()
    delta_dates = (today_date - first_buy_date).days
    annual_earn = cum_earn * 365 / delta_dates if delta_dates > 0 else 0
    return round(annual_earn, 2)


def get_trading_items_model(stock_data, indicator_dates, profit_threshold=0, stop_loss=5, max_holding_days=5, rule_type=RuleType.agent):
    stock_data = stock_data.reset_index(drop=True)
    trading_items = []
    open_prices = stock_data['open']
    close_prices = stock_data['close']
    dates = stock_data['date']
    data_length = len(dates)

    # Convert stop_loss from percentage to decimal (e.g., 5 -> 0.05)
    stop_loss_decimal = stop_loss / 100.0
    # Convert profit_threshold from percentage to decimal (e.g., 0 -> 0.00, 1 -> 0.01)
    profit_threshold_decimal = profit_threshold / 100.0

    # 将 indicator_dates 转换为字符串集合，避免类型不匹配导致的比较失败
    indicator_dates_str = {d.strftime('%Y-%m-%d') if hasattr(d, 'strftime') else str(d)[:10]
                           for d in indicator_dates}

    for each_index in range(data_length):
        date = dates[each_index]
        # 统一转换为字符串格式进行比较
        date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)[:10]
        if date_str in indicator_dates_str:
            indicating_price = close_prices[each_index]
            trading_item = {
                "indicating_date": format_date(date),
                "indicating_price": indicating_price,
            }
            buying_index = each_index + 1
            if buying_index < data_length:
                buy_date = format_date(dates[buying_index])
                buy_price = close_prices[buying_index]
                if not np.isnan(buy_price) and not np.isnan(indicating_price):
                    daily_percent = (buy_price - indicating_price) / indicating_price
                    if daily_percent >= HIGH_LIMIT:
                        trading_item.update({
                            "fail_to_buy_date": buy_date,
                            "fail_to_buy_close": buy_price,
                        })
                    else:
                        trading_item.update({
                            "buy_date": buy_date,
                            "buy_price": buy_price,
                        })
                        fail_to_sell_items = []
                        for j in range(max_holding_days):
                            selling_index = each_index + 2 + j
                            if selling_index < data_length:
                                sell_date = format_date(dates[selling_index])
                                sell_price = close_prices[selling_index]
                                last_date_close = close_prices[selling_index-1]
                                loss_percent = (buy_price - sell_price) / buy_price
                                daily_loss_percent = (sell_price - last_date_close) / last_date_close
                                if (daily_loss_percent <= LOW_LIMIT) and (j != max_holding_days-1):
                                    fs_item = {
                                        "fail_to_sell_date": sell_date,
                                        "fail_to_sell_price": sell_price,
                                        "last_close": last_date_close,
                                    }
                                    fail_to_sell_items.append(fs_item)
                                    trading_item.update({'fail_to_sell_items': fail_to_sell_items})
                                else:
                                    # Sell conditions (OR logic):
                                    # 1. Profit: (sell_price - buy_price) / buy_price >= profit_threshold
                                    # 2. Stop loss: loss_percent >= stop_loss_decimal
                                    # 3. Time exit: reached max_holding_days
                                    profit_percent = (sell_price - buy_price) / buy_price
                                    if (profit_percent >= profit_threshold_decimal) or (loss_percent >= stop_loss_decimal) or (j == max_holding_days-1):
                                        trading_item.update({
                                            "sell_date": sell_date,
                                            "sell_price": sell_price,
                                        })
                                        break
            trading_items.append(trading_item)
    return trading_items
