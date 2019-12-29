import base64
import re
import json
import urllib.parse
from flask import Flask, request
from flask_restful import Api, Resource, abort, reqparse
from sqlalchemy import text

from db import db
from utils import check_null

def get_school_name_by_sid(sid):
    res = db.session.execute(
        text('SELECT name FROM school WHERE sid=:sid LIMIT 1'), {'sid': sid})
    res = res.fetchone()[0]
    return res

# TODO(roy4801): query the SQL directly by sid
# TODO(roy4801): separate logic of the condits
def get_course_list_by_sid(sid, condit, param):
    # Get courses
    school = get_school_name_by_sid(sid)  # by name
    param.update(school=school)

    # Prepare the sql statement
    sql = 'SELECT id, name, department, teacher from class WHERE school=:school'
    for i in condit:
        sql += ' AND'
        sql += ' {0}=:{0}'.format(i)
    sql += ';'
    # if one condit doesn't have the corresponding params, then exit
    for i in condit:
        if i not in param:
            msg = '[DEBUG] Whenever there\'s a condition, there\'s a parameter'
            print(msg)
            return msg

    res = db.session.execute(text(sql), param)
    # pack into a list
    li = []
    if res.returns_rows and res.rowcount > 0:
        for i, name, dep, teacher in res:
            li.append(
                {
                    'id'        : i,
                    'name'      : name,
                    'department': dep,
                    'teacher'   : teacher
                }
            )
    # print(li)
    return li

# TODO(roy4801): pack this into model
def get_detail_of_course(cid):
    res = db.session.execute(text(
        "SELECT year, semester, name, department, teacher, grade, score, student, subject, system, lang, description from class WHERE id=:cid"), {'cid': cid})
    res = res.fetchone()
    dic = {
        "year"       : res[0],
        "semester"   : res[1],
        "name"       : res[2],
        "department" : res[3],
        "teacher"    : res[4],
        "grade"      : res[5],
        "score"      : res[6],
        "student"    : res[7],
        "subject"    : res[8],
        "system"     : res[9],
        "lang"       : res[10],
        "description": res[11]
    }
    return dic

# TODO(roy4801): handle 4xx or 5xx
class Course(Resource):
    def get(self, sid):
        # TODO(roy4801): refactor these args checks into funcs
        condit = []
        param = {}
        if 'teacher' in request.args:
            condit.append('teacher')
            param.update(teacher=request.args['teacher'])
        if 'department' in request.args:
            condit.append('department')
            param.update(department=request.args['department'])
        # TODO(roy4801): change the name to search instead of compareision
        if 'name' in request.args:
            condit.append('name')
            param.update(name=request.args['name'])

        # print(condit, param)
        li = get_course_list_by_sid(sid, condit, param)
        return li, 200

    @staticmethod
    def get_fju_school_id():
        res = db.session.execute(
            text("SELECT sid FROM school WHERE `name`='輔仁大學'"))
        if res.rowcount == 1:
            return int(res.fetchone()[0])
        raise RuntimeError('`res` returns more than 1 row')

# provide only filters
parse_filter = reqparse.RequestParser()
parse_filter.add_argument('cid', type=str, help='Please provide `cid`')
parse_filter.add_argument('year', type=str, help='Please provide `year`')
parse_filter.add_argument('name', type=str, help='Please provide `name`')
parse_filter.add_argument('semester', type=str,
                          help='Please provide `semester`')
parse_filter.add_argument('department', type=str,
                          help='Please provide `department`')
parse_filter.add_argument('college', type=str, help='Please provide `college`')
parse_filter.add_argument('grade', type=str, help='Please provide `grade`')
parse_filter.add_argument('school', type=str, help='Please provide `school`')
parse_filter.add_argument('teacher', type=str, help='Please provide `teacher`')


def get_school_id(school_name):
    res = db.session.execute(text('SELECT sid FROM school WHERE name=:school_name'), {
                             'school_name': school_name})
    if res.rowcount == 0:
        return None
    res = res.fetchone()
    return res[0]

def get_teacher_id(teacher_name):
    res = db.session.execute(text('SELECT * FROM teacher WHERE name LIKE :teacher_name'),{
                             'teacher_name': teacher_name})
    res_id = []
    for row in res:
        res_id.append(row['tid'])

    return res_id

# DEPRECATED: This will be removed soon
class CourseList(Resource):
    def get(self):
        args = parse_filter.parse_args()
        paremeter = []
        condition = []
        idx = [
            'cid',
            'year',
            'name',
            'teacher',
            'semester',
            'department',
            'college',
            'grade',
            'school'
        ]

        # Null parameter
        none_data = True
        for i in idx:
            if args[i] != None:
                none_data = False
                break
        if none_data == True:
            return {"message": "You need to provide above one parameter"}, 400

        # ready for search
        for i in idx:
            if i == 'school':
                condition.append(get_school_id(args[i]))
                paremeter.append('sid')
            elif i == 'teacher':
                # Find the teacher id
                res = get_teacher_id(args[i])
                condition.append(res)
                paremeter.append('tid')
            else:
                condition.append(args[i])
                paremeter.append(i)

        # 將有給條件的都拿去SQL搜尋，只能一個一個用AND接起
        # 符合teacher的tid 都 return
        flag = 0
        search_condition = ''
        for i in range(0, len(condition)):
            if paremeter[i] == 'tid':
                if len(condition[i]) != 0:
                    if flag == 0:
                        search_condition += 'WHERE ('
                        for j in range(0,len(condition[i])):
                            if j == len(condition[i])-1:
                                search_condition += str(paremeter[i]) + \
                                    '=' + '\'' + str(condition[i][j]) + '\''
                            else:
                                search_condition += str(paremeter[i]) + \
                                    '=' + '\'' + str(condition[i][j]) + '\'' + ' OR '
                        search_condition += ')'
                        flag = 1
                    else:
                        search_condition += 'AND'
                        search_condition += '('
                        for j in range(0, len(condition[i])):
                            if j == len(condition[i])-1:
                                search_condition += str(paremeter[i]) + \
                                    '=' + '\'' + str(condition[i][j]) + '\''
                            else:
                                search_condition += str(paremeter[i]) + \
                                    '=' + '\'' + \
                                    str(condition[i][j]) + '\'' + ' OR '
                        search_condition += ')'
                else:
                    search_condition += 'WHERE (' + 'tid' + \
                        '=' + '\'' + '' + '\'' + ')'
                    flag = 1

            elif condition[i] != None:
                if flag == 0:
                    search_condition += 'WHERE ' + str(paremeter[i]) + \
                        '=' + '\'' + str(condition[i]) + '\''
                    flag = 1
                else:
                    search_condition += 'AND ' + \
                                        str(paremeter[i]) + '=' + \
                                        '\'' + str(condition[i]) + '\''

        search_condition = 'SELECT * FROM course ' + search_condition
        res = db.session.execute(text(search_condition))
        print(search_condition)

        if res.rowcount == 0:
            return {"message": "NOT FOUND"}, 400

        items = []
        for row in res:
            items.append({
                'cid'        : check_null(str(row['cid'])),
                'year'       : check_null(str(row['year'])),
                'semester'   : check_null(str(row['semester'])),
                'name'       : check_null(str(row['name'])),
                'teacher'    : check_null(str(row['tid'])),
                'school'     : check_null(str(row['sid'])),
                'college'    : check_null(str(row['college'])),
                'grade'      : check_null(str(row['grade'])),
                'department' : check_null(str(row['department'])),
                'score'      : check_null(str(row['score'])),
                'description': check_null(str(row['description'])),
                'link'       : check_null(str(row['link'])),
                'system'     : check_null(str(row['system'])),
                'subject'    : check_null(str(row['subject'])),
                'required'   : check_null(str(row['required'])),
                'student'    : check_null(str(row['student'])),
                'lang'       : check_null(str(row['lang']))
            })
        return items, 200

class CourseDetail(Resource):
    def get(self, cid):
        data = get_detail_of_course(cid)
        # print(data)
        return data, 200

def weekday_num_to_eng(weekday):
    """Convert the weekday (number) to the English representation: e.g. 2 -> Tue
    """
    return {
        1: 'Mon',
        2: 'Tue',
        3: 'Wed',
        4: 'Thu',
        5: 'Fri',
        6: 'Sat',
        7: 'Sun'
    }[weekday]

def weekday_eng_to_num(weekday):
    """Convert the weekday (English) to the number representation: e.g. Tue -> 2
    """
    return {
        'Mon' : 1,
        'Tue' : 2,
        'Wed' : 3,
        'Thu' : 4,
        'Fri' : 5,
        'Sat' : 6,
        'Sun' : 7
    }[weekday]

def convert_weekday2list(weekday):
    """Convert the weekday to bool list"""
    bl = [False] * 9
    for it in weekday:
        bl[ord(it)-ord('0')] = True
    return bl

class CoursePeriod:
    """Struct for period of a course"""
    ALL_PERIOD = ['D0', 'D1', 'D2', 'D3', 'D4', 'DN', 'D5', 'D6', 'D7', 'D8', 'E0', 'E1', 'E2', 'E3', 'E4']
    PERIOD2IDX = {'D0' : 0, 'D1' : 1, 'D2' : 2, 'D3' : 3, 'D4' : 4, 'DN' : 5, 'D5' : 6, 'D6' : 7, 'D7' : 8, 'D8' : 9, 'E0' : 10, 'E1' : 11, 'E2' : 12, 'E3' : 13, 'E4' : 14}

    def __init__(self, start, end):
        self.start = start
        self.end = end
    def __eq__(this, other):
        """a == b"""
        if isinstance(this, type(other)):
            return this.start == other.start and this.end == other.end
        return False
    def __contains__(self, item):
        """a in b"""
        if not isinstance(item, type(self)):
            raise TypeError('The item should be CoursePeriod not {}'.format(type(item)))
        p2i = CoursePeriod.PERIOD2IDX
        overlapp = 0
        # i= self idx
        for i in range(p2i[self.start], p2i[self.end]+1):
            if p2i[item.start] <= i and i <= p2i[item.end]:
                overlapp += 1
        return overlapp > 0
    def __repr__(self):
        return '<CoursePeriod start={} end={}>'.format(self.start, self.end)

def make_CoursePeriod(x):
    """Turn the str 'D?-D?' into the CoursePeriod"""
    if re.match(r'^((?:D(?:[0-8]|N)|E[0-4])-(?:D(?:[0-8]|N)|E[0-4]))$', x):
        p = x.split('-')
        return CoursePeriod(*p)
    else:
        raise RuntimeError('Cannot make the CoursePeriod: {}'.format(x))

TIME_NONE = 1

class FJU_course_list(Resource):
    """Provides APIs for listing the courses in FJU"""
    param_parser = reqparse.RequestParser()
    param_parser.add_argument('course_code', type=str)
    param_parser.add_argument('name', type=str)
    param_parser.add_argument('teacher', type=str)
    param_parser.add_argument('department', type=str)
    param_parser.add_argument('weekday', type=str)
    param_parser.add_argument('time', type=str)
    param_parser.add_argument('include', type=bool)

    def get(self):
        args = FJU_course_list.param_parser.parse_args()
        params = {}
        condit = [
            'course_code',
            'name',
            'teacher',
            'department'
        ]
        not_query = ['weekday', 'time', 'include']
        condit += not_query # for checking
        selected_condit = []
        sql_where = ''

       # Check if it provides more than one param
        is_none_data = True
        for p in condit:
            if args[p] != None:
                is_none_data = False
                break
        if is_none_data:
            return {'message': 'You need to provide more than one parameter.'}, 400

        # Prepare the params depends on the condit
        for p in condit:
            if p in args and args[p] != None:
                selected_condit.append(p)
                if p not in not_query:
                    params[p] = args[p] + '%'
        # Prepare weekday part of SQL WHERE
        weekday = None
        weekday_arg = args['weekday'] if 'weekday' in selected_condit and 'weekday' in args else None
        if weekday_arg:
            if not re.match(r'^[1-8]{1,8}$', weekday_arg):
                return {'message': '`weekday` must be numbers'}, 400
            weekday = convert_weekday2list(weekday_arg)
            first = True
            for i in range(1, len(weekday)):
                if weekday[i]:
                    if not first:
                        sql_where += ' OR '
                    sql_where += "day='{0}' OR day2='{0}' OR day3='{0}'".format(weekday_num_to_eng(i))
                    first = False
            sql_where = '({})'.format(sql_where)
        # Prepare time (D?-D?)
        # Notice: TIME_NONE means empty time and None means it didn't pass time option in
        if 'time' in selected_condit:
            if args['time'] == 'None':
                time = TIME_NONE
                sql_where = '' # ignore the weekday
                sql_where += "(period='' AND period2='' AND period3='')"
            else:
                time = args['time'].split('-')
                time = CoursePeriod(*time)
        else:
            time = None
        print('>> {}'.format(time))
        #
        inc_flag = args['include']
        # Make SQL by the given condition
        selected_condit = [x for x in selected_condit if x not in not_query] # remove not_query from condit
        for idx, c in enumerate(selected_condit):
            if idx == 0:
                if weekday:
                    sql_where += ' AND '
                sql_where += '{0} LIKE :{0}'.format(c)
            else:
                sql_where += ' AND {0} LIKE :{0}'.format(c)
        # if no option was chosen
        if sql_where == '':
            sql_where = '1'
        sql = 'SELECT * FROM fju_course WHERE {}'.format(sql_where)
        print(sql)
        res = db.session.execute(text(sql), params)
        # Pack the results
        items = []
        for row in res:
            # Check period of a course if necessary
            if time and time != TIME_NONE:
                p1 = make_CoursePeriod(row['period']) if row['period'] else None
                p2 = make_CoursePeriod(row['period2']) if row['period2'] else None
                p3 = make_CoursePeriod(row['period3']) if row['period3'] else None
                plist = [p1, p2, p3]
                succ = False
                for p in plist:
                    if inc_flag: # include
                        if p and p in time:
                            succ = True
                    else: # not include
                        if p and p == time:
                            succ = True
                if not succ:
                    continue
            #
            items.append({
                'course_code'     : check_null(row['course_code']),
                'name'            : check_null(row['name']),
                'teacher'         : check_null(row['teacher']),
                'department'      : check_null(row['department']),
                'score'           : check_null(row['score']),
                'kind'            : check_null(row['kind']),
                'times'           : check_null(row['times']),
                'day'             : check_null(row['day']),
                'week'            : check_null(row['week']),
                'period'          : check_null(row['period']),
                'classroom'       : check_null(row['classroom']),
                'day2'            : check_null(row['day2']),
                'week2'           : check_null(row['week2']),
                'period2'         : check_null(row['period2']),
                'classroom2'      : check_null(row['classroom2']),
                'day3'            : check_null(row['day3']),
                'week3'           : check_null(row['week3']),
                'period3'         : check_null(row['period3']),
                'classroom3'      : check_null(row['classroom3']),
            })
        return items, 200

class FJU_CourseDetail(Resource):
    @staticmethod
    def get_fju_teacher_id(teacher_name, department):
        '''Get teacher id by his/her name and department'''
        res = db.session.execute(text('''
            SELECT tid FROM teacher
            WHERE name LIKE :teacher_name
                AND sid=68
                AND department LIKE :department
        '''), {
            'teacher_name': teacher_name+'%',
            'department': department+'%'
        })
        tid = []
        for row in res:
            tid.append(row['tid'])
        return tid

    def get(self):
        param_parser = reqparse.RequestParser()
        param_parser.add_argument('cid', type=str)
        # Get cid
        cid_param = param_parser.parse_args()['cid']
        if not cid_param:
            abort(400, message='Please provide `cid`')
        # Make sql
        sql = '''
            SELECT * FROM fju_course WHERE course_code=:cid
        '''
        res = db.session.execute(text(sql), {'cid': cid_param})
        rt = None
        for row in res:
            # Gen WHERE part of sql querying from BIG table `course`
            sql_where = ''
            sql_where += "name = '{}'".format(row['name'])
            sql_where += " AND year = '108'"
            sql_where += " AND sid = '68'"
            tids = FJU_CourseDetail.get_fju_teacher_id(row['teacher'], row['department'])
            for i, tid in enumerate(tids):
                if i:
                    sql_where += " OR tid = '{}'".format(tid)
                else:
                    sql_where += " AND tid = '{}'".format(tid)

            sql = 'SELECT * FROM course WHERE {}'.format(sql_where)
            res_detail = db.session.execute(text(sql))

            if res_detail.rowcount == 0:
                rt = {
                    'description': '',
                    'system'     : '',
                    'link'       : '',
                    'student'    : '',
                    'lang'       : ''
                }
            else:
                row_detail = res_detail.fetchone()
                rt = {
                    'description': check_null(row_detail['description']),
                    'system'     : check_null(row_detail['system']),
                    'link'       : check_null(row_detail['link']),
                    'student'    : check_null(row_detail['student']),
                    'lang'       : check_null(row_detail['lang'])
                }

        return rt, 200
