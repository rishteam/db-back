import urllib.parse
from flask import Flask, request
from flask_restful import Api, Resource, abort, reqparse
from sqlalchemy import text
import datetime


from db import db
from utils import check_null, token_required


def get_uid(stuID):
    res = db.session.execute(text('SELECT * FROM user WHERE username=:stuID'),
                             {'stuID': stuID})

    for row in res:
        return row['uid']


def check_cid_exists(cid):
    res = db.session.execute(text('SELECT * FROM fju_course WHERE course_code=:cid'),
                            {'cid' : cid })
    if res.rowcount == 0:
        return False
    else:
        return True


class Comment_insert(Resource):
    @token_required
    def post(self, stuID, cid):

        if check_cid_exists(cid) == False:
            abort(400, 'cid is not exist')

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
            param_parser.add_argument(i, type=str, help='Please give me data')


        args = param_parser.parse_args()
        # print(cid)
        res = db.session.execute('SELECT name, teacher, department FROM fju_course WHERE course_code=:cid', {'cid': cid})

        data = []
        for row in res:
            data.append(row['name'])
            data.append(row['department'])
            data.append(row['teacher'])

        db.session.execute('INSERT INTO comment(uid, className, classOpen, teacher, createDate, Quiz, MidExam, FinalExam, PersonalReport, GroupReport, OtherExam, OtherWork, lvExamAmount, lvFun, lvLearned, lvRequest, lvTeachlear, lvWork, lvRecommend, message) \
                            values(:uid, :className, :classOpen, :teacher, :createDate, :Quiz, :MidExam, :FinalExam, :PersonalReport, :GroupReport, :OtherExam, :OtherWork, :lvExamAmount, :lvFun, :lvLearned, :lvRequest, :lvTeachlear, :lvWork, :lvRecommend, :message)',
                            {
                                'uid'           : uid,
                                'className'     : data[0],
                                'classOpen'     : data[1],
                                'teacher'       : data[2],
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
        db.session.commit()

        return {'message': 'success'}




class Comment_delete(Resource):
    @token_required
    def delete(self, stuID, commentID):
        uid = get_uid(stuID)

        # get the user comment
        res = db.session.execute(text('SELECT commentID FROM comment WHERE uid=:uid'), {'uid' : uid})

        for row in res:
            if row['commentID'] == commentID:
                db.session.execute(text('DELETE FROM comment WHERE commentID=:commentID'), {'commentID' : commentID})
                db.session.commit()
                return {"message" : "Success delete comment"}, 200

        return {"message": "Cannot Found the comment"}, 400


# TODO comment search
# class Comment(Resource):
