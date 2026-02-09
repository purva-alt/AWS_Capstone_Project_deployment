from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
<<<<<<< HEAD
import random

# ================= APP SETUP =================
=======

# ================= CONFIG =================

USE_AWS = False   # 🔴 CHANGE TO True WHEN AWS IS READY
>>>>>>> 93821fe (Fixed transaction history, profile data, and improved user flow)

app = Flask(__name__)
app.secret_key = "local_secret_key"

<<<<<<< HEAD
def generate_account_number():
    return "CB" + str(random.randint(1000000000, 9999999999))

# ================= LOCAL MOCK STORAGE =================

local_users = {}          # email -> user data
local_accounts = {}       # email -> balance
local_transactions = []   # list of transactions

# ================= FRAUD MONITORING =================

suspicious_alerts = []    # fraud alerts for analyst dashboard

HIGH_VALUE_THRESHOLD = 50000
RAPID_TXN_LIMIT = 3
RAPID_TIME_WINDOW = 5     # minutes

# ================= REGULATORY COMPLIANCE =================

DAILY_TRANSFER_LIMIT = 100000  # ₹1,00,000 per day

def check_compliance(email, amount):
    today = datetime.now().date()

    daily_total = sum(
        t["amount"]
        for t in local_transactions
        if t["email"] == email
        and t["type"] == "SENT"
        and t["time"].date() == today
    )

    if daily_total + amount > DAILY_TRANSFER_LIMIT:
        return False

    return True

# ================= FRAUD DETECTION =================

def detect_fraud(email, amount):
    now = datetime.now()

    # Rule 1: High-value transaction
    if amount >= HIGH_VALUE_THRESHOLD:
        suspicious_alerts.append({
            "email": email,
            "reason": "High value transaction",
            "amount": amount,
            "time": now
        })

    # Rule 2: Rapid transactions
    recent_txns = [
        t for t in local_transactions
        if t["email"] == email
        and t["type"] == "SENT"
        and (now - t["time"]).seconds <= RAPID_TIME_WINDOW * 60
    ]

    if len(recent_txns) >= RAPID_TXN_LIMIT:
        suspicious_alerts.append({
            "email": email,
            "reason": "Multiple rapid transfers",
            "amount": amount,
            "time": now
        })

    # Rule 3: Near daily limit
    today = now.date()
    daily_total = sum(
        t["amount"]
        for t in local_transactions
        if t["email"] == email
        and t["type"] == "SENT"
        and t["time"].date() == today
    )

    if daily_total >= 0.9 * DAILY_TRANSFER_LIMIT:
        suspicious_alerts.append({
            "email": email,
            "reason": "Near daily regulatory limit",
            "amount": daily_total,
            "time": now
        })

=======
# ================= LOCAL MOCK STORAGE =================
# (Used when AWS is NOT available)

local_users = {}          # email -> user data
local_accounts = {}       # email -> balance
local_transactions = []   # list of transactions

# ================= AWS SETUP (ONLY IF ENABLED) =================

if USE_AWS:
    import boto3
    from decimal import Decimal
    from boto3.dynamodb.conditions import Key

    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    users_table = dynamodb.Table("Users")
    accounts_table = dynamodb.Table("Accounts")
    transactions_table = dynamodb.Table("Transactions")

>>>>>>> 93821fe (Fixed transaction history, profile data, and improved user flow)
# ================= PUBLIC PAGES =================

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
<<<<<<< HEAD
        email = request.form.get("email")

        if not email:
            flash("Email is required ❌")
            return redirect(url_for("register"))

        if email in local_users:
            flash("Account already exists ❌")
            return redirect(url_for("login"))

        account_number = generate_account_number()

        local_users[email] = {
            "first_name": request.form.get("first_name"),
            "middle_name": request.form.get("middle_name"),
            "last_name": request.form.get("last_name"),
            "email": email,
            "phone": request.form.get("phone"),
            "state": request.form.get("state"),
            "city": request.form.get("city"),
            "address": request.form.get("address"),
            "account_number": account_number,
            "password": request.form.get("password"),
            "pin": request.form.get("pin")
        }

        local_accounts[email] = 0
        flash(f"Account created successfully ✅ Account No: {account_number}")
=======
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password")

        # ---------- LOCAL MODE ----------
        if not USE_AWS:
            if email in local_users:
                flash("User already exists. Please login.")
                return redirect(url_for("login"))

            local_users[email] = {
                "name": name,
                "email": email,
                "phone": phone,
                "password": password
            }
            local_accounts[email] = 0

        # ---------- AWS MODE ----------
        else:
            if "Item" in users_table.get_item(Key={"email": email}):
                flash("User already exists. Please login.")
                return redirect(url_for("login"))

            users_table.put_item(Item={
                "email": email,
                "name": name,
                "phone": phone,
                "password": password
            })

            accounts_table.put_item(Item={
                "email": email,
                "balance": Decimal("0")
            })

        # ✅ IMPORTANT CHANGE HERE
        flash("Your account has been successfully created. Please login.")
>>>>>>> 93821fe (Fixed transaction history, profile data, and improved user flow)
        return redirect(url_for("login"))

    return render_template("register.html")

# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

<<<<<<< HEAD
        user = local_users.get(email)

        if user and user["password"] == password:
            session["user_email"] = email
            flash("Login successful ✅")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password ❌")
=======
        if not USE_AWS:
            user = local_users.get(email)
        else:
            user = users_table.get_item(Key={"email": email}).get("Item")

        if user and user["password"] == password:
            session["user"] = {"name": user["name"], "email": user["email"]}
            flash("Login successful")
            return redirect(url_for("dashboard"))

        flash("Invalid credentials")
>>>>>>> 93821fe (Fixed transaction history, profile data, and improved user flow)
        return redirect(url_for("login"))

    return render_template("login.html")

# ================= LOGOUT =================

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully")
    return redirect(url_for("index"))
<<<<<<< HEAD

# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():
    if "user_email" not in session:
        return redirect(url_for("login"))

    email = session["user_email"]
    balance = local_accounts.get(email, 0)

    return render_template("dashboard.html", balance=balance)

=======

# ================= PROFILE =================

@app.route("/profile")
def profile():
    if "user_email" not in session:
        return redirect(url_for("login"))

    email = session["user_email"]

    # LOCAL MODE (no AWS)
    if not USE_AWS:
        user = local_users[email]

    # AWS MODE
    else:
        user = users_table.get_item(
            Key={"email": email}
        )["Item"]

    return render_template("profile.html", user=user)


# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    email = session["user"]["email"]

    if not USE_AWS:
        balance = local_accounts.get(email, 0)
    else:
        balance = accounts_table.get_item(
            Key={"email": email}
        )["Item"]["balance"]

    return render_template("dashboard.html",
                           user=session["user"],
                           balance=balance)

>>>>>>> 93821fe (Fixed transaction history, profile data, and improved user flow)
# ================= DEPOSIT =================

@app.route("/deposit", methods=["GET", "POST"])
def deposit():
<<<<<<< HEAD
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
=======
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        amount = int(request.form.get("amount"))
        email = session["user"]["email"]

        if not USE_AWS:
            local_accounts[email] += amount
            local_transactions.append({
                "email": email,
                "type": "Deposit",
                "amount": amount,
                "time": datetime.now()
            })
        else:
            accounts_table.update_item(
                Key={"email": email},
                UpdateExpression="SET balance = balance + :a",
                ExpressionAttributeValues={":a": Decimal(amount)}
            )

            transactions_table.put_item(Item={
                "email": email,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "Deposit",
                "amount": Decimal(amount)
            })

        flash("Amount deposited successfully")
>>>>>>> 93821fe (Fixed transaction history, profile data, and improved user flow)
        return redirect(url_for("dashboard"))

    return render_template("deposit.html")

# ================= WITHDRAW =================

@app.route("/withdraw", methods=["GET", "POST"])
def withdraw():
    if "user_email" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
<<<<<<< HEAD
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
=======
        amount = int(request.form.get("amount"))
        email = session["user_email"]

        # -------- LOCAL MODE --------
        if not USE_AWS:
            if local_accounts[email] < amount:
                flash("Insufficient balance")
                return redirect(url_for("withdraw"))

            # deduct balance
            local_accounts[email] -= amount

            # ✅ ADD TRANSACTION ENTRY
            local_transactions.append({
                "email": email,
                "type": "Withdraw",
                "amount": amount,
                "time": datetime.now()
            })

        # -------- AWS MODE --------
        else:
            acc = accounts_table.get_item(Key={"email": email})["Item"]

            if acc["balance"] < amount:
                flash("Insufficient balance")
                return redirect(url_for("withdraw"))

            accounts_table.update_item(
                Key={"email": email},
                UpdateExpression="SET balance = balance - :a",
                ExpressionAttributeValues={":a": Decimal(amount)}
            )

            transactions_table.put_item(Item={
                "email": email,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "Withdraw",
                "amount": Decimal(amount)
            })

        flash("Amount withdrawn successfully")
>>>>>>> 93821fe (Fixed transaction history, profile data, and improved user flow)
        return redirect(url_for("dashboard"))

    return render_template("withdraw.html")


# ================= TRANSFER =================

@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    if "user_email" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
<<<<<<< HEAD
        sender_email = session["user_email"]
        sender = local_users[sender_email]

        amount = float(request.form.get("amount"))
        entered_pin = request.form.get("pin")

        # PIN check
        if entered_pin != sender["pin"]:
            flash("Incorrect PIN ❌")
            return redirect(url_for("transfer"))

        # Compliance check
        if not check_compliance(sender_email, amount):
            flash("Daily transfer limit exceeded ❌")
            return redirect(url_for("transfer"))

        # PHONE TRANSFER
        if request.form.get("receiver_phone"):
            receiver_phone = normalize_phone(request.form.get("receiver_phone"))

            # Check balance
            if local_accounts[sender_email] < amount:
                flash("Insufficient balance ❌")
                return redirect(url_for("transfer"))

            # Find receiver (if registered)
            receiver_email = None
            for email, user in local_users.items():
                if normalize_phone(user["phone"]) == receiver_phone:
                    receiver_email = email
                    break

            # Deduct from sender
            local_accounts[sender_email] -= amount

            # If receiver is registered → credit
            if receiver_email:
                local_accounts[receiver_email] += amount

                local_transactions.append({
                    "email": receiver_email,
                    "type": "RECEIVED",
                    "amount": amount,
                    "other": receiver_phone,
                    "mode": "PHONE",
                    "status": "REGISTERED",
                    "time": datetime.now()
                })

                receiver_status = "REGISTERED"
            else:
                receiver_status = "UNREGISTERED"

            # Sender transaction
            local_transactions.append({
                "email": sender_email,
                "type": "SENT",
                "amount": amount,
                "other": receiver_phone,
                "mode": "PHONE",
                "status": receiver_status,
                "time": datetime.now()
            })

            # Fraud detection
            detect_fraud(sender_email, amount)

            flash("Transaction completed successfully ✅")
            return redirect(url_for("transfer"))

        flash("Invalid transfer request ❌")
        return redirect(url_for("transfer"))
=======
        receiver = request.form.get("receiver_email")
        amount = int(request.form.get("amount"))
        sender = session["user_email"]

        # -------- LOCAL MODE --------
        if not USE_AWS:
            if receiver not in local_accounts:
                flash("Receiver not found")
                return redirect(url_for("transfer"))

            if local_accounts[sender] < amount:
                flash("Insufficient balance")
                return redirect(url_for("transfer"))

            # update balances
            local_accounts[sender] -= amount
            local_accounts[receiver] += amount

            # ✅ ADD TRANSACTION ENTRY
            local_transactions.append({
                "email": sender,
                "type": "Transfer",
                "amount": amount,
                "time": datetime.now()
            })

        # -------- AWS MODE --------
        else:
            sender_acc = accounts_table.get_item(Key={"email": sender})["Item"]

            if sender_acc["balance"] < amount:
                flash("Insufficient balance")
                return redirect(url_for("transfer"))

            accounts_table.update_item(
                Key={"email": sender},
                UpdateExpression="SET balance = balance - :a",
                ExpressionAttributeValues={":a": Decimal(amount)}
            )

            accounts_table.update_item(
                Key={"email": receiver},
                UpdateExpression="SET balance = balance + :a",
                ExpressionAttributeValues={":a": Decimal(amount)}
            )

            transactions_table.put_item(Item={
                "email": sender,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "Transfer",
                "amount": Decimal(amount)
            })

        flash("Transfer successful")
        return redirect(url_for("dashboard"))
>>>>>>> 93821fe (Fixed transaction history, profile data, and improved user flow)

    return render_template("transfer.html")


<<<<<<< HEAD
# ================= ANALYTICS =================

@app.route("/analytics_dashboard")
def analytics_dashboard():
    return render_template("analytics.html", alerts=suspicious_alerts)

=======
>>>>>>> 93821fe (Fixed transaction history, profile data, and improved user flow)
# ================= HISTORY =================

@app.route("/history")
def history():
<<<<<<< HEAD
    if "user_email" not in session:
        return redirect(url_for("login"))

    email = session["user_email"]
    transactions = [t for t in local_transactions if t["email"] == email]
    transactions.reverse()

    return render_template("history.html", transactions=transactions)

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
        flash("Profile updated successfully ✅")

    return render_template("profile.html", user=user)
=======
    if "user" not in session:
        return redirect(url_for("login"))

    email = session["user"]["email"]

    if not USE_AWS:
        txns = [t for t in local_transactions if t["email"] == email]
    else:
        response = transactions_table.query(
            KeyConditionExpression=Key("email").eq(email)
        )
        txns = response.get("Items", [])

    return render_template("history.html", transactions=txns)

>>>>>>> 93821fe (Fixed transaction history, profile data, and improved user flow)

# ================= ADMIN / ANALYTICS =================

@app.route("/admin")
def admin():
    return render_template("admin.html")

@app.route("/analytics")
def analytics():
    return render_template("analytics.html")

# ================= RUN LOCALLY =================

if __name__ == "__main__":
    app.run(debug=True)
