from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_mysqldb import MySQL
import mysql.connector
import os

mysql = MySQL()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback_secret')

    # Primary login DB config (Flask-MySQLdb)
    app.config['MYSQL_HOST'] = os.getenv('DB_HOST')
    app.config['MYSQL_PORT'] = int(os.getenv('DB_PORT', 3306))
    app.config['MYSQL_USER'] = os.getenv('DB_USER')
    app.config['MYSQL_PASSWORD'] = os.getenv('DB_PASSWORD')
    app.config['MYSQL_DB'] = os.getenv('DB_NAME')  # This can be login_system_emt
    app.config['MYSQL_SSL_CA'] = os.path.join(os.path.dirname(__file__), 'ca.pem')

    mysql.init_app(app)
    return app

def get_db_connection():
    return mysql.connection

def get_expense_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT')),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME_EXPENSE'),
        ssl_ca=os.path.join(os.path.dirname(__file__), 'ca.pem')
    )
