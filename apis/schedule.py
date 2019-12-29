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
    def delete(self, stuID, course_code):
        if not stuID:
            abort(400, message='Please provide `stuID`')
        if not course_code:
            abort(400, message='Please provide `course_code`')

        # get uid
        res = db.session.execute(
            text('SELECT uid FROM `user` WHERE username=:user'), {
                'user': stuID}
        )
        uid = res.fetchone()[0]

        # 判斷是否有這堂課
        res = db.session.execute(text('''
            SELECT * FROM curriculum WHERE uid= :uid AND course_code= :course_code AND year=\'1081\'
        '''), {
            'uid': uid,
            'course_code': course_code
        })

        if res.rowcount == 0:
            return {"result": "You don't have this course in 108-1"}, 400

        commentID = res.fetchone()['id']

        # 找到之後刪除
        db.session.execute(text('''
            DELETE FROM curriculum
            WHERE id=:id
        '''), {
            'id' : commentID
        })
        db.session.commit()
        return {"result": "Success",
                "course_code" : course_code}, 200


class Course_insert(Resource):
    @token_required
    def post(self, stuID, course_code):

        if not stuID:
            abort(400, message='Please provide `stuID`')
        if not course_code:
            abort(400, message='Please provide `course_code`')

        # stuID to uid
        res = db.session.execute(
            text('SELECT uid FROM `user` WHERE username=:user'), {
                'user': stuID}
        )

        uid = res.fetchone()[0]

        # Get user's course
        chose = db.session.execute(text('''
            SELECT * FROM curriculum WHERE uid=:stuID and year=1081
        '''), {
            'stuID': uid
        })


        # 0-index
        # timelist[week][period]
        timelist = [[0]*15 for i in range(7)]
        idx = ['', '2', '3']
        period = ['D0', 'D1', 'D2', 'D3', 'D4', 'DN', 'D5',
                  'D6', 'D7', 'D8', 'E0', 'E1', 'E2', 'E3', 'E4']
        day = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

        chose_course_code = []
        # change 1-idx
        chose_course_code.append('Garbage')

        cnt = 1

        # mark the course who have
        for row in chose:
            # duplicate
            if row['course_code'] == course_code:
                return {"message": "course_code duplicate"}, 400
            have = db.session.execute(text('''
                SELECT * FROM fju_course where course_code=:course_code
            '''), {
                'course_code': row['course_code']
            })
            chose_course_code.append(row['course_code'])
            for have_course in have:
                # enumerate Mon,Tue....
                for i in range(0, 7):
                     # enumerate day1,day2,day3
                    for m in idx:
                        if day[i] == have_course['day'+m]:
                            s = 0
                            e = 0
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

        # add course
        want_add = db.session.execute(text('''
        SELECT * FROM fju_course WHERE course_code=:course_code
        '''), {
            'course_code': course_code
        })

        if want_add.rowcount == 0:
            raise RuntimeError('Course_code {} is not exist'.format(course_code))

        # add course
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

        db.session.execute('INSERT INTO curriculum(uid, sid, course_code, year, pick, orig) VALUES (:uid, 68, :coursecode, 1081, 1, 0)',
        {
            'coursecode': course_code,
            'uid': uid
        })

        db.session.commit()

        return {'result': 'Success',
                'course_code': course_code}, 200
