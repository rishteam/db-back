import datetime
from flask_restful import Resource
from sqlalchemy import text

import models
from db import db
from utils import token_required
# TODO: this will be refactor to `models.py`
def get_uid(stuID):
    """Get the uid by the student ID"""
    res = db.session.execute(text('SELECT * FROM user WHERE username=:stuID'), {'stuID': stuID})
    print('[*] debug : {}'.format(stuID))
    print('[*] debug : {}'.format(res.rowcount))
    if res.rowcount >= 1:
        u = res.fetchone()
        return u['uid']
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
    info = {}
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
    info['complete_point'] = res['complete_point']
    info['select_course'] = res['select_course']
    # get school
    info['school'] = get_school_name_by_sid(res['sid'])
    info['department'] = res['department']
    info['grade'] = res['grade']
    info['avg_score'] = res['avg_score']
    info['last_login'] = datetime.datetime.fromtimestamp(res['lastlogin']).strftime("%Y-%m-%d %H:%M:%S")
    return info

def get_num_of_selected_courses(uid):
    """Get the number of selected courses by uid\n
    column `select_course` in table `curriculum`"""
    res = db.session.execute(text(
        'SELECT COUNT(*) AS num FROM curriculum WHERE pick=1 AND uid=:uid'), {'uid': uid})
    if res.rowcount:
        return res.fetchone()['num']
    return 0

class StudentInfo(Resource):
    """API for query the information of a specific student\n
    methods:
        - get(stuID): returns the information of a specified `stuID`"""
    @token_required
    def get(self, stuID):
        uid = get_uid(stuID)

        # Update number of selected course of a user
        user = models.get_user(uid)
        models.set_user_select_course(uid, get_num_of_selected_courses(uid))

        info = user_info_by_uid(uid)
        return info, 200

    @token_required
    def patch(self, stuID):
        return 'NotImpletemented', 500
