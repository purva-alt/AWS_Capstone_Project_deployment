from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
import random

# ================= APP SETUP =================

app = Flask(__name__)
app.secret_key = "aws_secret_key_change_later"

# ================= UTILITIES =================

def generate_account_number():
    return "CB" + str(random.randint(1000000000, 9999999999))

def normalize_phone(phone):
    if not phone:
        return ""
    phone = phone.replace(" ", "")
    if phone.startswith("+91"):
        phone = phone[3:]
    if phone.startswith("0"):
        phone = phone[1:]
    return phone

# ================= LOCAL MOCK STORAGE =================
# (AWS-safe: no DB dependency)

local_users = {}          # email → user data
local_accounts = {}       # email → balance
local_transactions = []   # all transactions
suspicious_alerts = []    # fraud alerts

# ================= FRAUD + COMPLIANCE CONFIG =================

HIGH_VALUE_THRESHOLD = 50000
RAPID_TXN_LIMIT = 3
RAPID_TIME_WINDOW = 5  # minutes
DAILY_TRANSFER_LIMIT = 100000  # ₹1,00,000

# ================= COMPLIANCE =================

def compliance_status(email, amount):
    today = datetime.now().date()
    daily_total = sum(
        t["amount"] for t in local_transactions
        if t["email"] == email
        and t["type"] == "SENT"
        and t["time"].date() == today
    )

    usage = (daily_total + amount) / DAILY_TRANSFER_LIMIT

    if usage >= 1:
        return "BLOCK"
    elif usage >= 0.9:
        return "CRITICAL"
    elif usage >= 0.8:
        return "WARNING"
    return "OK"

# ================= FRAUD DETECTION =================

def detect_fraud(email, amount):
    now = datetime.now()

    if amount >= HIGH_VALUE_THRESHOLD:
        suspicious_alerts.append({
            "email": email,
            "reason": "High value transaction",
            "amount": amount,
            "time": now
        })

    recent = [
        t for t in local_transactions
        if t["email"] == email
        and t["type"] == "SENT"
        and (now - t["time"]).seconds <= RAPID_TIME_WINDOW * 60
    ]

    if len(recent) >= RAPID_TXN_LIMIT:
        suspicious_alerts.append({
            "email": email,
            "reason": "Multiple rapid transfers",
            "amount": amount,
            "time": now
        })

# ================= PUBLIC ROUTES =================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

# ================= REGISTER =================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")

        if not email:
            flash("Email required ❌")
            return redirect(url_for("register"))

        if email in local_users:
            flash("Account already exists ❌")
            return redirect(url_for("login"))

        acc_no = generate_account_number()

        local_users[email] = {
            "first_name": request.form.get("first_name"),
            "middle_name": request.form.get("middle_name"),
            "last_name": request.form.get("last_name"),
            "email": email,
            "phone": request.form.get("phone"),
            "state": request.form.get("state"),
            "city": request.form.get("city"),
            "address": request.form.get("address"),
            "account_number": acc_no,
            "password": request.form.get("password"),
            "pin": request.form.get("pin")
        }

        local_accounts[email] = 0
        flash(f"Account created ✅ Account No: {acc_no}")
        return redirect(url_for("login"))

    return render_template("register.html")

# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = local_users.get(email)

        if user and user["password"] == password:
            session["user_email"] = email
            flash("Login successful ✅")
            return redirect(url_for("dashboard"))

        flash("Invalid credentials ❌")
        return redirect(url_for("login"))

    return render_template("login.html")

# ================= LOGOUT =================

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully")
    return redirect(url_for("index"))

# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():
    if "user_email" not in session:
        return redirect(url_for("login"))

    email = session["user_email"]
    balance = local_accounts.get(email, 0)
    return render_template("dashboard.html", balance=balance)

# ================= DEPOSIT =================

@app.route("/deposit", methods=["GET", "POST"])
def deposit():
    if "user_email" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        email = session["user_email"]
        amount = float(request.form["amount"])

        local_accounts[email] += amount
        local_transactions.append({
            "email": email,
            "type": "DEPOSIT",
            "amount": amount,
            "time": datetime.now()
        })

        flash("Deposit successful ✅")
        return redirect(url_for("dashboard"))

    return render_template("deposit.html")

# ================= WITHDRAW =================

@app.route("/withdraw", methods=["GET", "POST"])
def withdraw():
    if "user_email" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        email = session["user_email"]
        amount = float(request.form["amount"])

        if local_accounts[email] < amount:
            flash("Insufficient balance ❌")
            return redirect(url_for("withdraw"))

        local_accounts[email] -= amount
        local_transactions.append({
            "email": email,
            "type": "WITHDRAW",
            "amount": amount,
            "time": datetime.now()
        })

        flash("Withdraw successful ✅")
        return redirect(url_for("dashboard"))

    return render_template("withdraw.html")

# ================= TRANSFER =================

@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    if "user_email" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        sender_email = session["user_email"]
        sender = local_users[sender_email]

        amount = float(request.form.get("amount"))
        entered_pin = request.form.get("pin")

        if entered_pin != sender["pin"]:
            flash("Incorrect PIN ❌")
            return redirect(url_for("transfer"))

        status = compliance_status(sender_email, amount)
        if status == "BLOCK":
            flash("Daily limit exceeded ❌")
            return redirect(url_for("transfer"))

        receiver_phone = normalize_phone(request.form.get("receiver_phone"))

        if local_accounts[sender_email] < amount:
            flash("Insufficient balance ❌")
            return redirect(url_for("transfer"))

        local_accounts[sender_email] -= amount

        receiver_email = None
        for email, user in local_users.items():
            if normalize_phone(user["phone"]) == receiver_phone:
                receiver_email = email
                local_accounts[email] += amount
                break

        local_transactions.append({
            "email": sender_email,
            "type": "SENT",
            "amount": amount,
            "other": receiver_phone,
            "time": datetime.now()
        })

        if receiver_email:
            local_transactions.append({
                "email": receiver_email,
                "type": "RECEIVED",
                "amount": amount,
                "other": sender_email,
                "time": datetime.now()
            })

        detect_fraud(sender_email, amount)
        flash("Transfer successful ✅")
        return redirect(url_for("transfer"))

    return render_template("transfer.html")

# ================= HISTORY =================

@app.route("/history")
def history():
    if "user_email" not in session:
        return redirect(url_for("login"))

    email = session["user_email"]
    txns = [t for t in local_transactions if t["email"] == email]
    txns.reverse()
    return render_template("history.html", transactions=txns)

# ================= PROFILE =================

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_email" not in session:
        return redirect(url_for("login"))

    email = session["user_email"]
    user = local_users[email]

    if request.method == "POST":
        user["first_name"] = request.form.get("first_name")
        user["last_name"] = request.form.get("last_name")
        user["phone"] = request.form.get("phone")
        user["address"] = request.form.get("address")
        flash("Profile updated ✅")

    return render_template("profile.html", user=user)

# ================= ANALYTICS =================

@app.route("/analytics_dashboard")
def analytics_dashboard():
    return render_template("analytics.html", alerts=suspicious_alerts)

@app.route("/generate_report", methods=["GET", "POST"])
def generate_report():
    if "user_email" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        metrics = request.form.getlist("metrics")
        start = datetime.strptime(request.form["start_date"], "%Y-%m-%d")
        end = datetime.strptime(request.form["end_date"], "%Y-%m-%d")

        filtered = [t for t in local_transactions if start <= t["time"] <= end]
        report = {"generated_on": datetime.now()}

        if "users" in metrics:
            report["total_users"] = len(local_users)
        if "deposits" in metrics:
            report["total_deposits"] = sum(t["amount"] for t in filtered if t["type"] == "DEPOSIT")
        if "withdrawals" in metrics:
            report["total_withdrawals"] = sum(t["amount"] for t in filtered if t["type"] == "WITHDRAW")
        if "transfers" in metrics:
            report["total_transfers"] = sum(t["amount"] for t in filtered if t["type"] == "SENT")

        return render_template("report.html", report=report)

    return render_template("report_form.html")

# ================= RUN =================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
