from flask import Flask, request
from flask_restful import Api, Resource, abort, reqparse
from sqlalchemy import text, exc
import requests
import json
import time

from db import db
from utils import token_required
from crawler import course
import utils

class CurriculumRes(Resource):
    @token_required
    def get(self, stuID, year):
        year = str(year)
        # TODO: impl some time based updating course list mechanics
        res = db.session.execute(text('''
        SELECT password, course_list_time FROM `Course`.`user`
        WHERE username=:username
        '''), {
            'username': stuID
        })
        if res.returns_rows and res.rowcount == 1:
            passwd, cltime = res.fetchone()
            # Update list hash if necessary

            # Maintain time
            if not cltime:
                try:
                    res = db.session.execute(text('UPDATE `Course`.`user` SET course_list_time=:time WHERE username=:username'),
                    {'time': time.time(), 'username': stuID})
                except exc.SQLAlchemyError as e:
                    print(e)
                    abort(500, message='Internal Server Error (Go to see the log)')

            clist = course.get_course_list(stuID, passwd, None, [year])  # TODO: backup this
        return clist, 200

class CurriculumList(Resource):
    @token_required
    def get(self, stuID):
        r = requests.Session()
        # select user
        res = db.session.execute(text('''
            SELECT password FROM `Course`.`user`
            WHERE username=:username
        '''), {'username': stuID})
        if res.returns_rows and res.rowcount == 1:
            passwd = res.fetchone()[0]
        else:
            abort(404, message='User {} not found'.format(stuID))
        grade = course.grade_to_num(course.get_person_identity(r, stuID, passwd)['grade'])
        rt = {'year': []}
        for i, j in zip(course.ALL_YEAR, range(grade)):
            rt['year'].append(i)
        return rt, 200
