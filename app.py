from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime

# ================= CONFIG =================

USE_AWS = False   # 🔴 CHANGE TO True WHEN AWS IS READY

app = Flask(__name__)
app.secret_key = "local_secret_key"

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
        return redirect(url_for("login"))

    return render_template("register.html")

# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not USE_AWS:
            user = local_users.get(email)
        else:
            user = users_table.get_item(Key={"email": email}).get("Item")

        if user and user["password"] == password:
            session["user"] = {"name": user["name"], "email": user["email"]}
            flash("Login successful")
            return redirect(url_for("dashboard"))

        flash("Invalid credentials")
        return redirect(url_for("login"))

    return render_template("login.html")

# ================= LOGOUT =================

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully")
    return redirect(url_for("index"))

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

# ================= DEPOSIT =================

@app.route("/deposit", methods=["GET", "POST"])
def deposit():
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
        return redirect(url_for("dashboard"))

    return render_template("deposit.html")

# ================= WITHDRAW =================

@app.route("/withdraw", methods=["GET", "POST"])
def withdraw():
    if "user_email" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
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
        return redirect(url_for("dashboard"))

    return render_template("withdraw.html")


# ================= TRANSFER =================

@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    if "user_email" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
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

    return render_template("transfer.html")


# ================= HISTORY =================

@app.route("/history")
def history():
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
