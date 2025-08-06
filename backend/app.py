from flask import Flask, request, jsonify, render_template, session
from backend.db_config import create_app, mysql, get_db_connection
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from email.message import EmailMessage
import secrets
import smtplib
import os

# 🔧 Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# 🔐 In-memory reset tokens
reset_tokens = {}

# ===========================
# 🌍 GLOBAL ERROR HANDLER
# ===========================
@app.errorhandler(Exception)
def handle_exception(e):
    print(f"❌ Uncaught Exception: {e}")
    return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500

# ===================================
# 🔐 AUTHENTICATION REQUIRED DECORATOR
# ===================================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_email' not in session:
            return jsonify({"success": False, "error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

# ===========
# 🌐 HOME PAGE
# ===========
@app.route('/')
def index():
    return render_template('index.html')

# ======================
# 👤 USER REGISTRATION
# ======================
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
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO login_users_emt (name, email, password_hash) VALUES (%s, %s, %s)",
            (name, email, password_hash)
        )
        conn.commit()
        cursor.close()
        conn.close()

        print(f"✅ User registered: {email}")
        return jsonify({"success": True})

    except Exception as e:
        print("❌ Register Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

# ============
# 🔓 USER LOGIN
# ============
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')

        print(f"🛂 Login Attempt: {email}")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM login_users_emt WHERE email = %s", (email,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result:
            print("🔐 Password hash found. Verifying password...")
        else:
            print("❌ No user found with this email.")

        if result and check_password_hash(result[0], password):
            session['user_email'] = email
            session['trip_users'] = []
            print(f"✅ Login successful: {email}")
            return jsonify({"success": True})
        else:
            print(f"❌ Invalid credentials for: {email}")
            return jsonify({"success": False, "error": "Invalid credentials."})

    except Exception as e:
        print("❌ Login Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

# ============
# 🚪 LOGOUT
# ============
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_email', None)
    session.pop('trip_users', None)
    print("👋 User logged out.")
    return jsonify({"success": True})

# ==================
# ➕ ADD TRIP USER
# ==================
@app.route('/add_user', methods=['POST'])
@login_required
def add_user():
    try:
        data = request.get_json()
        name = data.get("name", "").strip()

        if not name:
            return jsonify({"success": False, "error": "Name is required."}), 400

        if 'trip_users' not in session:
            session['trip_users'] = []

        if name in session['trip_users']:
            return jsonify({"success": False, "error": "User already exists."}), 400

        session['trip_users'].append(name)
        session.modified = True
        print(f"➕ Trip user added: {name}")

        return jsonify({"success": True})

    except Exception as e:
        print("❌ Add User Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

# ==================
# 👥 GET TRIP USERS
# ==================
@app.route('/users', methods=['GET'])
@login_required
def get_users():
    try:
        trip_users = session.get('trip_users', [])
        return jsonify([{"name": name} for name in trip_users])
    except Exception as e:
        print("❌ Get Users Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

# ===========================
# 🔐 FORGOT PASSWORD (EMAIL)
# ===========================
@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json()
        email = data.get("email", "").strip()

        if not email:
            return jsonify({"success": False, "error": "Email is required."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM login_users_emt WHERE email = %s", (email,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result:
            return jsonify({"success": False, "error": "Email not found."}), 404

        token = secrets.token_urlsafe(32)
        reset_tokens[token] = email

        if send_reset_email(email, token):
            print(f"📧 Reset email sent to {email}")
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Email sending failed."}), 500

    except Exception as e:
        print("❌ Forgot Password Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

# =========================
# 🔁 RESET PASSWORD (TOKEN)
# =========================
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

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE login_users_emt SET password_hash = %s WHERE email = %s", (hashed, email))
        conn.commit()
        cursor.close()
        conn.close()

        reset_tokens.pop(token, None)
        print(f"🔑 Password reset successful for {email}")

        return jsonify({"success": True})
    except Exception as e:
        print("❌ Reset Password Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

# =====================
# 📧 EMAIL SENDER FUNC
# =====================
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

# ======================
# 🚀 RUN APP
# ======================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
