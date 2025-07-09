from flask_mysqldb import MySQL
from flask import Flask
#from db_config import create_app
def create_app():
    app = Flask(__name__)

    # MySQL Config
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'SOMNATH21!'
    app.config['MYSQL_DB'] = 'expense_management_tools_database'

    mysql = MySQL(app)
    return app, mysql
