from flask import Flask, request
from flask_restful import Api, Resource, abort, reqparse
from sqlalchemy import text
#
from db import db

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
                    'id': i,
                    'name': name,
                    'department': dep,
                    'teacher': teacher
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
        # li = 'test'
        return li, 200

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

def get_school_id(school_name):
    res = db.session.execute(text('SELECT sid FROM school WHERE name=:school_name'), {
                             'school_name': school_name})
    if res.rowcount == 0:
        return None
    res = res.fetchone()
    return res[0]

def check_null(data):
    if len(str(data)) == 0:
        return ''
    else:
        return data


# for Class
class CourseList(Resource):
    def get(self):
        args = parse_filter.parse_args()
        paremeter = []
        condition = []
        idx = [
            'cid',
            'year',
            'name',
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
            else:
                condition.append(args[i])
                paremeter.append(i)

        # 將有給條件的都拿去SQL搜尋，只能一個一個用AND接起
        flag = 0
        search_condition = ''
        for i in range(0, len(condition)):
            if condition[i] != None:
                if flag == 0:
                    search_condition += str(paremeter[i]) + \
                        '=' + '\'' + str(condition[i]) + '\''
                    flag = 1
                else:
                    search_condition += 'AND ' + \
                                        str(paremeter[i]) + '=' + \
                                        '\'' + str(condition[i]) + '\''

        search_condition = 'SELECT * FROM course WHERE ' + search_condition
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

parser = reqparse.RequestParser()
parser.add_argument('course_code', type=str, help='Please give me data')
parser.add_argument('name', type=str, help='Please give me data')
parser.add_argument('teacher', type=str, help='Please give me data')
parser.add_argument('department', type=str, help='Please give me data')


class FJU_course_list(Resource):
    def get(self):
        args = parser.parse_args()
        paremeter = []
        condition = []
        idx = [
            'course_code',
            'name',
            'teacher',
            'department'
        ]

       # Null parameter
        none_data = True
        for i in idx:
            if args[i] != None:
                none_data = False
                break
        if none_data == True:
            return {"message": "You need to provide above one parameter"}, 400


        for i in idx:
            condition.append(args[i])
            paremeter.append(i)


        # 將有給條件的都拿去SQL搜尋，只能一個一個用AND接起
        flag = 0
        search_condition = ''
        for i in range(0, len(condition)):
            if condition[i] != None:
                if flag == 0:
                    search_condition += paremeter[i] + \
                        '=' + '\'' + condition[i] + '\''
                    flag = 1
                else:
                    search_condition += 'AND ' + \
                        paremeter[i] + '=' + '\'' + condition[i] + '\''

        search_condition = 'SELECT * FROM fju_course WHERE ' + search_condition

        res = db.session.execute(text(search_condition))
        # print(search_condition)
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
                'course_selection': row['course_selection']
            })
        return items, 200