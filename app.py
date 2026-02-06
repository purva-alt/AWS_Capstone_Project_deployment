import bcrypt
import boto3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from functools import wraps
from decimal import Decimal

app = Flask(__name__)
app.secret_key = "cloudbank_secret"

AWS_REGION = "us-east-1"

# ================= AWS CONNECTION =================

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
sns = boto3.client("sns", region_name=AWS_REGION)

users_table = dynamodb.Table("Users")
accounts_table = dynamodb.Table("Accounts")
transactions_table = dynamodb.Table("Transactions")

SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:686255943052:AWS_PROJECT_DEPLOYMENT"

# ================= HELPERS =================

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrap


def send_alert(message):
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject="Cloud Bank Notification"
        )
    except Exception as e:
        print("SNS ERROR:", e)


# ================= HOME =================

@app.route("/")
def home():
    return render_template("index.html")

# ================= REGISTER =================

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":

        email = request.form["email"]

        if "Item" in users_table.get_item(Key={"email": email}):
            flash("Account already exists. Please login.")
            return redirect(url_for("login"))

        hashed = bcrypt.hashpw(
            request.form["password"].encode(),
            bcrypt.gensalt()
        ).decode()

        users_table.put_item(Item={
            "email": email,
            "first_name": request.form["first_name"],
            "last_name": request.form["last_name"],
            "dob": request.form["dob"],
            "account_number": request.form["account_number"],
            "address": request.form["address"],
            "phone": request.form["phone"],
            "password": hashed
        })

        accounts_table.put_item(Item={
            "email": email,
            "balance": Decimal("0")
        })

        send_alert(f"New Cloud Bank account created: {email}")

        flash("Account created successfully!")
        return redirect(url_for("login"))

    return render_template("register.html")

# ================= LOGIN =================

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        response = users_table.get_item(Key={"email": email})
        user = response.get("Item")

        if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
            session["user_id"] = email
            return redirect(url_for("dashboard"))

        flash("Invalid credentials")

    return render_template("login.html")

# ================= LOGOUT =================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ================= DASHBOARD =================

@app.route("/dashboard")
@login_required
def dashboard():
    acc = accounts_table.get_item(Key={"email": session["user_id"]})
    balance = acc["Item"]["balance"]

    return render_template("dashboard.html", balance=balance)

# ================= PROFILE =================

@app.route("/profile")
@login_required
def profile():
    user = users_table.get_item(Key={"email": session["user_id"]})["Item"]
    return render_template("profile.html", user=user)

# ================= DEPOSIT =================

@app.route("/deposit", methods=["GET","POST"])
@login_required
def deposit():
    if request.method == "POST":

        amount = Decimal(request.form["amount"])

        accounts_table.update_item(
            Key={"email": session["user_id"]},
            UpdateExpression="SET balance = balance + :a",
            ExpressionAttributeValues={":a": amount}
        )

        transactions_table.put_item(Item={
            "email": session["user_id"],
            "timestamp": str(datetime.utcnow()),
            "type": "Deposit",
            "amount": amount
        })

        send_alert(f"Deposit of ₹{amount} to {session['user_id']}")

        return redirect(url_for("dashboard"))

    return render_template("deposit.html")

# ================= WITHDRAW =================

@app.route("/withdraw", methods=["GET","POST"])
@login_required
def withdraw():
    if request.method == "POST":

        amount = Decimal(request.form["amount"])

        acc = accounts_table.get_item(Key={"email": session["user_id"]})["Item"]

        if acc["balance"] < amount:
            flash("Insufficient balance")
            return redirect(url_for("withdraw"))

        accounts_table.update_item(
            Key={"email": session["user_id"]},
            UpdateExpression="SET balance = balance - :a",
            ExpressionAttributeValues={":a": amount}
        )

        transactions_table.put_item(Item={
            "email": session["user_id"],
            "timestamp": str(datetime.utcnow()),
            "type": "Withdraw",
            "amount": amount
        })

        send_alert(f"Withdraw of ₹{amount} from {session['user_id']}")

        return redirect(url_for("dashboard"))

    return render_template("withdraw.html")

# ================= TRANSFER =================

@app.route("/transfer", methods=["GET","POST"])
@login_required
def transfer():
    if request.method == "POST":

        amount = Decimal(request.form["amount"])

        acc = accounts_table.get_item(Key={"email": session["user_id"]})["Item"]

        if acc["balance"] < amount:
            flash("Insufficient balance")
            return redirect(url_for("transfer"))

        accounts_table.update_item(
            Key={"email": session["user_id"]},
            UpdateExpression="SET balance = balance - :a",
            ExpressionAttributeValues={":a": amount}
        )

        transactions_table.put_item(Item={
            "email": session["user_id"],
            "timestamp": str(datetime.utcnow()),
            "type": "Transfer",
            "amount": amount
        })

        send_alert(f"Transfer of ₹{amount} from {session['user_id']}")

        return redirect(url_for("dashboard"))

    return render_template("transfer.html")

# ================= HISTORY =================

@app.route("/history")
@login_required
def history():

    response = transactions_table.scan()

    user_tx = [
        t for t in response["Items"]
        if t["email"] == session["user_id"]
    ]

    user_tx.sort(key=lambda x: x["timestamp"], reverse=True)

    return render_template("history.html", transactions=user_tx)

# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)

