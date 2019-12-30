import requests
import json
import datetime
import time
from flask import Flask, request
from flask_restful import Api, Resource, abort, reqparse
from sqlalchemy import text
#
from db import db
import config
from utils import result_msg, api_prefix
#
app = Flask(__name__)
app.config.from_object(config)
api = Api(app)
db.init_app(app)

# School
from apis import school
## list schools
api.add_resource(school.School, api_prefix('/schools'))

# Course
from apis import course
## list courses of a specific school
api.add_resource(course.Course, api_prefix(
    '/schools/<int:sid>/courses'), endpoint='list_courses_of_a_school')
## brief
api.add_resource(course.CourseList, api_prefix('/courses/list'), endpoint='list_brief_courses') #TODO(roy4801): this will fucked up
## details of a specific course
api.add_resource(course.CourseDetail, api_prefix('/courses/<int:cid>'))
## FJU course
api.add_resource(course.FJU_course_list, api_prefix('/fju_course/courses'))
api.add_resource(course.FJU_CourseDetail, api_prefix('/fju_course/courses/details'))

# Schedule for courses
from apis import schedule
api.add_resource(schedule.Course_insert, api_prefix('/fju_course/<int:stuID>/<string:course_code>'))
api.add_resource(schedule.Course_delete, api_prefix('/fju_course/<int:stuID>/<string:course_code>'))
api.add_resource(schedule.Auto_course_insert, api_prefix('/fju_course/auto/<int:stuID>/<int:weekday>/<string:timeperiod>'))

# Info
from apis import info
api.add_resource(info.StudentInfo, api_prefix('/users/<int:stuID>'))

# Login
from apis import login
api.add_resource(login.LoginRes, api_prefix('/login'))

# Curriculums
from apis import curriculum
api.add_resource(curriculum.CurriculumRes, api_prefix('/users/<int:stuID>/curriculums/<int:year>'))
api.add_resource(curriculum.CurriculumList,api_prefix('/users/<int:stuID>/curriculums'))

# Comment
from apis import comment
api.add_resource(comment.Comment_insert, api_prefix('/comments/<int:stuID>/<string:cid>'))
api.add_resource(comment.Comment_delete, api_prefix('/comments/<int:stuID>/<int:commentID>'))
api.add_resource(comment.Comment, api_prefix('/comments'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
