
from flask import Flask
from flask_restful import Api, Resource
#
import config
#
app = Flask(__name__)
app.config.from_object(config)
api = Api(app)

def api_prefix(s):
	return '/db/v1' + s

class School(Resource):
	def get(self):
		return {}, 200

api.add_resource(School, api_prefix('/school'))

if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)
