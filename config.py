DIALECT = 'mysql'
DRIVER = 'mysqldb'
USERNAME = 'domjudge'
PASSWORD = 'djpw'
HOST = '127.0.0.1'
PORT = '13306'
DATABASE = 'domjudge'

DB_URI = "{}+{}://{}:{}@{}:{}/{}?charset=utf8mb4".format(DIALECT, DRIVER, USERNAME, PASSWORD, HOST, PORT, DATABASE)
SQLALCHEMY_DATABASE_URI = "{}+{}://{}:{}@{}:{}/{}?charset=utf8mb4".format(DIALECT, DRIVER, USERNAME, PASSWORD, HOST, PORT, DATABASE)
SQLALCHEMY_TRACK_MODIFICATIONS = False