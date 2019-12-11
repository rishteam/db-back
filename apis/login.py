import requests
from flask_restful import Resource, reqparse
from sqlalchemy import text
import time

from crawler.course import try_to_login
from utils import md5
from db import db
import config

# TODO: Figure out why didn't location='form' work
login_parser = reqparse.RequestParser()
login_parser.add_argument('username', type=str, required=True,
                            help='Please provide the username or reference the API Docs')
login_parser.add_argument('password', type=str, required=True,
                            help='Please provide the password or reference the API Docs')

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
                SET `token`=:token, `lastlogin`=:time
                WHERE username=:username
                ''')
                db.session.execute(sql, {
                    'token': token,
                    'username': user,
                    'time': time.time()
                })
                db.session.commit()

        return {'token': token}, 200
