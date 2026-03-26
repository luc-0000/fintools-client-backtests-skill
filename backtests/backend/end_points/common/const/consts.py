
MAX_PAGE_SIZE = 10000
INIT_MONEY = 50000
INIT_MONEY_PER_STOCK = INIT_MONEY/3

# Global sell condition parameters for all simulators
PROFIT_THRESHOLD = 0      # Profit threshold percentage (0 = sell when price > buy price)
STOP_LOSS = 5             # Stop loss percentage
MAX_HOLDING_DAYS = 5      # Maximum holding days before forced sell

class DataBase:
    ai_stock = 'fintools_backtest'  # Legacy - not used in Agent system
    stocks = 'cn_stocks'   # Main database (fintools_backtest)
    stocks_m = 'cn_stocks_m'
    stocks_in_pool = 'cn_stocks_in_pool'
    # DH/DQ databases removed - all use the same stocks database

class Trade:
    buy = 'buy'
    sell = 'sell'
    hold = 'hold'
    not_indicating = 'not_indicating'
    indicating = 'indicating'
    fail_to_buy = 'fail_to_buy'
    fail_to_sell = 'fail_to_sell'
    not_sufficient_to_buy = 'not_sufficient_to_buy'

class Status:
    created = 'created'
    running = 'running'
    indicating = 'indicating'
    holding = 'holding'
    stopped = 'stopped'
    normal = 'normal'

class DataMode:
    train = 'train'
    validate = 'validate'
    test = 'test'

class RuleType:
    agent = 'agent'
    remote_agent = 'remote_agent'

class RL_ENV_Mode:
    train_open = 'train_open'
    validate = 'validate'
    test = 'test'

class ComboName:
    above_20 = 'above_20'
    best_k = 'best_k'

# Model training constants
import pandas as pd

TEST_START_DATE = pd.Timestamp(year=2025, month=1, day=1)
RL_TEST_START_DATE = pd.Timestamp(2024, 7, 1, 0)
RL_VAL_START_DATE = pd.Timestamp(2024, 1, 1, 0)
FILL_NUM = 0  # Fill number for RL data preprocessing
M = 240  # Moving window size for LSTM models
