from flask import Flask, request, jsonify, render_template, session
from db_config import create_app, mysql
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = create_app()
CORS(app)

# ---------------------- 🔐 AUTH HELPERS ----------------------

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_email' not in session:
            return jsonify({"success": False, "error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

# ---------------------- 🌐 FRONTEND ----------------------

@app.route('/')
def index():
    return render_template('index.html')

# ---------------------- 🔐 REGISTER ----------------------

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

# ---------------------- 🔐 LOGIN ----------------------

@app.route('/login', methods=['POST'])
def login():
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
    session.pop('user_email', None)
    return jsonify({"success": True})

# ---------------------- 👥 USERS ----------------------

@app.route('/users', methods=['GET'])
@login_required
def get_users():
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

# ---------------------- 💸 ADD EXPENSE ----------------------

@app.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    data = request.get_json()
    title = data.get('title')
    location = data.get('location')
    amount = float(data.get('amount', 0))
    paid_by = data.get('paid_by')
    distribution = data.get('distribution', {})

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("USE expense_management_tools_database;")

        cursor.execute("SELECT id FROM users WHERE name = %s", (paid_by,))
        paid_by_id = cursor.fetchone()
        if not paid_by_id:
            return jsonify({"success": False, "error": "Payer not found"})
        paid_by_id = paid_by_id[0]

        cursor.execute(
            "INSERT INTO expenses (title, location, amount, paid_by) VALUES (%s, %s, %s, %s)",
            (title, location, amount, paid_by_id)
        )
        expense_id = cursor.lastrowid

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

# ---------------------- 📊 SUMMARY ----------------------

@app.route('/summary', methods=['GET'])
@login_required
def summary():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("USE expense_management_tools_database;")

        cursor.execute("SELECT id, name FROM users")
        user_map = {uid: name for uid, name in cursor.fetchall()}

        cursor.execute("SELECT paid_by, SUM(amount) FROM expenses GROUP BY paid_by")
        contributions = {user_map[uid]: float(paid) for uid, paid in cursor.fetchall()}
        for name in user_map.values():
            contributions.setdefault(name, 0.0)

        cursor.execute("""
            SELECT u.name, SUM(es.amount_owed)
            FROM expense_shares es
            JOIN users u ON es.user_id = u.id
            GROUP BY u.name
        """)
        owed = {name: float(amt) for name, amt in cursor.fetchall()}
        for name in user_map.values():
            owed.setdefault(name, 0.0)

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

# ---------------------- 🚀 RUN ----------------------

if __name__ == '__main__':
    app.run(debug=True)
