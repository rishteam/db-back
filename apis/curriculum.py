from flask import Flask, request
from flask_restful import Api, Resource, abort, reqparse
from sqlalchemy import text, exc
import requests
import json
import datetime
import time

from db import db
from utils import token_required, md5
from crawler import course
import utils

CURR_UPDATE_TIME_LIMIT = datetime.timedelta(minutes=5)  # min
DISABLE_CURR_UPDATE_TIME_LIMIT = True

# Workaround: This is duplicate with get_uid inside `comment.py`
def get_uid(stuID):
    """Get the uid by the student ID"""
    res = db.session.execute(text('SELECT * FROM user WHERE username=:stuID'), {'stuID': stuID})
    if res.rowcount >= 1:
        return res.fetchone()['uid']
    else:
        raise RuntimeError('No uid referenced to {} in the db.'.format(stuID))

# TODO: move this to model
def insert_curriculum(uid, course_code, year, orig, pick, sid=68):
    """Insert a record into curriculum"""
    res = db.session.execute(text('''
        INSERT INTO curriculum (uid, sid, course_code, year, pick, orig) VALUES
        (:uid, :sid, :course_code, :year, :pick, :orig)
    '''), {
        'uid'        : uid,
        'sid'        : sid,
        'course_code': course_code,
        'year'       : year,
        'pick'       : pick,
        'orig'       : orig
    })
    # print(res.rowcount)
    # TODO: handle exception

def check_curriculum_updated(uid):
    """Checks if the curriculum has updated `CURR_UPDATE_TIME_LIMIT` ago\n
    Return: `bool`"""
    res = db.session.execute(text('SELECT * FROM Course.curriculum_check WHERE uid=:uid'), {'uid': uid})
    if res.rowcount:
        if res.rowcount > 1:
            raise RuntimeError('More than one uid existed in curriculum_check')
        p = res.fetchone() # person
        dt = utils.datetime_from_timestamp(p['time'])
        now = utils.datetime_now()
        return now - dt < CURR_UPDATE_TIME_LIMIT \
            or not DISABLE_CURR_UPDATE_TIME_LIMIT
    else:
        return False

def update_curriculum_check(uid):
    """Update the curriculum_check record by uid\n
    Return: `bool`"""
    # if not exist
    res = db.session.execute(text('SELECT id FROM Course.curriculum_check WHERE uid=:uid'), {'uid': uid})
    if not res.rowcount:
        res = db.session.execute(text('INSERT INTO Course.curriculum_check (uid, time) VALUES (:uid, :time)'), {'uid': uid, 'time': utils.time_now()})
        db.session.commit()
        return res.rowcount
    # Update
    res = db.session.execute(text('''
        UPDATE Course.curriculum_check SET time=:new_time WHERE uid=:uid
    '''), {
        'new_time': utils.time_now(),
        'uid': uid
    })
    db.session.commit()
    return res.rowcount

class CurriculumRes(Resource):
    TIME_LIMIT = datetime.timedelta(minutes=5)
    DISABLE_TIME_LIMIT = False

    @staticmethod
    def update_course_list_time(stuID):
        now = time.time()
        try:
            res = db.session.execute(text('UPDATE `Course`.`user` SET course_list_time=:time WHERE username=:username'),
            {'time': time.time(), 'username': stuID})
            db.session.commit()
        except exc.SQLAlchemyError as e:
            print(e)
            abort(500, message='Internal Server Error (Go to see the log)')
        return now

    @staticmethod
    def get_course_list_hash(stuID):
        res = db.session.execute(text('''
            SELECT course_list_hash, course_list FROM `Course`.`user`
            WHERE username=:username
        '''), {'username': stuID})
        res = res.fetchone()
        return res

    @staticmethod
    def update_course_list_and_hash(stuID, clist, clist_hash):
        try:
            res = db.session.execute(text('''
                UPDATE `Course`.`user`
                SET course_list=:clist, course_list_hash=:clist_hash
                WHERE username=:username
            '''), {
                'username': stuID,
                'clist': json.dumps(clist),
                'clist_hash': clist_hash
            })
        except exc.SQLAlchemyError as e:
            print(e)
            abort(500, message='Internal Server Error (Go to see the log)')
        db.session.commit()

    @staticmethod
    def update_curriculum(stuID, clist):
        """Update the curriculum by stuID"""
        uid = get_uid(stuID)
        if check_curriculum_updated(uid):
            print('[*] {}\'s curriculum is already updated'.format(stuID))
            return
        print('[*] Update {}\'s curriculum'.format(stuID))
        # Iterate through the whole record and insert each course into the curriculum
        for k in clist.keys():
            for course in clist[k]:
                insert_curriculum(uid, course['code'], k, True, False)
        update_curriculum_check(uid)
        db.session.commit()

    @token_required
    def get(self, stuID, year):
        year = str(year)
        res = db.session.execute(text('''
            SELECT password, course_list_time, course_list_hash FROM `Course`.`user`
            WHERE username=:username
        '''), {
            'username': stuID
        })
        if res.returns_rows and res.rowcount == 1:
            passwd, cltime, old_clist_hash = res.fetchone()
            # Maintain time
            if not cltime:
                cltime = CurriculumRes.update_course_list_time(stuID)
            cltime = datetime.datetime.fromtimestamp(cltime)
            time_delta = datetime.datetime.now() - cltime

            old_clist_hash, clist = CurriculumRes.get_course_list_hash(stuID)
            # Whether course list expired or not
            # or first time
            if time_delta >= CurriculumRes.TIME_LIMIT \
                or (clist == None and old_clist_hash == None) \
                or CurriculumRes.DISABLE_TIME_LIMIT:
                CurriculumRes.update_course_list_time(stuID)
                # Update list hash if necessary
                clist = course.get_course_list(stuID, passwd, None, course.ALL_YEAR) # FIXME: course.ALL_YEAR is not reflecting one's grade
                clist_hash = md5(clist)
                # Save the course list and hash if necessary
                if clist_hash != old_clist_hash:
                    CurriculumRes.update_course_list_and_hash(stuID, clist, clist_hash)
            # Not first time
            else:
                clist = json.loads(clist)
            CurriculumRes.update_curriculum(stuID, clist)
            # Leave only `year` data
            tmp = clist[year]
            clist.clear()
            clist[year] = tmp
        return clist, 200

class CurriculumList(Resource):
    @staticmethod
    def get_db_grade(stuID):
        res = db.session.execute(text('''
            SELECT grade FROM `Course`.`user` WHERE username=:user
        '''), {'user': stuID})
        if res.rowcount == 1:
            res = res.fetchone()[0]
        return int(res)
    @staticmethod
    def set_db_grade(stuID, grade):
        try:
            res = db.session.execute(text('''
                UPDATE `Course`.`user` SET grade=:grade WHERE username=:user
            '''), {'grade': grade, 'user': stuID})
        except exc.SQLAlchemyError as e:
            print(e)
            abort(500, message='Internal Server Error (Go to see the log)')
        db.session.commit()

    @token_required
    def get(self, stuID):
        r = requests.Session()
        # Get passwd of a user
        res = db.session.execute(text('''
            SELECT password FROM `Course`.`user`
            WHERE username=:username
        '''), {'username': stuID})
        # TODO: deprecate this check in the future
        if res.returns_rows and res.rowcount == 1:
            passwd = res.fetchone()[0]
        else:
            abort(404, message='User {} not found'.format(stuID))
        # Get grade of a user and return years
        db_grade = CurriculumList.get_db_grade(stuID)
        if db_grade == 0:
            grade = course.grade_to_num(course.get_person_identity(r, stuID, passwd)['grade'])
            CurriculumList.set_db_grade(stuID, grade)
        else:
            grade = db_grade
        rt = {'year': []}
        for year in range(course.CUR_YEAR, course.CUR_YEAR-grade, -1):
            for sem in range(2, 0, -1):
                # Not showing the future year
                if year == course.CUR_YEAR and sem > course.CUR_SEM:
                    continue
                rt['year'].append('{}{}'.format(year, sem))
        return rt, 200
