from flask import Flask, render_template, request, session, redirect
from flask_wtf.csrf import CSRFProtect

import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

csrf = CSRFProtect(app)

def init_db():

    conn = sqlite3.connect("users.db")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tool_name TEXT NOT NULL,
            topic TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Admin role column for existing users table
    columns = conn.execute("PRAGMA table_info(users)").fetchall()

    column_names = [column[1] for column in columns]

    if "is_admin" not in column_names:
        conn.execute(
            "ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0"
        )
    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/script-generator")
def script_generator():
    return render_template("script_generator.html")


@app.route("/title-generator")
def title_generator():
    return render_template("title_generator.html")


@app.route("/description-generator")
def description_generator():
    return render_template("description_generator.html")


@app.route("/tags-generator")
def tags_generator():
    return render_template("tags_generator.html")


@app.route("/shorts-hook-generator")
def shorts_hook_generator():
    return render_template("shorts_hook_generator.html")


@app.route("/thumbnail-generator")
def thumbnail_generator():
    return render_template("thumbnail_generator.html")


@app.route("/blog-generator")
def blog_generator():
    return render_template("blog_generator.html")


@app.route("/social-caption-generator")
def social_caption_generator():
    return render_template("social_caption_generator.html")


@app.route("/ai-tools")
def ai_tools():
    return render_template("ai_tools.html")


@app.route("/pricing")
def pricing():
    return render_template("pricing.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            return render_template(
                "contact.html",
                error="Please fill in all fields."
            )

        conn = sqlite3.connect("users.db")

        conn.execute(
            """
            INSERT INTO contact_messages (name, email, message)
            VALUES (?, ?, ?)
            """,
            (name, email, message)
        )

        conn.commit()
        conn.close()

        return render_template(
            "contact.html",
            success="Thank you! Your message has been received."
        )

    return render_template("contact.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            return "Please fill in all required fields."

        if password != confirm_password:
            return "Passwords do not match."

        password_hash = generate_password_hash(password)

        try:

            conn = sqlite3.connect("users.db")

            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password_hash)
            )

            conn.commit()
            conn.close()

            return "Account created successfully!"

        except sqlite3.IntegrityError:

            return "This email is already registered."

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = sqlite3.connect("users.db")
        conn.row_factory = sqlite3.Row

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user is None:
            return "Email or password is incorrect."

        if not check_password_hash(user["password"], password):
            return "Email or password is incorrect."

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]

        return redirect("/dashboard")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    return render_template(
        "dashboard.html",
        user_name=session["user_name"],
        user_email=session["user_email"]
    )

@app.route("/admin")
def admin():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    if user is None or user["is_admin"] != 1:
        conn.close()
        return "Access denied. Admin access required.", 403

    # Admin Search
    search = request.args.get("search", "").strip()

    # Users
    users = conn.execute(
        """
        SELECT id, name, email
        FROM users
        ORDER BY id DESC
        """
    ).fetchall()

    # Contact Messages
    messages = conn.execute(
        """
        SELECT *
        FROM contact_messages
        ORDER BY id DESC
        """
    ).fetchall()

    # Total History
    history_count = conn.execute(
        "SELECT COUNT(*) AS total FROM history"
    ).fetchone()["total"]

    # History Records
    if search:
        history_records = conn.execute(
            """
            SELECT
                history.id,
                history.tool_name,
                history.topic,
                history.content,
                history.created_at,
                users.name AS user_name,
                users.email AS user_email
            FROM history
            JOIN users ON history.user_id = users.id
            WHERE history.topic LIKE ?
               OR history.tool_name LIKE ?
               OR users.name LIKE ?
               OR users.email LIKE ?
            ORDER BY history.id DESC
            """,
            (
                "%" + search + "%",
                "%" + search + "%",
                "%" + search + "%",
                "%" + search + "%"
            )
        ).fetchall()

    else:
        history_records = conn.execute(
            """
            SELECT
                history.id,
                history.tool_name,
                history.topic,
                history.content,
                history.created_at,
                users.name AS user_name,
                users.email AS user_email
            FROM history
            JOIN users ON history.user_id = users.id
            ORDER BY history.id DESC
            """
        ).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        users=users,
        messages=messages,
        history_count=history_count,
        history_records=history_records,
        search=search
    )
@app.route("/admin/delete-message/<int:message_id>", methods=["POST"])
def admin_delete_message(message_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row

    user = conn.execute(
        "SELECT is_admin FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    if user is None or user["is_admin"] != 1:
        conn.close()
        return "Access denied. Admin access required.", 403

    conn.execute(
        "DELETE FROM contact_messages WHERE id = ?",
        (message_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")

@app.route("/admin/delete-user/<int:user_id>", methods=["POST"])
def admin_delete_user(user_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row

    admin = conn.execute(
        "SELECT is_admin FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    if admin is None or admin["is_admin"] != 1:
        conn.close()
        return "Access denied. Admin access required.", 403

    # Admin cannot delete their own account
    if user_id == session["user_id"]:
        conn.close()
        return "You cannot delete your own admin account.", 400

    conn.execute(
        "DELETE FROM history WHERE user_id = ?",
        (user_id,)
    )

    conn.execute(
        "DELETE FROM users WHERE id = ?",
        (user_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")

@app.route("/admin/delete-history/<int:history_id>", methods=["POST"])
def admin_delete_history(history_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row

    admin = conn.execute(
        "SELECT is_admin FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    if admin is None or admin["is_admin"] != 1:
        conn.close()
        return "Access denied. Admin access required.", 403

    conn.execute(
        "DELETE FROM history WHERE id = ?",
        (history_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


def save_history(user_id, tool_name, topic, content):

    conn = sqlite3.connect("users.db")

    conn.execute(
        """
        INSERT INTO history (user_id, tool_name, topic, content)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, tool_name, topic, content)
    )

    conn.commit()
    conn.close()


@app.route("/save-history", methods=["POST"])
def save_history_route():

    if "user_id" not in session:
        return {
            "success": False,
            "message": "Please login first."
        }

    data = request.get_json()

    if not data:
        return {
            "success": False,
            "message": "No data received."
        }

    tool_name = data.get("tool_name", "")
    topic = data.get("topic", "")
    content = data.get("content", "")

    save_history(
        session["user_id"],
        tool_name,
        topic,
        content
    )

    return {"success": True}


@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect("/login")

    search = request.args.get("search", "").strip()

    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row

    if search:

        records = conn.execute(
            """
            SELECT *
            FROM history
            WHERE user_id = ?
            AND (topic LIKE ? OR tool_name LIKE ?)
            ORDER BY id DESC
            """,
            (
                session["user_id"],
                "%" + search + "%",
                "%" + search + "%"
            )
        ).fetchall()

    else:

        records = conn.execute(
            """
            SELECT *
            FROM history
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (session["user_id"],)
        ).fetchall()

    conn.close()

    return render_template(
        "history.html",
        records=records,
        search=search
    )


@app.route("/delete-history/<int:history_id>", methods=["POST"])
def delete_history(history_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("users.db")

    conn.execute(
        """
        DELETE FROM history
        WHERE id = ? AND user_id = ?
        """,
        (history_id, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect("/history")


@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect("/login")

    return render_template(
        "profile.html",
        user_name=session["user_name"],
        user_email=session["user_email"]
    )

@app.route("/change-password", methods=["GET", "POST"])
def change_password():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        conn = sqlite3.connect("users.db")
        conn.row_factory = sqlite3.Row

        user = conn.execute(
            "SELECT password FROM users WHERE id = ?",
            (session["user_id"],)
        ).fetchone()

        if user is None:
            conn.close()
            return "User not found."

        if not check_password_hash(user["password"], current_password):
            conn.close()
            return "Current password is incorrect."

        if not new_password:
            conn.close()
            return "New password cannot be empty."

        if new_password != confirm_password:
            conn.close()
            return "New passwords do not match."

        if len(new_password) < 8:
            conn.close()
            return "New password must be at least 8 characters."

        new_password_hash = generate_password_hash(new_password)

        conn.execute(
            "UPDATE users SET password = ? WHERE id = ?",
            (new_password_hash, session["user_id"])
        )

        conn.commit()
        conn.close()

        return "Password changed successfully. Please login again."

    return render_template("change_password.html")

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


if __name__ == "__main__":

    init_db()

    app.run(debug=True)