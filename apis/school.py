from flask import Flask, request
from flask_restful import Api, Resource, abort, reqparse
from sqlalchemy import text

from db import db

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
