import requests
from flask_restful import Resource, reqparse
from sqlalchemy import text
import time

from crawler.course import try_to_login, get_person_identity, grade_to_num
from utils import md5
from db import db
import config

# TODO: Figure out why didn't location='form' work
login_parser = reqparse.RequestParser()
login_parser.add_argument('username', type=str, required=True,
                            help='Please provide the username or reference the API Docs')
login_parser.add_argument('password', type=str, required=True,
                            help='Please provide the password or reference the API Docs')

def update_user_info(stuID, info):
    """Update the user infomation"""
    res = db.session.execute(text('''
        UPDATE user SET complete_point=:complete_point, avg_score=:avg_score, grade=:grade, real_name=:real_name
        WHERE username=:stuID
    '''), {
        'complete_point': info['complete_point'],
        'avg_score': info['total_avg_score'],
        'grade': grade_to_num(info['grade']),
        'real_name': info['name'],
        'stuID': stuID
    })
    db.session.commit()

class LoginRes(Resource):
    def post(self):
        args = login_parser.parse_args() # get args if succeeded
        user, passwd = args['username'], args['password']
        # Login
        r = requests.Session()
        print('[*] debug - try to login')
        fail, _ = try_to_login(r, user, passwd)
        if fail:
            return {'message': 'Failed to login'}, 400
        print('[*] debug - login success')

        # Generate the token
        dic = {'username': user, 'password': passwd}
        dic['secret'] = md5(config.SECRET_KEY)
        token = md5(dic)  # TODO: add salt or use passlib?
        # print(token)

        # Check if a user is in the db
        res = db.session.execute(
            text('SELECT * FROM `user` WHERE username=:user'), {'user': user}
        )
        if res.returns_rows:
            # If not existing, add a new user
            if res.rowcount == 0:
                sql = text('''
                    INSERT INTO `Course`.`user` (`username`, `password`, `perm`, `firstlogin`, `lastlogin`, `token`)
                    VALUES (:username, :passwd, 0, :time, :time, :token);
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
                SET `token`=:token, `lastlogin`=:time
                WHERE username=:username
                ''')
                db.session.execute(sql, {
                    'token': token,
                    'username': user,
                    'time': time.time()
                })
                db.session.commit()
            # Update user information
            # TODO: make this async
            info = get_person_identity(r, user, passwd)
            update_user_info(user, info)

        return {'token': token}, 200
