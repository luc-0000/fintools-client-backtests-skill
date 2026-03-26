import base64
import decimal
import logging
from json import JSONEncoder


class APIException(Exception):
    def __init__(self, error_id, message=None, code='FAILURE'):
        self.error_id = error_id
        self.message = message if message is not None else str(error_id)
        self.code = code

    def to_dict(self):
        result = {
            "code": self.code,
            "id": self.error_id,
            "errMsg": self.message,
        }
        logging.error('{}: {}'.format(self.error_id, self.message))
        return result


class DecimalEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def format_base64_str(source):
    mod_length = len(source) % 4
    for i in range(0, 4 - mod_length, 1):
        source += '='
    result = base64.b64decode(source)
    return result


def has_error(rst):
    if type(rst) is dict and ('errMsg' in rst or 'error_msg' in rst):
        return True
    return False


def process_exception(code, message):
    rst = {"code":code,"message":message}
    # return abort(code, message=message)
    return rst


def build_error_response(err_code, err_msg):
    rst = {
        "code": err_code,
        "message": err_msg
    }
    return process_exception(err_code, rst)



def app_url(version, model, name):
    name = '/{}/{}{}'.format(version, model, name)
    return name


def getValueWithDefault(aMap, key, defaultVal=None):
    v = aMap.get(key, defaultVal)
    if v is None:
        v = defaultVal
    return v



def recogintion_url(name):
    name = '/{}'.format(name)
    return name
