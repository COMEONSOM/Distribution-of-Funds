from flask import Flask, request, jsonify, render_template, session
from db_config import create_app, mysql
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import secrets
import smtplib
from email.message import EmailMessage

app = create_app()
CORS(app)

reset_tokens = {}

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_email' not in session:
            return jsonify({"success": False, "error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')

        if not name or not email or not password:
            return jsonify({"success": False, "error": "All fields required."}), 400

        password_hash = generate_password_hash(password)

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO login_users_emt (name, email, password_hash) VALUES (%s, %s, %s)",
                       (name, email, password_hash))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"success": True})
    except Exception as e:
        print("❌ Register Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT password_hash FROM login_users_emt WHERE email = %s", (email,))
        result = cursor.fetchone()
        cursor.close()

        if result and check_password_hash(result[0], password):
            session['user_email'] = email
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Invalid credentials."})
    except Exception as e:
        print("Login Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_email', None)
    return jsonify({"success": True})

def send_reset_email(email, token):
    try:
        msg = EmailMessage()
        msg.set_content(f"""
Hi,

You requested to reset your password. Click the link below to set a new password:

http://localhost:5000/reset-password?token={token}

If you didn’t request this, you can ignore this email.
        """)
        msg['Subject'] = "Reset Your Password"
        msg['From'] = "noreply@expensetool.com"
        msg['To'] = email

        with smtplib.SMTP('localhost', 1025) as smtp:
            smtp.send_message(msg)

        return True
    except Exception as e:
        print("❌ Email send failed:", e)
        return False

@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json()
        email = data.get("email", "").strip()

        if not email:
            return jsonify({"success": False, "error": "Email is required."}), 400

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT email FROM login_users_emt WHERE email = %s", (email,))
        result = cursor.fetchone()
        cursor.close()

        if not result:
            return jsonify({"success": False, "error": "Email not found."}), 404

        token = secrets.token_urlsafe(32)
        reset_tokens[token] = email

        if send_reset_email(email, token):
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Email sending failed."}), 500

    except Exception as e:
        print("Forgot Password Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/reset_password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        token = data.get("token", "").strip()
        new_password = data.get("password", "")

        if not token or not new_password:
            return jsonify({"success": False, "error": "Token and password required."}), 400

        email = reset_tokens.get(token)
        if not email:
            return jsonify({"success": False, "error": "Invalid or expired token."}), 400

        hashed = generate_password_hash(new_password)

        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE login_users_emt SET password_hash = %s WHERE email = %s", (hashed, email))
        mysql.connection.commit()
        cursor.close()

        reset_tokens.pop(token, None)

        return jsonify({"success": True})
    except Exception as e:
        print("Reset Password Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
