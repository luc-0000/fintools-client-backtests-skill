#!/usr/bin/python
# encoding=utf8
"""
Dynamic SQLite model definitions used by backtests.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.orm import declarative_base

from end_points.common.const.consts import DataBase

DynamicBase = declarative_base(class_registry=dict())


def record_table_attr(table_name, bind_key):
    return {
        "__tablename__": table_name,
        "__bind_key__": bind_key,
        "id": Column(Integer, autoincrement=True, primary_key=True),
        "stock_code": Column(String(12), unique=True, nullable=False, comment="stock code"),
        "starting_date": Column(DateTime, nullable=True, default=None),
        "done": Column(Boolean, nullable=False, default=False),
        "created_at": Column(DateTime, nullable=True, default=datetime.now),
    }


def cn_stock_table_attr(table_name, bind_key):
    return {
        "__tablename__": table_name,
        "__table_args__": {"keep_existing": True},
        "__bind_key__": bind_key,
        "id": Column(Integer, autoincrement=True, primary_key=True),
        "date": Column(DateTime, unique=True, nullable=False, comment="d"),
        "open": Column(Float, nullable=True, comment="o"),
        "high": Column(Float, nullable=True, comment="h"),
        "low": Column(Float, nullable=True, comment="l"),
        "close": Column(Float, nullable=True, comment="c"),
        "volume": Column(Integer, nullable=True, comment="v"),
        "turnover": Column(Float, nullable=True, comment="to"),
        "turnover_rate": Column(Float, nullable=True, comment="to rate"),
        "shake_rate": Column(Float, nullable=True, comment="sk rate"),
        "change_rate": Column(Float, nullable=True, comment="change"),
        "change_amount": Column(Float, nullable=True, comment="change"),
        "jlrl": Column(Float, nullable=True, comment="jlrl"),
        "zljlrl": Column(Float, nullable=True, comment="zljlrl"),
        "hyjlrl": Column(Float, nullable=True, comment="hyjlrl"),
        "created_at": Column(DateTime, nullable=True, default=datetime.now),
        "updated_at": Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now),
    }


def get_stock_model(stock_code, bind_key=DataBase.stocks):
    class MyModel(DynamicBase):
        __tablename__ = stock_code
        __bind_key__ = bind_key
        id = Column(Integer, autoincrement=True, primary_key=True)
        date = Column(DateTime, unique=True, nullable=False, comment="d")
        open = Column(Float, nullable=True, comment="o")
        high = Column(Float, nullable=True, comment="h")
        low = Column(Float, nullable=True, comment="l")
        close = Column(Float, nullable=True, comment="c")
        volume = Column(Integer, nullable=True, comment="v")
        turnover = Column(Float, nullable=True, comment="to")
        turnover_rate = Column(Float, nullable=True, comment="to rate")
        shake_rate = Column(Float, nullable=True, comment="sk rate")
        change_rate = Column(Float, nullable=True, comment="change")
        change_amount = Column(Float, nullable=True, comment="change")
        jlrl = Column(Float, nullable=True, comment="jlrl")
        zljlrl = Column(Float, nullable=True, comment="zljlrl")
        hyjlrl = Column(Float, nullable=True, comment="hyjlrl")
        created_at = Column(DateTime, nullable=True, default=datetime.now)
        updated_at = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now)

    return MyModel


def cn_index_table_attr(table_name, bind_key):
    return {
        "__tablename__": table_name,
        "__table_args__": {"keep_existing": True},
        "__bind_key__": bind_key,
        "id": Column(Integer, autoincrement=True, primary_key=True),
        "date": Column(DateTime, unique=True, nullable=False, comment="d"),
        "open": Column(Float, nullable=True, comment="o"),
        "high": Column(Float, nullable=True, comment="h"),
        "low": Column(Float, nullable=True, comment="l"),
        "close": Column(Float, nullable=True, comment="c"),
        "volume": Column(Integer, nullable=True, comment="v"),
        "turnover": Column(Float, nullable=True, comment="to"),
        "turnover_rate": Column(Float, nullable=True, comment="to rate"),
        "shake_rate": Column(Float, nullable=True, comment="sk rate"),
        "change_rate": Column(Float, nullable=True, comment="change"),
        "change_amount": Column(Float, nullable=True, comment="change"),
        "created_at": Column(DateTime, nullable=True, default=datetime.now),
        "updated_at": Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now),
    }
