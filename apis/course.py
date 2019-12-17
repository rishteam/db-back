import base64
import re
import json
import urllib.parse
from flask import Flask, request
from flask_restful import Api, Resource, abort, reqparse
from sqlalchemy import text

from db import db
from utils import check_null, B64_REGEX

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

class FJU_course_list(Resource):
    param_parser = reqparse.RequestParser()
    param_parser.add_argument('course_code', type=str, help='Please give me data')
    param_parser.add_argument('name', type=str, help='Please give me data')
    param_parser.add_argument('teacher', type=str, help='Please give me data')
    param_parser.add_argument('department', type=str, help='Please give me data')

    def get(self):
        args = FJU_course_list.param_parser.parse_args()
        params = {}
        condit = [
            'course_code',
            'name',
            'teacher',
            'department'
        ]
        selected_condit = []

       # Null parameter
        is_none_data = True
        for p in condit:
            if args[p] != None:
                is_none_data = False
                break
        if is_none_data:
            return {"message": "You need to provide more than one parameter."}, 400

        for p in condit:
            if p in args and args[p] != None:
                selected_condit.append(p)
                params[p] = args[p] + '%'
        # Make SQL by the given condition
        sql_where = ''
        for idx, c in enumerate(selected_condit):
            if idx == 0:
                sql_where += '{0} LIKE :{0}'.format(c)
            else:
                sql_where += ' AND {0} LIKE :{0}'.format(c)
        #
        sql = 'SELECT * FROM fju_course WHERE {}'.format(sql_where)
        res = db.session.execute(text(sql), params)
        # Pack the results
        items = []
        for row in res:
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
                'course_selection': row['course_selection'] # WTF is this?
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
                    sql_where += " AND (tid = '{}'".format(tid)
            sql_where += ') '

            sql = 'SELECT * FROM course WHERE {}'.format(sql_where)
            res_detail = db.session.execute(text(sql))
            # print(sql)

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
