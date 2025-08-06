from dotenv import load_dotenv
import os
import mysql.connector
from flask import Flask
from flask_mysqldb import MySQL

# Load .env variables
load_dotenv()

# Initialize Flask-MySQLdb instance
mysql = MySQL()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback_secret')

    # Primary login DB config (Flask-MySQLdb)
    app.config['MYSQL_HOST'] = os.getenv('DB_HOST')
    app.config['MYSQL_PORT'] = int(os.getenv('DB_PORT', 3306))
    app.config['MYSQL_USER'] = os.getenv('DB_USER')
    app.config['MYSQL_PASSWORD'] = os.getenv('DB_PASSWORD')
    app.config['MYSQL_DB'] = os.getenv('DB_NAME')  # e.g., login_system_emt

    # Optional: Use SSL certificate for secure connection (Aiven)
    ca_path = os.path.join(os.path.dirname(__file__), 'ca.pem')
    if os.path.exists(ca_path):
        app.config['MYSQL_SSL_CA'] = ca_path

    # Initialize Flask-MySQLdb
    mysql.init_app(app)

    return app

def get_db_connection():
    """
    Returns a connection object for the login system (Flask-MySQLdb).
    Usage: cursor = get_db_connection().cursor()
    """
    return mysql.connection

def get_expense_db_connection():
    """
    Returns a MySQL Connector connection object for expense system.
    Usage: cursor = get_expense_db_connection().cursor(dictionary=True)
    """
    ca_path = os.path.join(os.path.dirname(__file__), 'ca.pem')

    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME_EXPENSE'),  # e.g., expense_management_tools_database
            ssl_ca=ca_path if os.path.exists(ca_path) else None
        )
        return connection
    except mysql.connector.Error as err:
        print(f"[DB ERROR] Expense DB connection failed: {err}")
        return None
