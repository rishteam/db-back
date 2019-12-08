from flask import Flask, request
from flask_restful import Api, Resource, abort, reqparse
from sqlalchemy import text
import requests
import json
import datetime
import time

from db import db
import config
app = Flask(__name__)
app.config.from_object(config)
api = Api(app)

db.init_app(app)


def api_prefix(s):
  return '/db/v1' + s

class FJU_course(Resource):
    def get(self):
        res = db.session.execute(text('SELECT * FROM fju_course limit 100'))
        
        items = []
        for row in res:
            items.append({
                         'course_code': row['course_code'],
                         'name': row['name'],
                         'teacher': row['teacher'],
                         'department': row['department'],
                         'day': row['day'],
                         'week': row['week'],
                         'period': row['period'],
                         'classroom': row['classroom']
                         })
        return items, 200


class Course_insert(Resource):
    def post(self, uid, add_course_code):

        chose = db.session.execute(text('''
        SELECT * FROM curriculum where uid=:uid
        '''),
        {
            'uid': uid
        })

        uid_exist = db.session.execute(text('''
            SELECT * FROM user where uid=:uid     
        '''),
        {
            'uid':uid
        })

        if uid_exist.rowcount == 0:
            return {
                "message": "uid error"
            },400;
    
        # 0-index
        timelist = [[0]*15 for i in range(7)]
        idx = ['', '2', '3']
        period = ['D0', 'D1', 'D2', 'D3', 'D4', 'DN', 'D5',
                  'D6', 'D7', 'D8', 'E0', 'E1', 'E2', 'E3', 'E4']
        day = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        chose_course_code = []
        # 配合1-index
        chose_course_code.append('Garbage')
        cnt = 1

        # 重複選課


        # 先劃上選到的課
        for row in chose:
            if row['course_code'] == add_course_code:
                return {
                    "message": "Course_code duplicate"
                },400
            have = db.session.execute(text('''
            SELECT * FROM fju_course where course_code=:course_code
            '''),
            {
                'course_code': row['course_code']
            })
            chose_course_code.append(row['course_code'])
            for have_course in have:
                for m in idx:
                    for i in range(0,7):
                        if day[i] == have_course['day'+m]:
                            e = 0
                            s = 0 
                            for j in range(0,15):
                                if period[j] == str(have_course['period'+m])[0:2]:
                                    s = j
                                elif period[j] == str(have_course['period'+m])[3:5]:
                                    e = j
                            for k in range(0,e-s+1):
                                timelist[i][s+k] = cnt
                                    
                cnt += 1
        # DEBUG
        for j in range(0,15):
            print(period[j], end=' ')
        print()
        for i in range(0,7):
            for j in range(0,15):
                print(timelist[i][j], end=' ')
            print()


        # 現在加上要選之課程
        want_add = db.session.execute(text('''
        SELECT * FROM fju_course WHERE course_code=:course_code
        '''), {
            'course_code': add_course_code
        })

        if want_add.rowcount == 0:
            return {
                "message": "Course_code error"
            },400
        # 示範: D510304623 E1~E3
        for row in want_add:
            for m in idx:
                for i in range(0,7):
                    if day[i] == row['day'+m]:
                        s = 0
                        e = 0
                        for j in range(0,15):
                            if period[j] == str(row['period'+m])[0:2]:
                                s = j
                            elif period[j] == str(row['period'+m])[3:5]:
                                e = j
                        for k in range(0,e-s+1):
                            if timelist[i][s+k] != 0:
                                return {'result' : False,
                                        'course_code': chose_course_code[timelist[i][s+k]]}, 400
        

        db.session.execute('Insert into curriculum(uid, sid, course_code) values (:uid, 68, :coursecode)',{'coursecode' : add_course_code, 'uid': uid} )
        db.session.commit()
        return {'result': 'Success',
                'course_code': add_course_code}, 200

                        

api.add_resource(FJU_course, api_prefix('/fju_course'))
api.add_resource(Course_insert, api_prefix('/fju_course/<int:uid>/<string:add_course_code>'))


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=80)
