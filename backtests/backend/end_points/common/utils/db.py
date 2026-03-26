# coding=utf-8

import json
from datetime import datetime
from decimal import Decimal
from collections import defaultdict
from xml import etree
from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker

from end_points.common.utils.utils import get_dict_value
from db.models import PoolRuleEarn
from end_points.common.const.consts import DataBase


def getPoolRuleEarnModel(bind_key):
    """Get the PoolRuleEarn model class based on bind key

    Note: DH/DQ databases have been removed, all use the same model
    """
    # All bind keys now use the same PoolRuleEarn model
    return PoolRuleEarn




def get_row_id(db, Table, cond):
    record = db.session.query(Table).filter_by(**cond).first()
    if record is None:
        return None
    return record.id


def strip_value(value, strip):
    if value is None:
        return value
    if isinstance(value, str):
        if strip:
            value = value.strip()
    elif isinstance(value, Decimal):
        value = float(value)
    return value
    # return value.strip() if strip and value is not None and isinstance(value, str) else value


def build_rows_result(rows, items, process_none=True, json_items=[], strip=False):
    rst = []
    item_len = len(items)
    for row in rows:
        x = {}
        for i in range(0, item_len):
            name = items[i]
            if isinstance(row[i], datetime):
                x[name] = datetime.strftime(row[i], '%Y-%m-%d %H:%M:%S')
            elif name in json_items:
                try:
                    content = json.loads(row[i]) if row[i] is not None and row[i] != '' else ''
                except Exception as e:
                    content = row[i]
                x[name] = content
            elif process_none:
                value = row[i] if row[i] is not None else ''
                x[name] = strip_value(value, strip=strip)
            else:
                x[name] = strip_value(row[i], strip=strip)
        rst.append(x)
    return rst


def build_general_filter(TableClass, columns, keyword):
    filters = []
    for col in columns:
        filters.append(getattr(TableClass, col).ilike(keyword))
    return filters


def build_general_exact_filter(TableClass, columns, keyword):
    filters = []
    for col in columns:
        filters.append(getattr(TableClass, col) == keyword)
    return filters


def update_record(record, items, args):
    for item in items:
        if item in args and args[item] is not None:
            setattr(record, item, args[item])


def build_one_result(one, items, process_none=True, json_items=[]):
    record = {}
    for idx, item in enumerate(items):
        if item in json_items:
            record[item] = json.loads(one[idx]) if one[idx] is not None and one[idx] != '' else one[idx]
        else:
            record[item] = one[idx]
        if process_none and record[item] is None:
            record[item] = ''
    return record


def build_new_one_result(one, items, process_none=True, json_items=[]):
    record = {}
    for idx, item in enumerate(items):
        if item in json_items:
            record[item] = json.loads(one[idx]) if one[idx] is not None and one[idx] != '' else one[idx]
        else:
            record[item] = one[idx]
        try:
            if isinstance(one[idx], datetime):
                record[item] = datetime.strftime(one[idx], '%Y-%m-%d %H:%M:%S')
        except Exception as e:
            pass
        if process_none and record[item] is None:
            record[item] = ''
    return record


def update_table_record(db, keys, args, record):
    data = {}
    for key in keys:
        value = get_dict_value(args, key[1], None)
        if value is not None:
            data[key[0]] = value
    if len(data.keys()) > 0:
        items = [key[0] for key in keys]
        update_record(record, items, data)
        db.session.commit()
    return


def parseobj(html):
    parser = etree.HTML(html)
    return parser


def list_duplicates(seq):
    tally = defaultdict(list)
    for i, item in enumerate(seq):
        tally[item].append(i)
    return list((key, locs) for key, locs in tally.items() if len(locs) > 1)


def merge_values(dicts: dict):
    for k, v in dicts.items():
        dicts[k] = '。'.join(v)
    return dicts


def html2json(html):
    tags = parseobj(html).xpath('//h3/@bb_metadata')  # list
    text_split = html.split('</h3>')
    p_set = []
    for tag_html in text_split:
        content = ''.join(parseobj(tag_html).xpath('//p/text()'))  # list->str
        p_set.append(content)
    if len(set(tags)) == len(tags):
        ret = dict(zip(tags, p_set[1:]))
        return ret
    else:
        tmp = list(zip(tags, p_set[1:]))  # [(x, y), (...), ...]
        container = defaultdict(list)
        for k, v in tmp:
            container[k].append(v)
        return dict(merge_values(container))


def get_db():
    """Database dependency for FastAPI routes"""
    from end_points.config.global_var import global_var
    return global_var['db']


@contextmanager
def get_bind_session(db, bind_key):
    """
    Context manager to create a session bound to a specific database.
    Automatically closes the session when done to prevent resource leaks.

    Usage:
        with get_bind_session(db, bind_key) as session:
            result = session.query(MyModel).filter(...).first()
            session.add(new_record)
            session.commit()

    Args:
        db: Database wrapper object
        bind_key: The database bind key (e.g., DataBase.stocks)

    Yields:
        session: SQLAlchemy session bound to the specified database
    """
    engine = db.get_engine(bind_key)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


if __name__ == '__main__':
    pass
