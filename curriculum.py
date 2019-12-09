from flask import Flask, request
from flask_restful import Api, Resource, abort, reqparse
from sqlalchemy import text

from db import db
from utils import token_required
from crawler import course

class CurriculumRes(Resource):
  @token_required
  def get(self, stuID, year):
    # TODO: impl some time based updating course list mechanics
    res = db.session.execute(text('''
    SELECT password FROM `Course`.`user`
    WHERE username=:username
    '''), {
      'username': stuID
    })
    if res.returns_rows and res.rowcount == 1:
      passwd = res.fetchone()[0]
      year = str(year)
      clist = course.get_course_list(stuID, passwd, None, [year])  # TODO: backup this
    return clist, 200

class CurriculumList(Resource):
  @token_required
  def get(self, stuID):
    
    return '', 200
