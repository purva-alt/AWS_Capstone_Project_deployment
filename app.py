import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "cloudbank_secret"

# ---------------- DATABASE CONNECTION ---------------- #

def get_db():
    return sqlite3.connect("bank.db")

# ---------------- CREATE TABLES ---------------- #

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        user_id INTEGER,
        balance REAL DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT,
        amount REAL,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- LOGIN REQUIRED ---------------- #

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "user_id" not in session:
            flash("Login first")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrap

# ---------------- HOME ---------------- #

@app.route("/")
def home():
    return render_template("home.html")

# ---------------- REGISTER ---------------- #

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        try:
            cur.execute("INSERT INTO users (name,email,password) VALUES (?,?,?)",
                        (name,email,password))
            user_id = cur.lastrowid

            cur.execute("INSERT INTO accounts (user_id,balance) VALUES (?,?)",
                        (user_id,0))

            conn.commit()
            flash("Registration successful!")
            return redirect(url_for("login"))

        except:
            flash("Email already registered")

        conn.close()

    return render_template("register.html")

# ---------------- LOGIN ---------------- #

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE email=? AND password=?",
                    (email,password))
        user = cur.fetchone()

        conn.close()

        if user:
            session["user_id"] = user[0]
            flash("Login successful!")
            return redirect(url_for("dashboard"))

        flash("Invalid credentials")

    return render_template("login.html")

# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out")
    return redirect(url_for("home"))

# ---------------- DASHBOARD ---------------- #

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT balance FROM accounts WHERE user_id=?",
                (session["user_id"],))
    balance = cur.fetchone()[0]

    conn.close()

    return render_template("dashboard.html", balance=balance)

# ---------------- DEPOSIT ---------------- #

@app.route("/deposit", methods=["GET","POST"])
@login_required
def deposit():
    if request.method == "POST":
        amount = float(request.form["amount"])

        conn = get_db()
        cur = conn.cursor()

        cur.execute("UPDATE accounts SET balance = balance + ? WHERE user_id=?",
                    (amount,session["user_id"]))

        cur.execute("""INSERT INTO transactions 
                       (user_id,type,amount,date) 
                       VALUES (?,?,?,?)""",
                    (session["user_id"],"Deposit",amount,str(datetime.now())))

        conn.commit()
        conn.close()

        flash("Money deposited!")
        return redirect(url_for("dashboard"))

    return render_template("deposit.html")

# ---------------- WITHDRAW ---------------- #

@app.route("/withdraw", methods=["GET","POST"])
@login_required
def withdraw():
    if request.method == "POST":
        amount = float(request.form["amount"])

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT balance FROM accounts WHERE user_id=?",
                    (session["user_id"],))
        balance = cur.fetchone()[0]

        if balance < amount:
            flash("Insufficient balance")
            return redirect(url_for("withdraw"))

        cur.execute("UPDATE accounts SET balance = balance - ? WHERE user_id=?",
                    (amount,session["user_id"]))

        cur.execute("""INSERT INTO transactions 
                       (user_id,type,amount,date) 
                       VALUES (?,?,?,?)""",
                    (session["user_id"],"Withdraw",amount,str(datetime.now())))

        conn.commit()
        conn.close()

        flash("Withdrawal successful")
        return redirect(url_for("dashboard"))

    return render_template("withdraw.html")

# ---------------- TRANSFER ---------------- #

@app.route("/transfer", methods=["GET","POST"])
@login_required
def transfer():
    if request.method == "POST":
        receiver = request.form["email"]
        amount = float(request.form["amount"])

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE email=?", (receiver,))
        receiver_user = cur.fetchone()

        if not receiver_user:
            flash("Receiver not found")
            return redirect(url_for("transfer"))

        receiver_id = receiver_user[0]

        cur.execute("SELECT balance FROM accounts WHERE user_id=?",
                    (session["user_id"],))
        balance = cur.fetchone()[0]

        if balance < amount:
            flash("Not enough balance")
            return redirect(url_for("transfer"))

        cur.execute("UPDATE accounts SET balance = balance - ? WHERE user_id=?",
                    (amount,session["user_id"]))
        cur.execute("UPDATE accounts SET balance = balance + ? WHERE user_id=?",
                    (amount,receiver_id))

        cur.execute("""INSERT INTO transactions 
                       (user_id,type,amount,date) 
                       VALUES (?,?,?,?)""",
                    (session["user_id"],f"Transfer to {receiver}",amount,str(datetime.now())))

        conn.commit()
        conn.close()

        flash("Transfer successful!")
        return redirect(url_for("dashboard"))

    return render_template("transfer.html")

# ---------------- TRANSACTIONS ---------------- #

@app.route("/transactions")
@login_required
def transactions():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT type,amount,date FROM transactions WHERE user_id=?",
                (session["user_id"],))
    data = cur.fetchall()

    conn.close()

    return render_template("transactions.html", transactions=data)

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app.run(debug=True)
