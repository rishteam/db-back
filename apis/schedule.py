import json
import datetime
from flask import Flask, request
from flask_restful import Api, Resource, abort, reqparse
from sqlalchemy import text

from db import db
import utils
from utils import token_required, check_null, md5
import models

import re
import requests

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

        row = res.fetchone()
        if row['orig'] == 1:
            return {"result": "Falied",
                    "message": "You cannot delete origin course"}, 400
        commentID = row['id']


        # 找到之後刪除
        db.session.execute('DELETE FROM curriculum WHERE id=:id', {'id' : commentID})
        db.session.commit()

        # Update user.schedule_data_changed
        db.session.execute('UPDATE user SET schedule_data_changed=1 WHERE uid=:uid', {'uid': uid})
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
                                if period[j] == str(have_course['period'+m])[3:5]:
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

        res = db.session.execute(text('''
        SELECT * FROM curriculum WHERE course_code=:course_code
        '''), {
            'course_code': course_code
        })

        # the course which is in the curriculum and orig is true
        if res.rowcount > 0:
            row = res.fetchone()
            # print(row)
            if row['orig'] == 1:
                return {"result": "Falied",
                        "message": "You cannot insert origin course"}, 400

        # add course
        for row in want_add:
            for m in idx:
                for i in range(0, 7):
                    if day[i] == row['day'+m]:
                        s = 0
                        e = 0
                        # print(row['period'])
                        for j in range(0, 15):
                            if period[j] == str(row['period'+m])[0:2]:
                                s = j
                            if period[j] == str(row['period'+m])[3:5]:
                                e = j
                        # print(s,e)
                        for k in range(0, e-s+1):
                                # print(s+k)
                                if timelist[i][s+k] != 0:
                                    return {'result': False,
                                            'course_code': chose_course_code[timelist[i][s+k]]}, 400

        db.session.execute('INSERT INTO curriculum(uid, sid, course_code, year, pick, orig) VALUES (:uid, 68, :coursecode, 1081, 1, 0)', {
            'coursecode': course_code,
            'uid': uid
        })
        db.session.commit()

        # Update user.schedule_data_changed
        db.session.execute('UPDATE user SET schedule_data_changed=1 WHERE uid=:uid', {'uid': uid})
        db.session.commit()

        return {'result': 'Success',
                'course_code': course_code}, 200

def make_CoursePeriod(x):
    """Turn the str 'D?-D?' into the CoursePeriod"""
    if re.match(r'^((?:D(?:[0-8]|N)|E[0-4])-(?:D(?:[0-8]|N)|E[0-4]))$', x):
        p = x.split('-')
        return CoursePeriod(*p)
    else:
        raise RuntimeError('Cannot make the CoursePeriod: {}'.format(x))

class CoursePeriod:
    """Struct for period of a course"""
    ALL_PERIOD = ['D0', 'D1', 'D2', 'D3', 'D4', 'DN',
                  'D5', 'D6', 'D7', 'D8', 'E0', 'E1', 'E2', 'E3', 'E4']
    PERIOD2IDX = {'D0': 0, 'D1': 1, 'D2': 2, 'D3': 3, 'D4': 4, 'DN': 5, 'D5': 6,
                  'D6': 7, 'D7': 8, 'D8': 9, 'E0': 10, 'E1': 11, 'E2': 12, 'E3': 13, 'E4': 14}

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __contains__(self, item):
        """a in b"""
        if not isinstance(item, type(self)):
            raise TypeError(
                'The item should be CoursePeriod not {}'.format(type(item)))
        p2i = CoursePeriod.PERIOD2IDX
        return p2i[self.start] <= p2i[item.start] and p2i[item.end] <= p2i[self.end]

    def __repr__(self):
        return '<CoursePeriod start={} end={}>'.format(self.start, self.end)

    def __str__(self):
        return '{}-{}'.format(self.start, self.end)

class Auto_course_insert(Resource):
    @staticmethod
    def get_free_period(uid, timelist):
        idx = ['', '2', '3']
        period = ['D0', 'D1', 'D2', 'D3', 'D4', 'DN', 'D5',
            'D6', 'D7', 'D8', 'E0', 'E1', 'E2', 'E3', 'E4']
        day = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

        res = db.session.execute(text("SELECT * FROM curriculum WHERE uid=:uid AND year=\'1081\'"), {'uid' : uid})

        # place the course
        for row in res:
            # print(row['course_code'])
            have = db.session.execute(text('SELECT * FROM fju_course where course_code=:course_code'), {'course_code': row['course_code']})
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
                                if period[j] == str(have_course['period'+m])[3:5]:
                                        e = j
                            for k in range(0, e-s+1):
                                timelist[i][s+k] = 1
        # debug(period, timelist)
        space_time = [ [] for i in range(7) ]

        # show space_time
        for d in range(0,7):
            i = 0
            while i < 15:
                if timelist[d][i] == 0:
                    for j in range(i,15):
                        if j == 14 and timelist[d][j] == 0:
                            space_time[d].append(str(period[i] + '-' + period[14]))
                            i = j
                            break
                        if timelist[d][j] == 1:
                            space_time[d].append(str(period[i] + '-' + period[j-1]))
                            i = j
                            break
                i += 1

        return space_time

    TIME_LIMIT = datetime.timedelta(minutes=5)
    DISABLE_TIME_LIMIT = False

    @staticmethod
    def load_schedule_data(uid):
        res = db.session.execute(text('SELECT schedule_data FROM user WHERE uid=:uid'), {'uid': uid})
        return res.fetchone()['schedule_data']

    @staticmethod
    def load_schedule_data_if_not_expired(uid):
        """Load the schedule data in dict if not expired"""
        # Get time and time check
        user = models.get_user(uid)
        # if the schedule needed to update (course insert/delete)
        if user['schedule_data_changed']:
            db.session.execute(text('UPDATE user SET schedule_data_changed=0 WHERE uid=:uid'), {'uid': uid})
            db.session.commit()
            return None
        # time expired?
        last = user['schedule_data_time']
        if not last:
            return None
        last = utils.datetime_from_timestamp(last)

        if not Auto_course_insert.DISABLE_TIME_LIMIT and utils.time_limit_check(last, Auto_course_insert.TIME_LIMIT):
            d = Auto_course_insert.load_schedule_data(uid)
            if d:
                return json.loads(d)
        return None

    # @token_required
    def get(self, stuID, weekday, timeperiod):
        idx = ['', '2', '3']
        period = ['D0', 'D1', 'D2', 'D3', 'D4', 'DN', 'D5',
                    'D6', 'D7', 'D8', 'E0', 'E1', 'E2', 'E3', 'E4']
        day = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        day_num2eng = ['', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        timelist = [[0]*15 for i in range(7)]

        res = db.session.execute(text('SELECT uid FROM `user` WHERE username=:user'), {'user': stuID})
        uid = res.fetchone()[0]
        space_time = Auto_course_insert.get_free_period(uid, timelist)

        # CoursePeriod
        ALL_PERIOD = ['D0', 'D1', 'D2', 'D3', 'D4', 'DN', 'D5', 'D6', 'D7', 'D8', 'E0', 'E1', 'E2', 'E3', 'E4']
        PERIOD2IDX = {'D0' : 0, 'D1' : 1, 'D2' : 2, 'D3' : 3, 'D4' : 4, 'DN' : 5, 'D5' : 6, 'D6' : 7, 'D7' : 8, 'D8' : 9, 'E0' : 10, 'E1' : 11, 'E2' : 12, 'E3' : 13, 'E4' : 14}

        data = Auto_course_insert.load_schedule_data_if_not_expired(uid)
        if not data:
            data = {
                'Mon': {},
                'Tue': {},
                'Wed': {},
                'Thu': {},
                'Fri': {},
                'Sat': {},
                'Sun': {}
            }
            print('[*] debug: Collecting pickable courses')
            for i in range(0, 7):
                for j in space_time[i]:
                    sql = 'SELECT * FROM fju_course WHERE '
                    sql += "day='{0}' OR day2='{0}' OR day3='{0}'".format(day[i])

                    res = db.session.execute(text(sql))
                    # print(res.rowcount)
                    time = j.split('-')
                    time = CoursePeriod(*time)
                    # print(time)

                    candi = []
                    for row in res:
                        # Check period of a course if necessary
                        p1 = make_CoursePeriod(row['period']) if row['period'] else None
                        p2 = make_CoursePeriod(row['period2']) if row['period2'] else None
                        p3 = make_CoursePeriod(row['period3']) if row['period3'] else None
                        plist = [p1, p2, p3]
                        succ = True
                        for p in plist:
                            if p and p not in time:
                                # print(p)
                                succ = False
                        if succ:
                            candi.append({
                                'course_code': check_null(row['course_code']),
                                'name'       : check_null(row['name']),
                                'teacher'    : check_null(row['teacher']),
                                'department' : check_null(row['department']),
                                'score'      : check_null(row['score']),
                                'kind'       : check_null(row['kind']),
                                'times'      : check_null(row['times']),
                                'day'        : check_null(row['day']),
                                'week'       : check_null(row['week']),
                                'period'     : check_null(row['period']),
                                'classroom'  : check_null(row['classroom']),
                                'day2'       : check_null(row['day2']),
                                'week2'      : check_null(row['week2']),
                                'period2'    : check_null(row['period2']),
                                'classroom2' : check_null(row['classroom2']),
                                'day3'       : check_null(row['day3']),
                                'week3'      : check_null(row['week3']),
                                'period3'    : check_null(row['period3']),
                                'classroom3' : check_null(row['classroom3'])
                            })
                    data[day[i]].update({j :  candi})
                    # end for row
                # end for j
            #end for i

            # Updates the data
            db.session.execute(text('''
                UPDATE user SET schedule_data=:schedule_data, schedule_data_time=:schedule_data_time WHERE uid=:uid
            '''), {'schedule_data': json.dumps(data), 'schedule_data_time': utils.time_now(), 'uid': uid})
            db.session.commit()
        else:
            print('[*] debug: deserialize schedule_data')
        weekday = day_num2eng[weekday]
        tlist = []
        for i in data[weekday]: # Turn period into CoursePeriod
            tlist.append(CoursePeriod(*(i.split('-'))))
        cur_time = CoursePeriod(timeperiod, timeperiod) # e.g. D4 = D4-D4
        res_list = None
        # See if it exists a CoursePeriod which includes cur_time
        for t in tlist:
            if cur_time in t:
                k = str(t)
                res_list = data[weekday][k]
                break
        return res_list, 200
