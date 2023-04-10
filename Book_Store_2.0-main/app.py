import os

from cs50 import SQL
from flask import Flask, flash, redirect, jsonify, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup

# Configure application
app = Flask(__name__)
app.debug = True

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///bookstore.db")



# session.clear()
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # if "page_no" not in session:
    #     session["page_no"] = 6
    if "first" not in session: 
        session["first"] = 1
    if "last" not in session: 
        session["last"] = 4

    if "prev" not in session: 
        session["prev"] = 0
    if "next" not in session: 
        session["next"] = 1

    if "username" not in session:
        session["username"] = ""

    row=db.execute("SELECT * FROM users WHERE id=?", session["user_id"])
    books=db.execute("SELECT * FROM books WHERE id >= ? and id <= ?", session["first"], session["last"])
    session["username"] = row[0]["username"]
    return render_template("index.html", username=row[0]["username"], books=books, prev=session["prev"], next=session["next"])


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("login.html", error="User name or password incorrect")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", error="User name or password incorrect")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("login.html", error="User name or password incorrect")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html", error="")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    username = request.form.get("username")
    password = request.form.get("password")
    confirmation = request.form.get("confirmation")

    if(request.method == "POST"):
        rows = db.execute("SELECT * FROM users WHERE username =?;", username)
        if(len(rows) == 1):
            return apology("Username Already Taken")

        if(password != confirmation):
            return apology("Passwords Don't Match")

        if(not username or not password or not confirmation):
            return apology("Empty Fields")

        hash = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (username,hash) VALUES (?,?);", username , hash)

        row = db.execute("SELECT * FROM users WHERE username=?", username)
        session["user_id"] = row[0]["id"]
        return redirect("/")

    return render_template("register.html")



@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/book")
@login_required
def book():
    id = request.args.get("id")
    row = db.execute("SELECT * FROM books WHERE id = ?", id)
    book = row[0]
    return render_template("booklayout.html", book=book, username=session["username"])


@app.route("/prev")
@login_required
def prev():
    row=db.execute("SELECT COUNT(id) FROM books")
    count=row[0]["COUNT(id)"]
    session["prev"] = 0
    if session["first"] > 4:
        session["first"] -= 4
        session["last"] -=4
        session["next"] = 1
    if session["first"] > 4:
        session["prev"] = 1
    return redirect("/")

@app.route("/next")
@login_required
def next():
    row=db.execute("SELECT COUNT(id) FROM books")
    count=row[0]["COUNT(id)"]
    session["next"] = 0
    if session["last"] < count:
        session["first"] += 4
        session["last"] += 4
        session["prev"] = 1
    if session["last"] < count:
        session["next"] = 1
        
    return redirect("/")

@app.route("/reset")
@login_required
def reset():
    id=session["user_id"]
    session.clear()
    session["user_id"]=id
    return redirect("/")

@app.route("/search", methods=["GET","POST"])
@login_required
def search():
    if (request.method == "GET"):
        q = request.args.get("q")
        if q:
            books = db.execute("SELECT * FROM books WHERE name LIKE ? LIMIT 4;", "%" + q + "%")
        else:
            books = []
        return jsonify(books)

    if (request.method == "POST"):
        q = request.form.get("q")
        book = db.execute("SELECT * FROM books WHERE name LIKE ?" , q)
        if (len(book) != 0):
            return render_template("booklayout.html", book=book[0], username=session["username"])
    return redirect("/")