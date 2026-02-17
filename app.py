from flask import Flask, render_template, request, redirect, url_for, session
from database import get_db, init_db
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

init_db()

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        student_id = request.form["student_id"]
        username = request.form["username"]
        faculty = request.form["faculty"]
        password = request.form["password"]

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (student_id, username, faculty, password) VALUES (?, ?, ?, ?)",
                (student_id, username, faculty, password)
            )
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return render_template("register.html", error="Username or Student ID already exists!")
    return render_template("register.html")

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session["admin"] = True
            session["student_id"] = user["student_id"]
            session["username"] = user["username"]
            session["faculty"] = user["faculty"]
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    total = conn.execute("SELECT COUNT(*) AS cnt FROM students").fetchone()["cnt"]
    conn.close()
    return render_template(
        "dashboard.html",
        total=total,
        student_id=session["student_id"],
        username=session["username"],
        faculty=session["faculty"]
    )

@app.route("/students")
def students():
    if "admin" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search", "")
    conn = get_db()
    if search:
        rows = conn.execute(
            """SELECT * FROM students
               WHERE student_id LIKE ? OR name LIKE ? OR roll LIKE ? OR department LIKE ? OR course LIKE ?""",
            (f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%")
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM students ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("students.html", students=rows, search=search)

@app.route("/add", methods=["GET", "POST"])
def add_student():
    if "admin" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        student_id = session["student_id"]
        name = request.form["name"]
        roll = request.form["roll"]
        course = request.form["course"]
        department = request.form["department"]

        conn = get_db()
        conn.execute(
            "INSERT INTO students (student_id, name, department, roll, course) VALUES (?, ?, ?, ?, ?)",
            (student_id, name, department, roll, course)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("students"))

    return render_template("add_students.html")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    if "admin" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id=?", (id,)).fetchone()

    if request.method == "POST":
        conn.execute(
            "UPDATE students SET student_id=?, name=?, department=?, roll=?, course=? WHERE id=?",
            (
                session["student_id"],
                request.form["name"],
                request.form["department"],
                request.form["roll"],
                request.form["course"],
                id
            )
        )
        conn.commit()
        conn.close()
        return redirect(url_for("students"))

    conn.close()
    return render_template("edit_student.html", student=student)

@app.route("/delete/<int:id>")
def delete_student(id):
    if "admin" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute("DELETE FROM students WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("students"))

if __name__ == "__main__":
    app.run(debug=True)