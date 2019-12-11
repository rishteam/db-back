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

class CurriculumRes(Resource):
    TIME_LIMIT = datetime.timedelta(minutes=5)
    DISABLE_TIME_LIMIT = False

    @staticmethod
    def update_course_list_time(stuID):
        try:
            res = db.session.execute(text('UPDATE `Course`.`user` SET course_list_time=:time WHERE username=:username'),
            {'time': time.time(), 'username': stuID})
            db.session.commit()
        except exc.SQLAlchemyError as e:
            print(e)
            abort(500, message='Internal Server Error (Go to see the log)')

    @token_required
    def get(self, stuID, year):
        year = str(year)
        # TODO: impl some time based updating course list mechanics
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
                CurriculumRes.update_course_list_time(stuID)
            cltime = datetime.datetime.fromtimestamp(cltime)
            time_delta = datetime.datetime.now() - cltime
            # print('prev = {}'.format(cltime))
            # print('delta = {}'.format(time_delta))
            # Whether course list expired or not
            if time_delta >= CurriculumRes.TIME_LIMIT or CurriculumRes.DISABLE_TIME_LIMIT:
                CurriculumRes.update_course_list_time(stuID)
                # Update list hash if necessary
                clist = course.get_course_list(stuID, passwd, None, course.ALL_YEAR) # FIXME: course.ALL_YEAR is not reflecting one's grade
                clist_hash = md5(clist)
                # Save the course list and hash if necessary
                if clist_hash != old_clist_hash:
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
                # print('> hash={}'.format(clist_hash))
            else:
                res = db.session.execute(text('SELECT course_list FROM `Course`.`user` WHERE username=:username'), {'username': stuID})
                if res.rowcount:
                    clist_json = res.fetchone()[0]
                    clist = json.loads(clist_json)
            tmp = clist[year]
            clist.clear()
            clist[year] = tmp
        return clist, 200

class CurriculumList(Resource):
    @token_required
    def get(self, stuID):
        r = requests.Session()
        # Get passwd of a user
        res = db.session.execute(text('''
            SELECT password FROM `Course`.`user`
            WHERE username=:username
        '''), {'username': stuID})
        if res.returns_rows and res.rowcount == 1:
            passwd = res.fetchone()[0]
        else:
            abort(404, message='User {} not found'.format(stuID))
        # Get grade of a user and return years
        grade = course.grade_to_num(course.get_person_identity(r, stuID, passwd)['grade'])
        rt = {'year': []}
        for i, j in zip(course.ALL_YEAR, range(grade)):
            rt['year'].append(i)
        return rt, 200
