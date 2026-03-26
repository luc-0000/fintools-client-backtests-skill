import os
from datetime import datetime
from pprint import pprint as default_pprint


def get_dict_value(d, key, default=None):
    v = d.get(key, default)
    if v is None:
        v = default
    return v


def info(*args, **kwargs):
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), end=' ')
    print(*args, **kwargs)


def is_debug():
    return 'AR_DEBUG' in os.environ and int(os.environ['AR_DEBUG']) != 0


def debug(*args, **kwargs):
    if is_debug():
        info(*args, **kwargs)


def pprint(*objs):
    for obj in objs:
        default_pprint(obj)


def read_param(params, key, default=None, strict=False):
    if params is not None and key in params:
        return params[key]
    else:
        if strict:
            raise Exception('read param [{0}] is not find'.format(key))
        else:
            return default


def _read_param_m_next(params, keys, default=None, strict=False):
    if len(keys) == 1:
        return read_param(params, keys[0], default, strict)
    else:
        if keys[0] in params:
            return _read_param_m_next(params[keys[0]], keys[1:], default, strict)
        else:
            return read_param(params, keys[0], default, strict)


def read_param_m(params, keys, default=None, strict=False):
    return _read_param_m_next(params, keys, default, strict)


def getValueAvailable(value, str_val=[]):
    """Check if value is available (not None, empty string, or empty whitespace)"""
    str_val = [None, '', ' '] if len(str_val) == 0 else str_val

    if isinstance(value, str):
        if value is not None and value not in str_val:
            return True
    elif isinstance(value, list):
        if value is not None and value != []:
            return True
    elif isinstance(value, dict):
        if value is not None and value != {}:
            return True
    elif value is not None:
        return True
    return False


def sort_dict_with_none(dict, key, reverse=False):
    """Sort list of dicts, placing None values at the end"""
    return sorted(dict, key=lambda x: float('-inf') if x.get(key) is None else x.get(key), reverse=reverse)
