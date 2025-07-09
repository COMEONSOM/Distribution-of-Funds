let users = []; // Global user list

// 📦 Load users from backend on page load
async function loadUsers() {
  try {
    const res = await fetch('/users');
    const data = await res.json();
    if (Array.isArray(data)) {
      users = data.map(u => u.name); // assuming backend sends [{name: 'Somnath'}, ...]
      updatePaidByDropdown();
      renderUserList();
    }
  } catch (err) {
    console.error("Error fetching users:", err);
    showMessage("❌ Failed to load user list.", "error");
  }
}

// 👥 Add a new user manually
async function addUser() {
  const nameInput = document.getElementById('newUserName');
  const name = nameInput.value.trim();

  if (!name || users.includes(name)) {
    showMessage("⚠ Enter a valid and unique user name.", "error");
    return;
  }

  try {
    const res = await fetch('/add_user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    const result = await res.json();

    if (result.success) {
      users.push(name);
      nameInput.value = '';
      updatePaidByDropdown();
      renderUserList();
      showMessage("✅ User added successfully!", "success");
    } else {
      showMessage(`❌ Could not add user: ${result.error}`, "error");
    }
  } catch (err) {
    console.error("Error adding user:", err);
    showMessage("❌ Network error adding user.", "error");
  }
}

// 🔄 Update the "Paid By" dropdown
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

// 👤 Render owed input fields
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
      />
    `;
    container.appendChild(div);
  });
}

// 🧾 Handle expense form submit
document.getElementById('expenseForm').addEventListener('submit', async function (e) {
  e.preventDefault();

  const title = this.title.value.trim();
  const location = this.location.value.trim();
  const amount = this.amount.value.trim();
  const paid_by = this.paid_by.value.trim();

  if (!title || !location || !amount || !paid_by || users.length === 0) {
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
  if (Math.abs(totalOwed - parseFloat(amount)) > 0.01) {
    return showMessage(`⚠ Total owed (${totalOwed}) must match total amount (${amount}).`, "error");
  }

  const payload = { title, location, amount, paid_by, distribution };

  try {
    const res = await fetch('/add_expense', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const result = await res.json();
    if (result.success) {
      showMessage("✅ Expense added successfully!", "success");
      this.reset();
      updatePaidByDropdown();
      renderUserList();
    } else {
      showMessage(`❌ Error: ${result.error}`, "error");
    }
  } catch (err) {
    console.error("Error adding expense:", err);
    showMessage("❌ Network error. Please try again.", "error");
  }
});

// 📊 Load settlements summary
async function loadSummary() {
  try {
    const res = await fetch('/summary');
    const data = await res.json();
    const summaryDiv = document.getElementById('summary');

    if (!data || data.success === false) {
      summaryDiv.innerHTML = "<p>❌ Failed to load summary.</p>";
      return;
    }

    const {
      total_expense,
      contributions,
      net_contributions,
      settlements_table,
      settlements_statements
    } = data;

    let html = `
      <h3>💰 Total Trip Expense: ₹${total_expense.toFixed(2)}</h3>

      <h3>📊 Net Contributions</h3>
      <table>
        <thead><tr><th>Person</th><th>Paid</th><th>Should Pay</th><th>Net Balance</th></tr></thead>
        <tbody>
          ${net_contributions.map(row => `
            <tr>
              <td>${row.person}</td>
              <td>₹${row.paid.toFixed(2)}</td>
              <td>₹${row.should_pay.toFixed(2)}</td>
              <td>${row.net_balance >= 0 ? "+" : "-"}₹${Math.abs(row.net_balance).toFixed(2)} ${row.net_balance > 0 ? "(gets back)" : "(owes)"}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>

      <h3>🔁 Correct Settlements</h3>
      <table>
        <thead><tr><th>Who Pays</th><th>To Whom</th><th>Amount</th></tr></thead>
        <tbody>
          ${settlements_table.map(s => `
            <tr>
              <td>${s.who_pays}</td>
              <td>${s.to_whom}</td>
              <td>₹${s.amount.toFixed(2)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>

      <h3>✅ Final Human-Readable Statements</h3>
      <ul>
        ${settlements_statements.length ? settlements_statements.map(s => `<li>${s}</li>`).join('') : "<li>✅ Everyone is settled up!</li>"}
      </ul>
    `;

    summaryDiv.innerHTML = html;

  } catch (err) {
    console.error("Error loading summary:", err);
    showMessage("❌ Failed to load summary.", "error");
  }
}


// 📢 Show success/error message
function showMessage(message, type) {
  const msgDiv = document.createElement('div');
  msgDiv.className = `message ${type}`;
  msgDiv.textContent = message;
  document.body.appendChild(msgDiv);
  setTimeout(() => msgDiv.remove(), 3000);
}

// 📦 Initialize on page load
window.addEventListener('DOMContentLoaded', loadUsers);
