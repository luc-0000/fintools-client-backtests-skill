#!/usr/bin/env python
# encoding=utf8
"""
SQLite database model definitions for the backtests backend.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, DOUBLE, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class StockIndex(Base):
    __tablename__ = "stock_index"
    code = Column(String(64), nullable=False, primary_key=True)
    name = Column(String(64), nullable=False)
    se = Column(String(64), nullable=False)
    created_at = Column(DateTime, nullable=True, default=datetime.now)
    updated_at = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)


class Stock(Base):
    __tablename__ = "stock"
    code = Column(String(64), nullable=False, primary_key=True, comment="代码")
    name = Column(String(64), nullable=False, comment="名称")
    se = Column(String(64), nullable=False, comment="交易所")
    type = Column(String(64), nullable=True, comment="类型")
    index_code = Column(String(64), nullable=True, comment="指数代码")
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class UpdatingStock(Base):
    __tablename__ = "updating_stock"
    id = Column(Integer, autoincrement=True, primary_key=True)
    stock_code = Column(String(32), unique=True, nullable=False)
    starting_date = Column(DateTime, nullable=True, default=None)
    done = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class StocksInPool(Base):
    __tablename__ = "stocks_in_pool"
    code = Column(String(64), nullable=False, primary_key=True)
    cap = Column(DOUBLE, nullable=True)
    pe = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=True, default=datetime.now)
    updated_at = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)


class Pool(Base):
    __tablename__ = "pool"
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(32), nullable=False, comment="分类名")
    stocks = Column(Integer, nullable=False, default=0, comment="股票数量")
    latest_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True, default=datetime.now)
    updated_at = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)


class PoolStock(Base):
    __tablename__ = "pool_stock"
    id = Column(Integer, autoincrement=True, primary_key=True)
    stock_code = Column(String(32), nullable=False, comment="股票代码")
    pool_id = Column(Integer, nullable=False, comment="股票池ID")
    created_at = Column(DateTime, nullable=True, default=datetime.now)
    updated_at = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)


class Rule(Base):
    __tablename__ = "rule"
    id = Column(Integer, autoincrement=True, primary_key=True, comment="规则ID")
    name = Column(String(255), nullable=False)
    type = Column(String(255), nullable=False)
    info = Column(String(255), nullable=False)
    description = Column(String(255), nullable=False)
    agent_id = Column(String(255), nullable=True, unique=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class RulePool(Base):
    __tablename__ = "rule_pool"
    id = Column(Integer, autoincrement=True, primary_key=True)
    rule_id = Column(Integer, nullable=False, comment="规则ID")
    pool_id = Column(Integer, nullable=False, comment="股票池ID")
    created_at = Column(DateTime, nullable=True, default=datetime.now)
    updated_at = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)


class StockRuleEarn(Base):
    __tablename__ = "stock_rule_earn"
    id = Column(Integer, autoincrement=True, primary_key=True)
    stock_code = Column(String(64), nullable=False, comment="股票代码")
    rule_id = Column(Integer, nullable=False, comment="规则ID")
    earn = Column(Float, nullable=True, comment="累计收益")
    avg_earn = Column(Float, nullable=True, comment="平均收益")
    earning_rate = Column(Float, nullable=True, comment="盈利率")
    trading_times = Column(Integer, nullable=True, comment="交易次数")
    status = Column(String(32), nullable=True, default="normal")
    indicating_date = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class PoolRuleEarn(Base):
    __tablename__ = "pool_rule_earn"
    id = Column(Integer, autoincrement=True, primary_key=True)
    pool_id = Column(Integer, nullable=False, comment="股票池ID")
    rule_id = Column(Integer, nullable=False, comment="规则ID")
    earn = Column(Float, nullable=True, comment="累计收益")
    avg_earn = Column(Float, nullable=True, comment="平均收益")
    earning_rate = Column(Float, nullable=True, comment="盈利率")
    trading_times = Column(Integer, nullable=True, comment="交易次数")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class Simulator(Base):
    __tablename__ = "simulator"
    id = Column(Integer, autoincrement=True, primary_key=True)
    stock_code = Column(String(32), nullable=True)
    rule_id = Column(Integer, nullable=False)
    start_date = Column(DateTime, nullable=True)
    status = Column(String(32), nullable=False, default="running")
    init_money = Column(Float, default=10000)
    current_money = Column(Float, default=10000)
    current_shares = Column(Text, default=0)
    cum_earn = Column(Float, nullable=True, comment="累计收益")
    avg_earn = Column(Float, nullable=True, comment="平均收益")
    earning_rate = Column(Float, nullable=True, comment="盈利率")
    trading_times = Column(Integer, nullable=True, comment="交易次数")
    indicating_date = Column(DateTime, nullable=True)
    earning_info = Column(Text, nullable=True, comment="收益信息")
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class SimTrading(Base):
    __tablename__ = "simulator_trading"
    id = Column(Integer, autoincrement=True, primary_key=True)
    sim_id = Column(Integer, nullable=False)
    stock = Column(String(64), nullable=False, default="stock")
    trading_date = Column(DateTime, nullable=False)
    trading_type = Column(String(64), nullable=False, default="buy")
    trading_amount = Column(Float, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class SimulatorConfig(Base):
    __tablename__ = "simulator_config"
    id = Column(Integer, primary_key=True, autoincrement=True)
    profit_threshold = Column(Float, default=0, comment="利润阈值百分比")
    stop_loss = Column(Float, default=5, comment="止损百分比")
    max_holding_days = Column(Integer, default=5, comment="最大持有天数")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_at = Column(DateTime, default=datetime.now)


class AgentTrading(Base):
    __tablename__ = "agent_trading"
    __table_args__ = (
        UniqueConstraint("rule_id", "stock", "trading_date", name="uq_rule_stock_date"),
    )
    id = Column(Integer, autoincrement=True, primary_key=True)
    rule_id = Column(Integer, nullable=False, comment="规则ID")
    stock = Column(String(64), nullable=False, default="stock")
    trading_date = Column(DateTime, nullable=False)
    trading_type = Column(String(64), nullable=False, default="buy")
    trading_amount = Column(Float, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
