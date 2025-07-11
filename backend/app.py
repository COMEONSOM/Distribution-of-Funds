from flask import Flask, request, jsonify, render_template, session
from db_config import create_app, mysql
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import secrets
import smtplib
from email.message import EmailMessage

# Initialize Flask app
app = create_app()
CORS(app)

# =========================
# 🔐 AUTH HELPERS
# =========================

reset_tokens = {}  # Temporary storage for reset tokens

def login_required(f):
    """Decorator to enforce login for certain routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_email' not in session:
            return jsonify({"success": False, "error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

# =========================
# 🌐 FRONTEND ROUTE
# =========================

@app.route('/')
def index():
    """Serve the main frontend page."""
    return render_template('index.html')

# =========================
# 🔐 REGISTER
# =========================

@app.route('/register', methods=['POST'])
def register():
    """Handle user registration."""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')

        if not name or not email or not password:
            return jsonify({"success": False, "error": "All fields required."}), 400

        password_hash = generate_password_hash(password)

        cursor = mysql.connection.cursor()
        cursor.execute("USE login_system_emt;")
        cursor.execute(
            "INSERT INTO login_users_emt (name, email, password_hash) VALUES (%s, %s, %s)",
            (name, email, password_hash)
        )
        mysql.connection.commit()
        cursor.close()

        return jsonify({"success": True})
    except Exception as e:
        print("❌ Register Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

# =========================
# 🔐 LOGIN / LOGOUT
# =========================

@app.route('/login', methods=['POST'])
def login():
    """Authenticate and log in a user."""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')

        cursor = mysql.connection.cursor()
        cursor.execute("USE login_system_emt;")
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
    """Log out the current user."""
    session.pop('user_email', None)
    return jsonify({"success": True})

# =========================
# 📧 FORGOT PASSWORD
# =========================

def send_reset_email(email, token):
    """Send a password reset email with the given token."""
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

        with smtplib.SMTP('localhost', 1025) as smtp:  # Dev SMTP server
            smtp.send_message(msg)

        return True
    except Exception as e:
        print("❌ Email send failed:", e)
        return False

@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    """Start password reset process by sending an email."""
    try:
        data = request.get_json()
        email = data.get("email", "").strip()

        if not email:
            return jsonify({"success": False, "error": "Email is required."}), 400

        cursor = mysql.connection.cursor()
        cursor.execute("USE login_system_emt;")
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
    """Handle password reset submission."""
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
        cursor.execute("USE login_system_emt;")
        cursor.execute("UPDATE login_users_emt SET password_hash = %s WHERE email = %s", (hashed, email))
        mysql.connection.commit()
        cursor.close()

        reset_tokens.pop(token, None)

        return jsonify({"success": True})
    except Exception as e:
        print("Reset Password Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

# =========================
# 👥 USERS
# =========================

@app.route('/users', methods=['GET'])
@login_required
def get_users():
    """Return a list of all users."""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("USE expense_management_tools_database;")
        cursor.execute("SELECT name FROM users ORDER BY name")
        users = [{"name": row[0]} for row in cursor.fetchall()]
        cursor.close()
        return jsonify(users)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/add_user', methods=['POST'])
@login_required
def add_user():
    """Add a new user to the system."""
    data = request.get_json()
    name = data.get('name', '').strip()

    if not name:
        return jsonify({"success": False, "error": "Name is required"})

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("USE expense_management_tools_database;")
        cursor.execute("INSERT IGNORE INTO users (name) VALUES (%s)", (name,))
        mysql.connection.commit()
        cursor.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# =========================
# 💸 ADD EXPENSE
# =========================

@app.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    """Save a new expense and its distribution."""
    data = request.get_json()
    title = data.get('title')
    location = data.get('location')
    amount = float(data.get('amount', 0))
    paid_by = data.get('paid_by')
    distribution = data.get('distribution', {})

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("USE expense_management_tools_database;")

        # Get paid_by user id
        cursor.execute("SELECT id FROM users WHERE name = %s", (paid_by,))
        paid_by_id = cursor.fetchone()
        if not paid_by_id:
            return jsonify({"success": False, "error": "Payer not found"})
        paid_by_id = paid_by_id[0]

        # Insert into expenses table
        cursor.execute(
            "INSERT INTO expenses (title, location, amount, paid_by) VALUES (%s, %s, %s, %s)",
            (title, location, amount, paid_by_id)
        )
        expense_id = cursor.lastrowid

        # Insert expense shares
        for name, owed_amt in distribution.items():
            cursor.execute("SELECT id FROM users WHERE name = %s", (name,))
            user_id = cursor.fetchone()
            if user_id:
                cursor.execute(
                    "INSERT INTO expense_shares (expense_id, user_id, amount_owed) VALUES (%s, %s, %s)",
                    (expense_id, user_id[0], owed_amt)
                )

        mysql.connection.commit()
        cursor.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# =========================
# 🗑 DELETE HISTORY
# =========================

# ---------------------- 🗑️ DELETE HISTORY ----------------------

@app.route('/delete_history', methods=['POST'])
@login_required
def delete_history():
    try:
        user_email = session.get('user_email')

        # Get user_id from login DB (to avoid accidental mismatch)
        cursor = mysql.connection.cursor()
        cursor.execute("USE login_system_emt;")
        cursor.execute("SELECT id, name FROM login_users_emt WHERE email = %s", (user_email,))
        result = cursor.fetchone()
        if not result:
            cursor.close()
            return jsonify({"success": False, "error": "User not found."}), 404

        user_name = result[1]
        cursor.close()

        # Now switch to expense DB and delete related data
        cursor = mysql.connection.cursor()
        cursor.execute("USE expense_management_tools_database;")

        # Find user ID in expense DB
        cursor.execute("SELECT id FROM users WHERE name = %s", (user_name,))
        user = cursor.fetchone()
        if not user:
            cursor.close()
            return jsonify({"success": False, "message": "No expense data found to delete."})

        user_id = user[0]

        # Start transaction: delete all expenses where user paid
        cursor.execute("""
            DELETE FROM expenses 
            WHERE paid_by = %s
        """, (user_id,))

        # Delete all shares where user was involved
        cursor.execute("""
            DELETE FROM expense_shares 
            WHERE user_id = %s
        """, (user_id,))

        mysql.connection.commit()
        cursor.close()

        return jsonify({"success": True, "message": "All expense history deleted."})
    except Exception as e:
        print("❌ Delete History Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500


# =========================
# 📊 SUMMARY
# =========================

@app.route('/summary', methods=['GET'])
@login_required
def summary():
    """Generate and return expense summary."""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("USE expense_management_tools_database;")

        # Get user mapping
        cursor.execute("SELECT id, name FROM users")
        user_map = {uid: name for uid, name in cursor.fetchall()}

        # Contributions
        cursor.execute("SELECT paid_by, SUM(amount) FROM expenses GROUP BY paid_by")
        contributions = {user_map[uid]: float(paid) for uid, paid in cursor.fetchall()}
        for name in user_map.values():
            contributions.setdefault(name, 0.0)

        # Owed amounts
        cursor.execute("""
            SELECT u.name, SUM(es.amount_owed)
            FROM expense_shares es
            JOIN users u ON es.user_id = u.id
            GROUP BY u.name
        """)
        owed = {name: float(amt) for name, amt in cursor.fetchall()}
        for name in user_map.values():
            owed.setdefault(name, 0.0)

        # Net balances
        net = {u: contributions[u] - owed[u] for u in user_map.values()}
        total = sum(contributions.values())

        net_contribs = [
            {
                "person": u,
                "paid": round(contributions[u], 2),
                "should_pay": round(owed[u], 2),
                "net_balance": round(net[u], 2)
            }
            for u in user_map.values()
        ]

        # Settlements (DSA optimized: two pointer)
        owe_list = sorted([(u, -amt) for u, amt in net.items() if amt < -0.01], key=lambda x: x[1])
        owed_list = sorted([(u, amt) for u, amt in net.items() if amt > 0.01], key=lambda x: x[1])

        settlements = []
        statements = []
        i = j = 0

        while i < len(owe_list) and j < len(owed_list):
            payer, amt_owe = owe_list[i]
            receiver, amt_owed = owed_list[j]

            settle_amt = round(min(amt_owe, amt_owed), 2)
            if settle_amt > 0:
                settlements.append({
                    "who_pays": payer,
                    "to_whom": receiver,
                    "amount": settle_amt
                })
                statements.append(f"{payer} has to pay ₹{settle_amt:.2f} to {receiver}.")

            owe_list[i] = (payer, amt_owe - settle_amt)
            owed_list[j] = (receiver, amt_owed - settle_amt)

            if owe_list[i][1] <= 0.01:
                i += 1
            if owed_list[j][1] <= 0.01:
                j += 1

        return jsonify({
            "total_expense": round(total, 2),
            "contributions": [{"name": k, "paid": round(v, 2)} for k, v in contributions.items()],
            "net_contributions": net_contribs,
            "settlements_table": settlements,
            "settlements_statements": statements
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# =========================
# 🚀 RUN
# =========================

if __name__ == '__main__':
    app.run(debug=True)
