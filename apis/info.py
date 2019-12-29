import datetime
from flask_restful import Resource
from sqlalchemy import text
from db import db

from utils import token_required
# TODO: this will be refactor to `models.py`
def get_uid(stuID):
    """Get the uid by the student ID"""
    res = db.session.execute(text('SELECT * FROM user WHERE username=:stuID'), {'stuID': stuID})
    if res.rowcount >= 1:
        return res.fetchone()['uid']
    else:
        raise RuntimeError('No uid referenced to {} in the db.'.format(stuID))
# TODO: this will be refactor to `models.py`
def get_school_name_by_sid(sid):
    res = db.session.execute(
        text('SELECT name FROM school WHERE sid=:sid LIMIT 1'), {'sid': sid})
    res = res.fetchone()[0]
    return res

def user_info_by_uid(uid):
    """Get user info by `uid`"""
    res = db.session.execute(text('''
        SELECT * FROM user WHERE uid=:uid
    '''), {'uid': uid})
    info = {
        'nickname': None,
        'score': None,
        'complete_course': None,
        'school': None,
        'department': None,
        'grade': None,
        'avg_grade': None,
        'last_login': None
    }
    if res.rowcount > 1:
        uids = []
        for i in res:
            uids.append(i['uid'])
        raise RuntimeError('Duplicate users in db: {}'.format(uids))
    elif res.rowcount == 0:
        return None
    # Only one user
    res = res.fetchone()
    info['nickname'] = res['nickname']
    info['score'] = res['curpoint']
    info['complete_course'] = res['complete_course']
    # get school
    info['school'] = get_school_name_by_sid(res['sid'])
    info['department'] = res['department']
    info['grade'] = res['grade']
    info['avg_grade'] = res['avg_grade']
    info['last_login'] = datetime.datetime.fromtimestamp(res['lastlogin']).strftime("%Y-%m-%d %H:%M:%S")
    return info

class StudentInfo(Resource):
    """API for query the information of a specific student\n
    methods:
        - get(stuID): returns the information of a specified `stuID`"""
    @token_required
    def get(self, stuID):
        uid = get_uid(stuID)
        info = user_info_by_uid(uid)
        return info, 200
