from dotenv import load_dotenv
load_dotenv()  # 👈 Load .env automatically

from flask import Flask
from flask_mysqldb import MySQL
import os

mysql = MySQL()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key')

    # Aiven MySQL Connection
    app.config['MYSQL_HOST'] = os.getenv('DB_HOST')
    app.config['MYSQL_PORT'] = int(os.getenv('DB_PORT', 3306))
    app.config['MYSQL_USER'] = os.getenv('DB_USER')
    app.config['MYSQL_PASSWORD'] = os.getenv('DB_PASSWORD')
    app.config['MYSQL_DB'] = os.getenv('DB_NAME')
    app.config['MYSQL_SSL_CA'] = os.path.join(os.path.dirname(__file__), 'ca.pem')

    mysql.init_app(app)
    return app
