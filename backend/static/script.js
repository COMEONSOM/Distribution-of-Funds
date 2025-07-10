let users = [];

// 🔐 Register New User
async function registerUser() {
  const name = document.getElementById("registerName").value.trim();
  const email = document.getElementById("registerEmail").value.trim();
  const password = document.getElementById("registerPassword").value.trim();

  if (!name || !email || !password) {
    return showAuthMessage("⚠ Please fill in all fields", "error");
  }

  try {
    const res = await fetch("/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ name, email, password })
    });

    const result = await res.json();

    if (!res.ok || !result.success) {
      return showAuthMessage(`❌ Registration failed: ${result.error || res.status}`, "error");
    }

    showAuthMessage("✅ Registration successful. You can now log in.", "success");

    // Optional: auto switch to login view
    setTimeout(() => {
      document.getElementById("registerName").value = "";
      document.getElementById("registerEmail").value = "";
      document.getElementById("registerPassword").value = "";
    }, 500);

  } catch (err) {
    console.error("Registration error:", err);
    showAuthMessage("❌ Network or server error during registration.", "error");
  }
}

// 🔓 Login Existing User
async function loginUser() {
  const email = document.getElementById("loginEmail").value.trim();
  const password = document.getElementById("loginPassword").value.trim();

  if (!email || !password) {
    return showAuthMessage("⚠ Please enter email and password", "error");
  }

  try {
    const res = await fetch("/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email, password })
    });

    const result = await res.json();

    if (!res.ok || !result.success) {
      return showAuthMessage(`❌ Login failed: ${result.error || res.status}`, "error");
    }

    document.getElementById("userEmailDisplay").textContent = email;
    document.getElementById("login-section").style.display = "none";
    document.getElementById("register-section").style.display = "none";
    document.getElementById("user-info").style.display = "block";
    showAuthMessage("✅ Logged in successfully!", "success");

    await loadUsers();
    await loadSummary();
  } catch (err) {
    console.error("Login error:", err);
    showAuthMessage("❌ Network or server error during login.", "error");
  }
}

// 🚪 Logout
async function logoutUser() {
  try {
    const res = await fetch("/logout", {
      method: "POST",
      credentials: "include"
    });

    const result = await res.json();

    if (!res.ok || !result.success) {
      return showAuthMessage("❌ Logout failed.", "error");
    }

    document.getElementById("userEmailDisplay").textContent = "";
    document.getElementById("login-section").style.display = "block";
    document.getElementById("register-section").style.display = "block";
    document.getElementById("user-info").style.display = "none";
    document.getElementById("summary").innerHTML = "";
    users = [];
    showAuthMessage("👋 Logged out successfully!", "success");

  } catch (err) {
    console.error("Logout error:", err);
    showAuthMessage("❌ Network or server error during logout.", "error");
  }
}

// ℹ️ Auth messages
function showAuthMessage(msg, type) {
  const div = document.getElementById("auth-message");
  div.className = `message ${type}`;
  div.textContent = msg;
  setTimeout(() => { div.textContent = ""; }, 3000);
}

// 📢 UI Messages
function showMessage(message, type) {
  const msgDiv = document.createElement('div');
  msgDiv.className = `message ${type}`;
  msgDiv.textContent = message;
  document.body.appendChild(msgDiv);
  setTimeout(() => msgDiv.remove(), 3000);
}

// 👥 Load users
async function loadUsers() {
  try {
    const res = await fetch('/users', { credentials: "include" });
    const data = await res.json();

    if (!res.ok || !Array.isArray(data)) {
      throw new Error(`Error ${res.status} loading users`);
    }

    users = data.map(u => u.name);
    updatePaidByDropdown();
    renderUserList();

  } catch (err) {
    console.error("Error fetching users:", err);
    showMessage(`❌ Failed to load user list (${err.message})`, "error");
  }
}

// ➕ Add user
async function addUser() {
  const nameInput = document.getElementById('newUserName');
  const name = nameInput.value.trim();

  if (!name || users.includes(name)) {
    return showMessage("⚠ Enter a valid and unique user name.", "error");
  }

  try {
    const res = await fetch('/add_user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: "include",
      body: JSON.stringify({ name })
    });

    const result = await res.json();

    if (!res.ok || !result.success) {
      throw new Error(result.error || `Error ${res.status}`);
    }

    users.push(name);
    nameInput.value = '';
    updatePaidByDropdown();
    renderUserList();
    showMessage("✅ User added successfully!", "success");

  } catch (err) {
    console.error("Error adding user:", err);
    showMessage(`❌ Network/server error: ${err.message}`, "error");
  }
}

// 🧾 Submit expense form
document.getElementById('expenseForm').addEventListener('submit', async function (e) {
  e.preventDefault();

  const title = this.title.value.trim();
  const location = this.location.value.trim();
  const amount = parseFloat(this.amount.value.trim());
  const paid_by = this.paid_by.value.trim();

  if (!title || !location || isNaN(amount) || !paid_by || users.length === 0) {
    return showMessage("⚠ Please fill in all fields and add users.", "error");
  }

  const distribution = {};
  let valid = true;

  document.querySelectorAll('.owed-input').forEach(input => {
    const name = input.getAttribute('data-username');
    const owed = parseFloat(input.value);
    if (isNaN(owed)) valid = false;
    distribution[name] = owed || 0;
  });

  if (!valid) {
    return showMessage("⚠ Please enter valid owed amounts for all users.", "error");
  }

  const totalOwed = Object.values(distribution).reduce((a, b) => a + b, 0);
  if (Math.abs(totalOwed - amount) > 0.01) {
    return showMessage(`⚠ Total owed (${totalOwed}) must match total amount (${amount}).`, "error");
  }

  try {
    const res = await fetch('/add_expense', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: "include",
      body: JSON.stringify({ title, location, amount, paid_by, distribution })
    });

    const result = await res.json();

    if (!res.ok || !result.success) {
      throw new Error(result.error || `Error ${res.status}`);
    }

    showMessage("✅ Expense added successfully!", "success");
    this.reset();
    updatePaidByDropdown();
    renderUserList();

  } catch (err) {
    console.error("Expense error:", err);
    showMessage(`❌ Network/server error: ${err.message}`, "error");
  }
});

// 📊 Load summary
async function loadSummary() {
  try {
    const res = await fetch('/summary', { credentials: "include" });
    const data = await res.json();
    const summaryDiv = document.getElementById('summary');

    if (!res.ok || data.success === false) {
      summaryDiv.innerHTML = "<p>❌ Failed to load summary.</p>";
      return;
    }

    const {
      total_expense,
      net_contributions,
      settlements_table,
      settlements_statements
    } = data;

    let html = `
      <h3>💰 Total Trip Expense: ₹${total_expense.toFixed(2)}</h3>
      <h3>📊 Net Contributions</h3>
      <table><thead><tr><th>Person</th><th>Paid</th><th>Should Pay</th><th>Net Balance</th></tr></thead>
      <tbody>
        ${net_contributions.map(row => `
          <tr>
            <td>${row.person}</td>
            <td>₹${row.paid.toFixed(2)}</td>
            <td>₹${row.should_pay.toFixed(2)}</td>
            <td>${row.net_balance >= 0 ? "+" : "-"}₹${Math.abs(row.net_balance).toFixed(2)} ${row.net_balance > 0 ? "(gets back)" : "(owes)"}</td>
          </tr>`).join('')}
      </tbody></table>

      <h3>🔁 Correct Settlements</h3>
      <table><thead><tr><th>Who Pays</th><th>To Whom</th><th>Amount</th></tr></thead>
      <tbody>
        ${settlements_table.map(s => `
          <tr>
            <td>${s.who_pays}</td>
            <td>${s.to_whom}</td>
            <td>₹${s.amount.toFixed(2)}</td>
          </tr>`).join('')}
      </tbody></table>

      <h3>✅ Final Human-Readable Statements</h3>
      <ul>
        ${settlements_statements.length
          ? settlements_statements.map(s => `<li>${s}</li>`).join('')
          : "<li>✅ Everyone is settled up!</li>"
        }
      </ul>`;

    summaryDiv.innerHTML = html;

  } catch (err) {
    console.error("Summary error:", err);
    showMessage(`❌ Failed to load summary: ${err.message}`, "error");
  }
}

// 🔽 Paid by dropdown
function updatePaidByDropdown() {
  const dropdown = document.getElementById('paid_by');
  dropdown.innerHTML = '<option value="">-- Select Paid By --</option>';
  users.forEach(user => {
    const option = document.createElement('option');
    option.value = user;
    option.textContent = user;
    dropdown.appendChild(option);
  });
}

// 👤 Render owed amount inputs
function renderUserList() {
  const container = document.getElementById('userList');
  container.innerHTML = '';
  users.forEach(user => {
    const div = document.createElement('div');
    div.classList.add('user-row');
    div.innerHTML = `
      <label>${user}</label>
      <input 
        type="number" 
        step="0.01" 
        class="owed-input" 
        data-username="${user}" 
        placeholder="Amount owed by ${user}" 
        required
      />`;
    container.appendChild(div);
  });
}
