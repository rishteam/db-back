
from flask import Flask, request
from flask_restful import Api, Resource, abort, reqparse
from sqlalchemy import text
import requests
import json
import datetime
import time
#
from db import db
import config
from utils import result_msg
#
app = Flask(__name__)
app.config.from_object(config)
api = Api(app)

db.init_app(app)

# TODO: Figure out why didn't location='form' work
login_parser = reqparse.RequestParser()
login_parser.add_argument('username', type=str, required=True,
                          help='Please provide the username or reference the API Docs')
login_parser.add_argument('password', type=str, required=True,
                          help='Please provide the password or reference the API Docs')

def api_prefix(s):
  return '/db/v1' + s

# TODO(roy4801): handle 5xx
class School(Resource):
  def get(self):
    select = None
    if 'school' in request.args:
      select = request.args['school']
    if select:
      res = db.session.execute(text("SELECT * FROM school WHERE name=:name"), {'name': select})
    else:
      res = db.session.execute(text('SELECT * FROM school;'))
    # Returns not rows
    if res.returns_rows and res.rowcount == 0:
      abort(400, message='Not found')
    items = []
    for sid, name in res:
      items.append({'name': name, 'id': sid})
    return items, 200

def get_school_name_by_sid(sid):
  res = db.session.execute(text('SELECT name FROM school WHERE sid=:sid LIMIT 1'), {'sid': sid})
  res = res.fetchone()[0]
  return res

# TODO(roy4801): query the SQL directly by sid
# TODO(roy4801): separate logic of the condits
def get_course_list_by_sid(sid, condit, param):
  # Get courses
  school = get_school_name_by_sid(sid) # by name

  param.update(school=school)

  # Prepare the sql statement
  nf = False
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
          'id' : i,
          'name': name,
          'department': dep,
          'teacher': teacher
        }
      )
  # print(li)
  return li

# TODO(roy4801): pack this into model
def get_detail_of_course(cid):
  res = db.session.execute(text("SELECT year, semester, name, department, teacher, grade, score, student, subject, system, lang, description from class WHERE id=:cid"), {'cid': cid})
  res = res.fetchone()
  dic = {
    "year": res[0],
    "semester": res[1],
    "name": res[2],
    "department": res[3],
    "teacher": res[4],
    "grade": res[5],
    "score": res[6],
    "student": res[7],
    "subject": res[8],
    "system": res[9],
    "lang": res[10],
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

# TODO(roy4801): provide only filters
class CourseList(Resource):
  def get(self):
    res = db.session.execute(text("SELECT id, name, department, teacher from class"))
    # pack into a list
    li = []
    if res.returns_rows and res.rowcount > 0:
      for i, name, dep, teacher in res:
        li.append(
          {
            'id' : i,
            'name': name,
            'department': dep,
            'teacher': teacher
          }
        )
    # print(li)
    return {}, 200

class CourseDetail(Resource):
  def get(self, cid):
    data = get_detail_of_course(cid)
    # print(data)
    return data, 200

from crawler.course import get_currnet_course_list, try_to_login
import hashlib

class LoginRes(Resource):
  def post(self):
    args = login_parser.parse_args() # get args if succeeded
    user, passwd = args['username'], args['password']
    # Login
    r = requests.Session()
    fail, _ = try_to_login(r, user, passwd)
    if fail:
      return {'message': 'Failed to login'}, 400

    # Generate the token
    dic = {'username': user, 'password': passwd}
    from config import SECRET_KEY
    dic['secret'] = hashlib.md5(SECRET_KEY).hexdigest()
    json_dic = json.dumps(dic, sort_keys=True)
    token = hashlib.md5(json_dic.encode('utf-8')).hexdigest()
    print(token)

    # Check if a user is in the db
    res = db.session.execute(
      text('SELECT * FROM `user` WHERE username=:user'), {'user': user}
    )
    if res.returns_rows:
      # If not existing, add a new user
      if res.rowcount == 0:
        sql = text('''
          INSERT INTO `Course`.`user` (`username`, `password`, `curpoint`, `perm`, `firstlogin`, `lastlogin`, `token`)
          VALUES (:username, :passwd, '0', '0', :time, :time, :token);
          ''')
        db.session.execute(sql, {
          'username': user,
          'passwd': passwd,
          'time': time.time(),
          'token': token
        })
        db.session.commit()
      # If it exists, updates the token
      elif res.rowcount == 1:
        sql = text('''
        UPDATE `Course`.`user`
        SET `token`=:token
        WHERE username=:username
        ''')
        db.session.execute(sql, {
          'token': token,
          'username': user
        })
        db.session.commit()

    print(time.time())
    return {'token': token}, 200

from utils import token_required
class CurriculumRes(Resource):
  @token_required
  def get(self, stuID):
    # TODO: impl some time based updating course list mechanics
    res = db.session.execute(text('''
    SELECT password FROM `Course`.`user`
    WHERE username=:username
    '''), {
      'username': stuID
    })
    if res.returns_rows and res.rowcount == 1:
      passwd = res.fetchone()[0]
      clist = get_currnet_course_list(stuID, passwd) # TODO: backup this
    return clist, 200


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
            'uid': uid
        })

        if uid_exist.rowcount == 0:
            return {
                "message": "uid error"
            }, 400

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
                return {
                    "message": "Course_code duplicate"
                }, 400
            have = db.session.execute(text('''
            SELECT * FROM fju_course where course_code=:course_code
            '''),
                                      {
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
        for j in range(0, 15):
            print(period[j], end=' ')
        print()
        for i in range(0, 7):
            for j in range(0, 15):
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

        db.session.execute('Insert into curriculum(uid, sid, course_code) values (:uid, 68, :coursecode)', {
                           'coursecode': add_course_code, 'uid': uid})
        db.session.commit()
        return {'result': 'Success',
                'course_code': add_course_code}, 200


# school
## list schools
api.add_resource(School, api_prefix('/schools'))
## list courses of a specific school
api.add_resource(Course, api_prefix('/schools/<int:sid>/courses'), endpoint='list_courses_of_a_school')

# courses
## breif
api.add_resource(CourseList, api_prefix('/courses/list'), endpoint='list_brief_courses') #TODO(roy4801): this will fucked up
## details of a specific course
api.add_resource(CourseDetail, api_prefix('/courses/<int:cid>'))

# Login
api.add_resource(LoginRes, api_prefix('/login'))

# Curriculums
api.add_resource(CurriculumRes, api_prefix('/users/<int:stuID>/curriculums'))

# FJU_course
api.add_resource(FJU_course, api_prefix('/fju_course'))
api.add_resource(Course_insert, api_prefix(
    '/fju_course/<int:uid>/<string:add_course_code>'))


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=80)
