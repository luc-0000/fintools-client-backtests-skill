import json
import os
from datetime import datetime

import numpy as np
from end_points.common.const.consts import INIT_MONEY, Status
from db.models import Simulator, Rule
from scipy.ndimage import shift

from end_points.config.global_var import global_var
from end_points.init_global import init_global
from end_points.common.const.consts import TEST_START_DATE
from end_points.common.tech_indicators.tech_factors_utils import cal_weighted_avg


def get_combo_earn(db):
    print('Start updating combo sims...')
    # all_rules = all_rules_sorted(db)  # Removed: cron_tasks deleted
    all_rules = [172, 164, 174, 98]
    all_sims = (db.session.query(Simulator.id)\
            .join(Rule, Rule.id == Simulator.rule_id)\
            .filter(Rule.id.in_(all_rules)).all())
    all_sims = [x for (x,) in all_sims]
    combo_name = 'above_20'
    total_earn, avg_earn, earning_rate, trade_times, money, combo_trades = cal_combo_sims_earn(db, combo_name, all_sims)
    update_combo_sims(db, combo_name, total_earn, avg_earn, earning_rate, trade_times, money, combo_trades)
    print('Cal combo done!')
    print(datetime.now())
    return

def cal_combo_sims_earn(db, combo_name, all_sims, init_money=INIT_MONEY):
    combo_earns = []
    combo_trades = []
    avg_earns = []
    if combo_name == 'above_20':
        CUM_EARN_THRESHOULD = 20
        EARN_RATE_THRESJOULD = 70
        sims = (db.session.query(Simulator).filter(Simulator.id.in_(all_sims)).all())
        for each_sim in sims:
            sim_id = each_sim.id
            earning_dict = json.loads(each_sim.earning_info)
            earns = earning_dict.get('earns')
            bought_dates = earning_dict.get('bought_dates')
            sell_dates = earning_dict.get('sell_dates')
            cum_earns_chosen = np.cumsum(earns) > CUM_EARN_THRESHOULD
            cum_earns_chosen = shift(cum_earns_chosen, 1)
            earning = np.array(earns) > 0
            earning_rates = np.cumsum(earning) * 100 / (np.arange(len(earns)) + 1)
            earning_rate_choosen = earning_rates > EARN_RATE_THRESJOULD
            earning_rate_choosen = shift(earning_rate_choosen, 1)
            chosen = cum_earns_chosen & earning_rate_choosen
            for i, each_chosen in enumerate(chosen):
                if each_chosen == True:
                    bought_date = bought_dates[i]
                    sell_date = sell_dates[i]
                    earn = earns[i]
                    combo_earns.append(earn)
                    avg_earn = cal_weighted_avg(earns)
                    chosen_trade = {
                        'sim': sim_id,
                        'bought_date': bought_date,
                        'sell_date': sell_date,
                        'earn': earn,
                        'avg_earn': avg_earn
                    }
                    avg_earns.append(avg_earn)
                    combo_trades.append(chosen_trade)
        total_earn = np.sum(combo_earns)
        money = init_money * total_earn / 100
        avg_earn = np.sum(avg_earns) / len(avg_earns)
        num_earns = sum(x > 0 for x in combo_earns)
        trade_times = len(combo_earns)
        earning_rate = round(num_earns * 100 / trade_times, 2) if trade_times > 0 else 0
    return total_earn, avg_earn, earning_rate, trade_times, money, combo_trades

def update_combo_sims(db, combo_name, total_earn, avg_earn, earning_rate, trade_times, money, combo_trades, init_money=INIT_MONEY):
    the_combo_record = db.session.query(Simulator).join(Rule, Rule.id == Simulator.rule_id)\
                .filter(Rule.name == combo_name).first()
    if the_combo_record is None:
        rule_id = db.session.query(Rule.id).filter(Rule.name == combo_name).scalar()
        new_record = Simulator(
            rule_id=rule_id,
            init_money=init_money,
            current_money=money,
            current_shares=0,
            start_date=TEST_START_DATE,
            status=Status.running,
            cum_earn=total_earn,
            avg_earn=avg_earn,
            earning_rate=earning_rate,
            trading_times=trade_times
        )
        db.session.add(new_record)
        db.session.commit()
    else:
        the_combo_record.money = money
        the_combo_record.cum_earn = total_earn
        the_combo_record.avg_earn = avg_earn
        the_combo_record.earning_rate = earning_rate
        the_combo_record.trading_times = trade_times
        db.session.commit()
    return


if __name__ == '__main__':
    config_file = os.environ.get('CFG_PATH', '../../service.conf')
    init_global(config_file)
    db = global_var["db"]
    get_combo_earn(db)
