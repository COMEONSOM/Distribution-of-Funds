from flask import Flask
from flask_mysqldb import MySQL

mysql = MySQL()

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your-secret-key'

    # Configure connection (without fixing the DB here)
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'SOMNATH21!'  # ✅ your password
    # Do NOT set MYSQL_DB here

    mysql.init_app(app)
    return app
