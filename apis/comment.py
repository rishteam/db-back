import urllib.parse
from flask import Flask, request
from flask_restful import Api, Resource, abort, reqparse
from sqlalchemy import text, exc
import datetime

from db import db
from utils import check_null, token_required

def get_uid(stuID):
    """Get the uid by the student ID"""
    res = db.session.execute(text('SELECT * FROM user WHERE username=:stuID'), {'stuID': stuID})
    if res.rowcount >= 1:
        return res.fetchone()['uid']
    else:
        raise RuntimeError('No uid referenced to {} in the db.'.format(stuID))

def get_stuID(uid):
    """Get the stuID by the uid"""
    res = db.session.execute(text('SELECT username FROM user WHERE uid=:uid'), {'uid': uid})
    if res.rowcount >= 1:
        return res.fetchone()['username']
    else:
        raise RuntimeError('No stuID(username) referenced to {} in the db.'.format(stuID))

def check_cid_exists(cid):
    """Check whether the cid exists or not"""
    res = db.session.execute(text('SELECT * FROM fju_course WHERE course_code=:cid'), {'cid' : cid })
    return res.rowcount != 0

def get_recent_commentID(uid, className, classOpen, teacher):
    """Get the recent commentID by user info and class info"""
    res = db.session.execute(text('''
        SELECT commentID FROM comment
        WHERE uid=:uid AND className=:className AND classOpen=:classOpen AND teacher=:teacher
        ORDER BY commentID DESC LIMIT 1
    '''), {
        'uid'       : uid,
        'className' : className,
        'classOpen' : classOpen,
        'teacher'   : teacher
    })
    if res.rowcount:
        return res.fetchone()['commentID']
    raise RuntimeError('The result of recent commentID is not exist')

class Comment_insert(Resource):
    @token_required
    def post(self, stuID, cid):
        if check_cid_exists(cid) == False:
            abort(400, message='`cid` is not exist.')

        uid = get_uid(stuID)
        condit = [
            'Quiz',
            'MidExam',
            'FinalExam',
            'PersonalReport',
            'GroupReport',
            'OtherExam',
            'OtherWork',
            'lvExamAmount',
            'lvFun',
            'lvLearned',
            'lvRequest',
            'lvTeachlear',
            'lvWork',
            'lvRecommend',
            'message'
        ]
        param_parser = reqparse.RequestParser()
        for i in condit:
            param_parser.add_argument(i, type=str, help='Please provide `{}`'.format(i), location='form')

        args = param_parser.parse_args()
        # print(cid)
        res = db.session.execute(text('SELECT name, teacher, department FROM fju_course WHERE course_code=:cid'), {'cid': cid})
        data = res.fetchone()

        try:
            db.session.execute(text('''
                INSERT INTO comment(uid, className, classOpen, teacher, createDate, Quiz, MidExam, FinalExam, PersonalReport, GroupReport, OtherExam, OtherWork, lvExamAmount, lvFun, lvLearned, lvRequest, lvTeachlear, lvWork, lvRecommend, message)
                values(:uid, :className, :classOpen, :teacher, :createDate, :Quiz, :MidExam, :FinalExam, :PersonalReport, :GroupReport, :OtherExam, :OtherWork, :lvExamAmount, :lvFun, :lvLearned, :lvRequest, :lvTeachlear, :lvWork, :lvRecommend, :message)
            '''), {
                'uid'           : uid,
                'className'     : data['name'],
                'classOpen'     : data['department'],
                'teacher'       : data['teacher'],
                'createDate'    : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'Quiz'          : check_null(args['Quiz']),
                'MidExam'       : check_null(args['MidExam']),
                'FinalExam'     : check_null(args['FinalExam']),
                'PersonalReport': check_null(args['PersonalReport']),
                'GroupReport'   : check_null(args['GroupReport']),
                'OtherExam'     : check_null(args['OtherExam']),
                'OtherWork'     : check_null(args['OtherWork']),
                'lvExamAmount'  : check_null(args['lvExamAmount']),
                'lvFun'         : check_null(args['lvFun']),
                'lvLearned'     : check_null(args['lvLearned']),
                'lvRequest'     : check_null(args['lvRequest']),
                'lvTeachlear'   : check_null(args['lvTeachlear']),
                'lvWork'        : check_null(args['lvWork']),
                'lvRecommend'   : check_null(args['lvRecommend']),
                'message'       : check_null(args['message'])
            })
        except exc.SQLAlchemyError as e:
            print(e)
            abort(500, message='Internal Server Error (Go to see the log)')
        db.session.commit()
        commentID = get_recent_commentID(uid, data['name'], data['department'], data['teacher'])

        return {'message': 'Success to add a comment', 'commentID': commentID}, 200

class Comment_delete(Resource):
    @token_required
    def delete(self, stuID, commentID):
        uid = get_uid(stuID)
        # Try to delete
        try:
            res = db.session.execute(text('''
                DELETE FROM comment WHERE uid=:uid AND commentID=:commentID
            '''), {
                'uid' : uid,
                'commentID': commentID
            })
        except exc.SQLAlchemyError as e:
            print(e)
            abort(500, message='Internal Server Error (Go to see the log)')

        if res.rowcount:
            db.session.commit()
            return {'message' : 'Succeeded to delete comment'}, 200
        return {'message': 'Cannot found the comment'}, 404

# TODO: comment search
class Comment(Resource):
    @staticmethod
    def get_comment_data(param):
        # Make the sql
        sql = 'SELECT * FROM comment WHERE '
        for idx, key in enumerate(param.keys()):
            if idx == 0:
                sql +=  '{0} LIKE :{0}'.format(key)
            else:
                sql += ' AND {0} LIKE :{0}'.format(key)
        # Set all of the values to '%...%'
        for key, val in param.items():
            param[key] = '%{}%'.format(val)
        res = db.session.execute(text(sql), param)
        return res

    def get(self):
        param = {}
        if 'stuID' in request.args:
            stuID = request.args['stuID']
            param.update(uid=get_uid(stuID))
        if 'teacher' in request.args:
            param.update(teacher=request.args['teacher'])
        if 'coursename' in request.args:
            param.update(className=request.args['coursename'])
        if 'cid' in request.args:
            res = db.session.execute(text('SELECT name, teacher, department FROM fju_course WHERE course_code=:cid'), {'cid': request.args['cid']})
            if res.rowcount == 0:
                return {'message' : 'Course_code is not exist'}, 404
            for row in res:
                if row['name']:
                    param.update(className=row['name'])
                if row['teacher']:
                    param.update(teacher=row['teacher'])
                # diff between comment and fju_course in department column
                # if row['department']:
                #     param.update(classOpen=row['department'])

        res = Comment.get_comment_data(param)
        if res.rowcount == 0:
            abort(404, message='Cannot Found the comment data.')
        # Collect the comments
        res_list = []
        for row in res:
            dic = {
                'commentID'     : check_null(row['commentID']),
                'stuID'         : check_null(get_stuID(row['uid'])),
                'classOpen'     : check_null(row['classOpen']),
                'className'     : check_null(row['className']),
                'teacher'       : check_null(row['teacher']),
                'createDate'    : check_null(str(row['createDate'])),
                'Quiz'          : check_null(row['Quiz']),
                'MidExam'       : check_null(row['MidExam']),
                'FinalExam'     : check_null(row['FinalExam']),
                'PersonalReport': check_null(row['PersonalReport']),
                'GroupReport'   : check_null(row['GroupReport']),
                'OtherExam'     : check_null(row['OtherExam']),
                'OtherWork'     : check_null(row['OtherWork']),
                'lvExamAmount'  : check_null(row['lvExamAmount']),
                'lvFun'         : check_null(row['lvFun']),
                'lvLearned'     : check_null(row['lvLearned']),
                'lvRequest'     : check_null(row['lvRequest']),
                'lvTeachlear'   : check_null(row['lvTeachlear']),
                'lvWork'        : check_null(row['lvWork']),
                'lvRecommend'   : check_null(row['lvRecommend']),
                'message'       : check_null(row['message'])
            }
            res_list.append(dic)

        return res_list, 200
