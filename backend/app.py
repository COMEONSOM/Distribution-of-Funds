from flask import Flask, request, jsonify, render_template
from db_config import create_app
from flask_cors import CORS
import MySQLdb.cursors

app, mysql = create_app()
CORS(app)

# 🌐 Serve frontend
@app.route('/')
def index():
    return render_template('index.html')


# 📦 Get all users
@app.route('/users', methods=['GET'])
def get_users():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT name FROM users ORDER BY name")
        users = [{"name": row[0]} for row in cursor.fetchall()]
        cursor.close()
        return jsonify(users)
    except Exception as e:
        print("Error fetching users:", e)
        return jsonify({"success": False, "error": str(e)})


# ➕ Add new user
@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.get_json()
    name = data.get('name', '').strip()
    if not name:
        return jsonify({"success": False, "error": "Name is required."})

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT IGNORE INTO users (name) VALUES (%s)", (name,))
        mysql.connection.commit()
        cursor.close()
        return jsonify({"success": True})
    except Exception as e:
        print("Error adding user:", e)
        return jsonify({"success": False, "error": str(e)})


# 🧾 Add new expense
@app.route('/add_expense', methods=['POST'])
def add_expense():
    data = request.get_json()
    title = data.get('title')
    location = data.get('location')
    amount = float(data.get('amount', 0))
    paid_by = data.get('paid_by')
    distribution = data.get('distribution', {})

    if not title or not location or amount <= 0 or not paid_by or not distribution:
        return jsonify({"success": False, "error": "Invalid input."})

    try:
        cursor = mysql.connection.cursor()

        # Get paid_by user_id
        cursor.execute("SELECT id FROM users WHERE name = %s", (paid_by,))
        paid_by_id = cursor.fetchone()
        if not paid_by_id:
            return jsonify({"success": False, "error": "Payer not found."})

        paid_by_id = paid_by_id[0]

        # Insert expense
        cursor.execute("""
            INSERT INTO expenses (title, location, amount, paid_by)
            VALUES (%s, %s, %s, %s)
        """, (title, location, amount, paid_by_id))
        expense_id = cursor.lastrowid

        # Insert expense shares
        for user_name, owed_amount in distribution.items():
            cursor.execute("SELECT id FROM users WHERE name = %s", (user_name,))
            user_id = cursor.fetchone()
            if user_id:
                user_id = user_id[0]
                cursor.execute("""
                    INSERT INTO expense_shares (expense_id, user_id, amount_owed)
                    VALUES (%s, %s, %s)
                """, (expense_id, user_id, owed_amount))

        mysql.connection.commit()
        cursor.close()
        return jsonify({"success": True})

    except Exception as e:
        print("Error adding expense:", e)
        return jsonify({"success": False, "error": str(e)})


# 📊 Get summary (pairwise settlements + totals)
@app.route('/summary', methods=['GET'])
def get_summary():
    try:
        cursor = mysql.connection.cursor()

        # 1. Get all users
        cursor.execute("SELECT id, name FROM users")
        user_map = {uid: name for uid, name in cursor.fetchall()}
        name_to_id = {v: k for k, v in user_map.items()}

        # 2. Get total paid by each user
        cursor.execute("""
            SELECT paid_by, SUM(amount) 
            FROM expenses 
            GROUP BY paid_by
        """)
        contributions = {user_map[uid]: float(paid) for uid, paid in cursor.fetchall()}

        # Initialize all users with 0 paid
        for name in user_map.values():
            contributions.setdefault(name, 0.0)

        total_expense = sum(contributions.values())

        # 3. Get total owed by each user from expense_shares
        cursor.execute("""
            SELECT u.name, SUM(es.amount_owed)
            FROM expense_shares es
            JOIN users u ON es.user_id = u.id
            GROUP BY u.name
        """)
        owed = {name: float(amt) for name, amt in cursor.fetchall()}

        # Initialize anyone who hasn’t owed anything
        for name in user_map.values():
            owed.setdefault(name, 0.0)

        # 4. Calculate net balances = Paid - Owed
        net_balances = {user: contributions[user] - owed[user] for user in user_map.values()}

        # 5. Prepare net contributions table
        net_contribs = [
            {
                "person": user,
                "paid": round(contributions[user], 2),
                "should_pay": round(owed[user], 2),
                "net_balance": round(net_balances[user], 2)
            }
            for user in user_map.values()
        ]

        # 6. Compute settlements
        owe_list = sorted([(u, -amt) for u, amt in net_balances.items() if amt < -0.01], key=lambda x: x[1])
        owed_list = sorted([(u, amt) for u, amt in net_balances.items() if amt > 0.01], key=lambda x: x[1])

        settlements = []
        statements = []

        i = j = 0
        while i < len(owe_list) and j < len(owed_list):
            payer, amt_owe = owe_list[i]
            receiver, amt_owed = owed_list[j]

            settle_amt = round(min(amt_owe, amt_owed), 2)
            if payer != receiver and settle_amt > 0:
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
            "total_expense": round(total_expense, 2),
            "contributions": [{"name": k, "paid": round(v, 2)} for k, v in contributions.items()],
            "net_contributions": net_contribs,
            "settlements_table": settlements,
            "settlements_statements": statements
        })

    except Exception as e:
        print("Error in /summary:", e)
        return jsonify({"success": False, "error": str(e)})


if __name__ == '__main__':
    app.run(debug=True)
