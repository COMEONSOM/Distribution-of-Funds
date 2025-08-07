# ========================================
# 🚀 Travel Expense Manager - Backend App
# 🔧 Developed with Flask + MySQL
# 🧠 2025 Developer-Ready Structure
# ========================================

from flask import request, jsonify, render_template, session
from flask_cors import CORS
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from email.message import EmailMessage
import smtplib, secrets
import os


# Import local modules
from backend.db_config import create_app, get_db_connection

# ============================
# 🔧 Initialize Flask App
# ============================
app = create_app()
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow cross-origin requests (adjust for production)

# Store password reset tokens temporarily (in-memory)
reset_tokens = {}

# ==============================
# 🌐 Global Error Handler
# ==============================
@app.errorhandler(Exception)
def handle_exception(e):
    print(f"❌ Uncaught Exception: {e}")
    return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500

# ============================================
# 🔐 Login Required Decorator for Protected APIs
# ============================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return jsonify({"success": False, "error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

# ==================
# 📄 Serve Homepage
# ==================
@app.route('/')
def index():
    return render_template('index.html')


# ==================================
# 👤 User Registration API [POST]
# ==================================
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')

        if not all([name, email, password]):
            return jsonify({"success": False, "error": "All fields are required."}), 400

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert new user
        cursor.execute(
            "INSERT INTO login_users_emt (name, email, password_hash) VALUES (%s, %s, %s)",
            (name, email, hashed_password)
        )
        conn.commit()

        print(f"✅ Registered user: {email}")
        return jsonify({"success": True})

    except Exception as e:
        print("❌ Register Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ==================================
# 🔓 User Login API [POST]
# ==================================
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

        if result and check_password_hash(result[0], password):
            session['user_email'] = email
            session['trip_users'] = []
            print(f"✅ Login successful: {email}")
            return jsonify({"success": True})
        else:
            print(f"❌ Login failed for: {email}")
            return jsonify({"success": False, "error": "Invalid credentials."})

    except Exception as e:
        print("❌ Login Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ========================
# 🚪 Logout API [POST]
# ========================
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    print("👋 User logged out.")
    return jsonify({"success": True})


# ======================================
# ➕ Add User to Trip Session [Protected]
# ======================================
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
            return jsonify({"success": False, "error": "User already added."}), 400

        session['trip_users'].append(name)
        session.modified = True
        print(f"➕ Added trip user: {name}")

        return jsonify({"success": True})

    except Exception as e:
        print("❌ Add User Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500


# ======================================
# 👥 Get Trip Users in Session [Protected]
# ======================================
@app.route('/users', methods=['GET'])
@login_required
def get_users():
    try:
        users = session.get('trip_users', [])
        return jsonify([{"name": name} for name in users])

    except Exception as e:
        print("❌ Get Users Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500


# ========================================
# 📩 Forgot Password - Send Email [POST]
# ========================================
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

        if not result:
            return jsonify({"success": False, "error": "Email not registered."}), 404

        # Generate and store token
        token = secrets.token_urlsafe(32)
        reset_tokens[token] = email

        # Send reset email
        if send_reset_email(email, token):
            print(f"📧 Reset email sent to {email}")
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Email sending failed."}), 500

    except Exception as e:
        print("❌ Forgot Password Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ========================================
# 🔁 Reset Password Using Token [POST]
# ========================================
@app.route('/reset_password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        token = data.get("token", "").strip()
        new_password = data.get("password", "")

        if not token or not new_password:
            return jsonify({"success": False, "error": "Token and new password are required."}), 400

        email = reset_tokens.get(token)
        if not email:
            return jsonify({"success": False, "error": "Invalid or expired token."}), 400

        hashed = generate_password_hash(new_password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE login_users_emt SET password_hash = %s WHERE email = %s", (hashed, email))
        conn.commit()

        print(f"🔑 Password reset successful for {email}")
        reset_tokens.pop(token, None)  # Clear used token
        return jsonify({"success": True})

    except Exception as e:
        print("❌ Reset Password Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ================================
# 📬 Utility: Send Reset Email
# ================================
def send_reset_email(email, token):
    try:
        msg = EmailMessage()
        msg.set_content(f"""
Hi,

You requested to reset your password. Click the link below to reset:

http://localhost:5000/reset-password?token={token}

If you didn’t request this, please ignore this email.
        """)
        msg['Subject'] = "Reset Your Password"
        msg['From'] = "noreply@expensetool.com"
        msg['To'] = email

        # Local SMTP server for testing (run `python -m smtpd -c DebuggingServer -n localhost:1025`)
        with smtplib.SMTP('localhost', 1025) as smtp:
            smtp.send_message(msg)

        return True

    except Exception as e:
        print("❌ Email sending error:", e)
        return False


# ========================
# ▶️ Run the Flask App
# ========================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
