from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import sqlite3
import os

app = Flask(__name__)

DATABASE = "assign2.db"
UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Create uploads folder if it does not exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# --------------------------------------------------
# Database setup
# --------------------------------------------------

def init_db():
    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            firstname TEXT NOT NULL,
            lastname TEXT NOT NULL,
            email TEXT NOT NULL,
            address TEXT NOT NULL,
            filename TEXT,
            word_count INTEGER
        )
    """)

    conn.commit()
    conn.close()


# --------------------------------------------------
# Home / Registration page
# --------------------------------------------------

@app.route("/")
def home():
    return redirect(url_for("register"))


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        firstname = request.form["firstname"]
        lastname = request.form["lastname"]
        email = request.form["email"]
        address = request.form["address"]

        conn = sqlite3.connect(DATABASE)

        try:
            conn.execute("""
                INSERT INTO users
                (username, password, firstname, lastname, email, address)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                username,
                password,
                firstname,
                lastname,
                email,
                address
            ))

            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()

            return """
            <h2>Username already exists.</h2>
            <a href="/register">Go back to registration</a>
            """

        conn.close()

        # Redirect to profile page after registration
        return redirect(url_for("profile", username=username))

    return render_template("register.html")


# --------------------------------------------------
# Profile page
# --------------------------------------------------

@app.route("/profile/<username>")
def profile(username):

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    user = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    conn.close()

    if user is None:
        return "User not found."

    return render_template("profile.html", user=user)


# --------------------------------------------------
# Login
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row

        user = conn.execute("""
            SELECT * FROM users
            WHERE username = ? AND password = ?
        """, (username, password)).fetchone()

        conn.close()

        if user:
            return redirect(url_for("profile", username=username))

        return """
        <h2>Invalid username or password.</h2>
        <a href="/login">Try again</a>
        """

    return render_template("login.html")


# --------------------------------------------------
# File Upload
# --------------------------------------------------

@app.route("/upload/<username>", methods=["POST"])
def upload(username):

    if "file" not in request.files:
        return "No file selected."

    file = request.files["file"]

    if file.filename == "":
        return "No file selected."

    # Save uploaded file
    filename = file.filename
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    file.save(filepath)

    # Calculate word count
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    word_count = len(text.split())

    # Store filename and word count in database
    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        UPDATE users
        SET filename = ?, word_count = ?
        WHERE username = ?
    """, (filename, word_count, username))

    conn.commit()
    conn.close()

    return redirect(url_for("profile", username=username))


# --------------------------------------------------
# Download uploaded file
# --------------------------------------------------

@app.route("/download/<filename>")
def download(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
        as_attachment=True
    )


# --------------------------------------------------
# Run application
# --------------------------------------------------

if __name__ == "__main__":
    init_db()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
