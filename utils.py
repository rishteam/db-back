import re
from functools import wraps
from flask_restful import reqparse, abort
from sqlalchemy import text
#
from db import db

token_parser = reqparse.RequestParser()
token_parser.add_argument('Authorization', type=str, location='headers', required=True)

def check_user_exist(stuID):
    res = db.session.execute(
        text('SELECT uid FROM `user` WHERE username=:user'), {'user': stuID}
    )
    return res.returns_rows and res.rowcount >= 1

def check_token(stdID, token):
    res = db.session.execute(
        text('SELECT token FROM `user` WHERE username=:user'), {'user': stdID}
    )
    if res.returns_rows and res.rowcount == 1:
        act_token = res.fetchone()[0]
        return act_token == token
    else:
        raise RuntimeError

def token_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        header = token_parser.parse_args()
        t, h = header['Authorization'].split()
        stuID = kwargs['stuID']
        # check user
        if not check_user_exist(stuID):
            abort(404, message='User not found')

        # TODO: user regex to santitize hash
        if t == 'Digest' and re.match('^ [a-f0-9]{32}$', h):
            if not check_token(stuID, h):
                abort(400, message='Bad token')
        return func(*args, **kwargs)
    return wrapper

def result_msg(s):
    return {'message': s}
