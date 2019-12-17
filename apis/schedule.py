from flask import Flask, request
from flask_restful import Api, Resource, abort, reqparse
from sqlalchemy import text

from db import db
from utils import token_required


def debug(period, timelist):
    for j in range(0, 15):
        print(period[j], end=' ')
        print()
        for i in range(0, 7):
            for j in range(0, 15):
                print(timelist[i][j], end=' ')
            print()

class Course_delete(Resource):
    @token_required
    def delete(self, stuID, delete_course_code):
        # get uid
        res = db.session.execute(
            text('SELECT uid FROM `user` WHERE username=:user'), {
                'user': stuID}
        )
        uid = res.fetchone()[0]

        # 判斷是否有這堂課
        res = db.session.execute(text('''
            SELECT * FROM curriculum WHERE uid= :uid AND course_code= :course_code
        '''), {
            'uid': uid,
            'course_code': delete_course_code
        })
        if res.rowcount == 0:
            return {"result": "You don't have this course"}, 400

        # 找到之後刪除
        db.session.execute(text('''
            DELETE FROM curriculum
            WHERE uid=:uid AND course_code=:course_code
        '''), {
            'uid': uid,
            'course_code': delete_course_code
        })
        db.session.commit()
        return {"result": "success"}, 200


class Course_insert(Resource):
    @token_required
    def post(self, stuID, add_course_code):

        res = db.session.execute(
            text('SELECT uid FROM `user` WHERE username=:user'), {
                'user': stuID}
        )

        uid = res.fetchone()[0]

        # 已選到的課
        chose = db.session.execute(text('''
            SELECT * FROM curriculum WHERE uid=:stuID
        '''), {
            'stuID': uid
        })



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

        # 先劃上選到的課
        for row in chose:
            # 重複選課
            if row['course_code'] == add_course_code:
                return {"message": "course_code duplicate"}, 400
            have = db.session.execute(text('''
                SELECT * FROM fju_course where course_code=:course_code
            '''), {
                'course_code': row['course_code']
            })
            chose_course_code.append(row['course_code'])
            for have_course in have:
                for m in idx:
                    for i in range(0, 7):
                        if day[i] == have_course['day'+m]:
                            e = 0
                            s = 0
                            for j in range(0, 15):
                                if period[j] == str(have_course['period'+m])[0:2]:
                                        s = j
                                elif period[j] == str(have_course['period'+m])[3:5]:
                                        e = j
                            for k in range(0, e-s+1):
                                timelist[i][s+k] = cnt
                cnt += 1
        # DEBUG
        # debug(period, timelist)

        # 加上要選之課程
        want_add = db.session.execute(text('''
        SELECT * FROM fju_course WHERE course_code=:course_code
        '''), {
            'course_code': add_course_code
        })

        if want_add.rowcount == 0:
            return {
                "message": "Course_code error"
            }, 400
        # 示範: D510304623 E1~E3
        for row in want_add:
            for m in idx:
                for i in range(0, 7):
                    if day[i] == row['day'+m]:
                        s = 0
                        e = 0
                        for j in range(0, 15):
                            if period[j] == str(row['period'+m])[0:2]:
                                s = j
                            elif period[j] == str(row['period'+m])[3:5]:
                                e = j
                        for k in range(0, e-s+1):
                                if timelist[i][s+k] != 0:
                                    return {'result': False,
                                            'course_code': chose_course_code[timelist[i][s+k]]}, 400

        db.session.execute('Insert into curriculum(uid, sid, course_code) values (:uid, 68, :coursecode)',
        {
            'coursecode': add_course_code,
            'uid': uid
        })
        db.session.commit()

        return {'result': 'Success',
                'course_code': add_course_code}, 200
