import re
from functools import wraps
from flask_restful import reqparse, abort
from sqlalchemy import text
import json
import hashlib
import time
import datetime
#
from db import db

token_parser = reqparse.RequestParser()
token_parser.add_argument('Authorization', type=str, location='headers', required=True)

def check_user_exist(stuID):
    res = db.session.execute(
        text('SELECT uid FROM `user` WHERE username=:user'), {'user': stuID}
    )
    return res.returns_rows and res.rowcount >= 1

def check_token(stuID, token):
    res = db.session.execute(
        text('SELECT token FROM `user` WHERE username=:user'), {'user': stuID}
    )
    if res.returns_rows and res.rowcount == 1:
        act_token = res.fetchone()[0]
        return act_token == token
    else:
        raise RuntimeError


def check_null(data):
    if len(str(data)) == 0:
        return ''
    else:
        return data

def token_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        header = token_parser.parse_args()
        try:
            t, h = header['Authorization'].split()
        except ValueError as e:
            print(e)
            abort(400, message='Bad token')
        stuID = kwargs['stuID']
        # check user
        if not check_user_exist(stuID):
            abort(404, message='User not found')

        if not re.match('^[a-f0-9]{32}$', h):
            abort(400, message='Bad token')
        if t != 'Digest':
            abort(400, message='Bad token')
        if not check_token(stuID, h):
            abort(400, message='Bad token')
        return func(*args, **kwargs)
    return wrapper

def result_msg(s):
    return {'message': s}

def api_prefix(s):
    return '/db/v1' + s

def md5(s, salt=''):
    if isinstance(s, str):
        s = s.encode('utf-8')
    elif isinstance(s, dict):
        json_dic = json.dumps(s, sort_keys=True)
        return md5(json_dic)
    return hashlib.md5(s).hexdigest()

# https://stackoverflow.com/questions/475074/regex-to-parse-or-validate-base64-data
B64_REGEX = re.compile('^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{4})$')

def datetime_from_timestamp(ts):
    """Return a datetime converted from a timestamp"""
    return datetime.datetime.fromtimestamp(ts)

def datetime_now():
    return datetime.datetime.now()

def time_from_datetime(dt):
    raise NotImplementedError

def time_now():
    return time.time()
