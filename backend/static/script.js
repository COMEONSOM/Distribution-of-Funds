// ============================
// 🌐 BASE URL (Auto for Local + Render)
// ============================
const API_BASE = window.location.origin;

// ============================
// 🌟 GLOBAL VARIABLES & CACHES
// ============================
let users = new Set();

const authModal = document.getElementById('authModal');
const toastContainer = document.getElementById('toast-container');
const summaryDiv = document.getElementById('summary');
const paidByDropdown = document.getElementById('paid_by');
const userListContainer = document.getElementById('userList');

// ============================
// 🔁 AUTH MODAL CONTROLS
// ============================
function openAuthModal() {
  authModal.classList.remove('hidden');
  showStep('welcome');
}

function closeAuthModal() {
  authModal.classList.add('hidden');
}

function modalBackgroundClick(event) {
  if (event.target.classList.contains('modal')) {
    closeAuthModal();
  }
}

document.addEventListener('keydown', (e) => {
  if (e.key === "Escape" && !authModal.classList.contains('hidden')) {
    closeAuthModal();
  }
});

function showStep(step) {
  document.querySelectorAll('.step, #authStep').forEach(div => {
    div.classList.add('hidden');
    div.classList.remove('active');
  });

  const target = step === 'welcome' ? document.getElementById('authStep') : document.getElementById(step + 'Step');
  if (target) {
    target.classList.remove('hidden');
    target.classList.add('active');
  }
}

// ============================
// 🔐 REGISTER USER
// ============================
async function registerUser() {
  const name = document.getElementById("registerName").value.trim();
  const email = document.getElementById("registerEmail").value.trim();
  const password = document.getElementById("registerPassword").value.trim();

  if (!name || !email || !password) {
    return showToast("⚠ Please fill in all fields", "error");
  }

  try {
    const res = await fetch(`${API_BASE}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ name, email, password })
    });

    const result = await res.json();
    if (!res.ok || !result.success) {
      return showToast(`❌ Registration failed: ${result.error || res.status}`, "error");
    }

    showToast("✅ Registration successful! Please login.", "success");
    showStep('login');

  } catch (err) {
    console.error("Registration Error:", err);
    showToast("❌ Network error during registration.", "error");
  }
}

// ============================
// 🔓 LOGIN USER
// ============================
async function loginUser() {
  const email = document.getElementById("loginEmail").value.trim();
  const password = document.getElementById("loginPassword").value.trim();
  const loginBtn = document.getElementById("loginBtn");

  if (!email || !password) {
    return showToast("⚠ Enter email and password", "error");
  }

  loginBtn.disabled = true;
  loginBtn.textContent = "Logging in...";

  try {
    const res = await fetch(`${API_BASE}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email, password })
    });

    const result = await res.json();
    loginBtn.disabled = false;
    loginBtn.textContent = "Login";

    if (!res.ok || !result.success) {
      return showToast(`❌ Login failed: ${result.error || res.status}`, "error");
    }

    showToast("✅ Logged in successfully!", "success");
    closeAuthModal();
    await loadUsers();
    await loadSummary();

  } catch (err) {
    loginBtn.disabled = false;
    loginBtn.textContent = "Login";
    console.error("Login Error:", err);
    showToast("❌ Network error during login.", "error");
  }
}

// ============================
// 🔑 FORGOT PASSWORD
// ============================
async function forgotPassword() {
  const email = document.getElementById("forgotEmail").value.trim();

  if (!email) {
    return showToast("⚠ Enter your email", "error");
  }

  try {
    const res = await fetch(`${API_BASE}/forgot_password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email })
    });

    const result = await res.json();
    if (!res.ok || !result.success) {
      return showToast(`❌ Request failed: ${result.error || res.status}`, "error");
    }

    showToast("📧 Reset link sent to your email.", "success");

  } catch (err) {
    console.error("Forgot Password Error:", err);
    showToast("❌ Network error during reset request.", "error");
  }
}

// ============================
// 🚪 LOGOUT USER
// ============================
async function logoutUser() {
  try {
    const res = await fetch(`${API_BASE}/logout`, {
      method: "POST",
      credentials: "include"
    });

    const result = await res.json();
    if (!res.ok || !result.success) {
      return showToast("❌ Logout failed.", "error");
    }

    users.clear();
    summaryDiv.innerHTML = "";
    showToast("👋 Logged out successfully!", "success");
    openAuthModal();

  } catch (err) {
    console.error("Logout Error:", err);
    showToast("❌ Network error during logout.", "error");
  }
}

// ============================
// 👥 USER MANAGEMENT
// ============================
async function addUser() {
  const nameInput = document.getElementById('newUserName');
  const name = nameInput.value.trim();

  if (!name || users.has(name)) {
    return showToast("⚠ Enter a unique name.", "error");
  }

  try {
    const res = await fetch(`${API_BASE}/add_user`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ name })
    });

    const result = await res.json();
    if (!res.ok || !result.success) throw new Error(result.error || res.status);

    users.add(name);
    updatePaidByDropdown();
    renderUserList();
    nameInput.value = "";
    showToast("✅ User added!", "success");

  } catch (err) {
    console.error("Add User Error:", err);
    showToast(`❌ Error adding user: ${err.message}`, "error");
  }
}

async function loadUsers() {
  try {
    const res = await fetch(`${API_BASE}/users`, { credentials: "include" });

    if (res.status === 401) {
      openAuthModal();
      return showToast("⚠ Session expired. Please login again.", "error");
    }

    const data = await res.json();
    if (!res.ok || !Array.isArray(data)) throw new Error(`HTTP ${res.status}`);

    users = new Set(data.map(u => u.name));
    updatePaidByDropdown();
    renderUserList();

  } catch (err) {
    console.error("Load Users Error:", err);
    showToast(`❌ Could not load users: ${err.message}`, "error");
  }
}

function updatePaidByDropdown() {
  paidByDropdown.innerHTML = '<option value="">Who Paid?</option>';
  users.forEach(name => {
    const option = document.createElement('option');
    option.value = name;
    option.textContent = name;
    paidByDropdown.appendChild(option);
  });
}

function renderUserList() {
  userListContainer.innerHTML = "";
  users.forEach(name => {
    const div = document.createElement('div');
    div.classList.add('user-row');
    div.innerHTML = `
      <label>${name}</label>
      <input type="number" class="owed-input" data-username="${name}" placeholder="Amount owed by ${name}" step="0.01" required>
    `;
    userListContainer.appendChild(div);
  });
}

// ============================
// 💾 ADD EXPENSE
// ============================
document.getElementById('expenseForm').addEventListener('submit', async function (e) {
  e.preventDefault();

  const title = this.title.value.trim();
  const location = this.location.value.trim();
  const amount = parseFloat(this.amount.value.trim());
  const paidBy = this.paid_by.value.trim();

  if (!title || !location || isNaN(amount) || !paidBy || users.size === 0) {
    return showToast("⚠ Fill all fields & add users.", "error");
  }

  const distribution = {};
  let valid = true;

  document.querySelectorAll('.owed-input').forEach(input => {
    const user = input.dataset.username;
    const owed = parseFloat(input.value);
    if (isNaN(owed)) valid = false;
    distribution[user] = owed || 0;
  });

  const totalOwed = Object.values(distribution).reduce((sum, val) => sum + val, 0);
  if (Math.abs(totalOwed - amount) > 0.01) {
    return showToast(`⚠ Total owed (${totalOwed}) != Total amount (${amount})`, "error");
  }

  if (!valid) {
    return showToast("⚠ Enter valid owed amounts.", "error");
  }

  try {
    const res = await fetch(`${API_BASE}/add_expense`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ title, location, amount, paid_by: paidBy, distribution })
    });

    const result = await res.json();
    if (!res.ok || !result.success) throw new Error(result.error || res.status);

    showToast("✅ Expense saved!", "success");
    this.reset();
    updatePaidByDropdown();
    renderUserList();

  } catch (err) {
    console.error("Add Expense Error:", err);
    showToast(`❌ Failed to save expense: ${err.message}`, "error");
  }
});

// ============================
// 📊 LOAD SUMMARY
// ============================
async function loadSummary() {
  try {
    const res = await fetch(`${API_BASE}/summary`, { credentials: "include" });

    if (res.status === 401) {
      openAuthModal();
      return showToast("⚠ Session expired. Please login again.", "error");
    }

    const data = await res.json();
    if (!res.ok || data.success === false) {
      summaryDiv.innerHTML = "<p>❌ Failed to load summary.</p>";
      return;
    }

    summaryDiv.innerHTML = renderSummaryHTML(data);

  } catch (err) {
    console.error("Load Summary Error:", err);
    showToast(`❌ Could not load summary: ${err.message}`, "error");
  }
}

function renderSummaryHTML(data) {
  const { total_expense, net_contributions, settlements_statements } = data;

  return `
    <h3>💰 Total: ₹${total_expense.toFixed(2)}</h3>
    <h3>📊 Contributions</h3>
    <ul>${net_contributions.map(u =>
      `<li>${u.person}: Paid ₹${u.paid.toFixed(2)}, Should Pay ₹${u.should_pay.toFixed(2)}, Net: ₹${u.net_balance.toFixed(2)}</li>`).join('')}</ul>
    <h3>🔁 Settlements</h3>
    <ul>${settlements_statements.map(s => `<li>${s}</li>`).join('')}</ul>
  `;
}

// ============================
// 🗑️ DELETE HISTORY
// ============================
async function deleteHistory() {
  if (!confirm("⚠️ Are you sure? This will permanently delete all your expenses.")) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/delete_history`, {
      method: "POST",
      credentials: "include",
    });

    const result = await res.json();
    if (!res.ok || !result.success) {
      return showToast(`❌ Delete failed: ${result.error || res.status}`, "error");
    }

    showToast("🗑️ All expense history deleted.", "success");
    summaryDiv.innerHTML = "<p>🗑️ No expenses found.</p>";

    users.clear();
    updatePaidByDropdown();
    renderUserList();

  } catch (err) {
    console.error("Delete History Error:", err);
    showToast("❌ Network or server error during delete.", "error");
  }
}

// ============================
// 🔔 TOAST SYSTEM
// ============================
function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;

  toastContainer.appendChild(toast);

  if (toastContainer.children.length > 5) {
    toastContainer.removeChild(toastContainer.firstChild);
  }

  setTimeout(() => toast.remove(), 4000);
}
