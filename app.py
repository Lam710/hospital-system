from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, session
from functools import wraps
import sqlite3
import pandas as pd

app = Flask(__name__)
app.secret_key = "123456"


# ---------- DATABASE ----------

def get_db():
    conn = sqlite3.connect("hospital.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------- LOGIN REQUIRED ----------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        stored_password = "scrypt:32768:8:1$dt6ryeylR1Rgeyni$0e7391bec9ac4857fffc7f33660a573d54b80b8e08690f39977a71f53a1acb344b549f1d45a6bd8ac1a97b81db88bdb66801805351acb05ebb9d53edac03ee27"

        if username == "admin" and check_password_hash(stored_password, password):
            session["user"] = username
            return redirect("/")

        else:
            return "Wrong username or password"

    return render_template("login.html")

# ---------- LOGIN ----------

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        stored_password = "scrypt:32768:8:1$dt6ryeylR1Rgeyni$0e7391bec9ac4857fffc7f33660a573d54b80b8e08690f39977a71f53a1acb344b549f1d45a6bd8ac1a97b81db88bdb66801805351acb05ebb9d53edac03ee27"

if username == "admin" and check_password_hash(stored_password, password):
            session["user"] = username
            return redirect("/")

        return "Wrong username or password"

    return render_template("login.html")


# ---------- LOGOUT ----------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------- ADMISSION (ACTIVE) + SEARCH ----------

@app.route("/")
@login_required
def home():

    search = request.args.get("search")
    db = get_db()

    if search:
        patients = db.execute("""
        SELECT * FROM patients
        WHERE status='active'
        AND (mrn LIKE ? OR name LIKE ?)
        """,('%'+search+'%','%'+search+'%')).fetchall()
    else:
        patients = db.execute("""
        SELECT * FROM patients
        WHERE status='active'
        """).fetchall()

    return render_template("admission.html", patients=patients)


# ---------- PATIENT DATABASE + SEARCH ----------

@app.route("/patients")
@login_required
def patients():

    search = request.args.get("search")
    db = get_db()

    if search:
        patients = db.execute("""
        SELECT * FROM patients
        WHERE mrn LIKE ? OR name LIKE ?
        """,('%'+search+'%','%'+search+'%')).fetchall()
    else:
        patients = db.execute("SELECT * FROM patients").fetchall()

    return render_template("patients.html", patients=patients)


# ---------- ARCHIVE + SEARCH ----------

@app.route("/archive")
@login_required
def archive():

    search = request.args.get("search")
    db = get_db()

    if search:
        patients = db.execute("""
        SELECT * FROM patients
        WHERE status='archive'
        AND (mrn LIKE ? OR name LIKE ?)
        """,('%'+search+'%','%'+search+'%')).fetchall()
    else:
        patients = db.execute("""
        SELECT * FROM patients
        WHERE status='archive'
        """).fetchall()

    return render_template("archive.html", patients=patients)


# ---------- ADD PATIENT ----------

@app.route("/add", methods=["GET","POST"])
@login_required
def add_patient():

    if request.method == "POST":

        mrn = request.form["mrn"]
        name = request.form["name"]
        background = request.form["background"]
        admission = request.form["admission"]

        db = get_db()
        db.execute("""
        INSERT INTO patients (mrn,name,background,admission,status)
        VALUES (?,?,?,?,?)
        """,(mrn,name,background,admission,"active"))

        db.commit()
        return redirect("/")

    return render_template("add.html")
    
    # ---------- IMPORT FROM EXCEL ----------

@app.route("/import", methods=["GET","POST"])
@login_required
def import_excel():

    if request.method == "POST":

        file = request.files["file"]

        if file:

            df = pd.read_excel(file)

            db = get_db()

            for _, row in df.iterrows():

                mrn = str(row["MRN"])
                name = str(row["Name"])
                background = str(row["Background"])
                admission = str(row["Admission"])

                db.execute("""
                INSERT INTO patients (mrn,name,background,admission,status)
                VALUES (?,?,?,?,?)
                """,(mrn,name,background,admission,"active"))

            db.commit()

            return redirect("/patients")

    return render_template("import.html")


# ---------- EDIT PATIENT ----------

@app.route("/edit/<int:id>", methods=["GET","POST"])
@login_required
def edit_patient(id):

    db = get_db()

    if request.method == "POST":

        mrn = request.form["mrn"]
        name = request.form["name"]
        background = request.form["background"]
        admission = request.form["admission"]

        db.execute("""
        UPDATE patients
        SET mrn=?, name=?, background=?, admission=?
        WHERE id=?
        """,(mrn,name,background,admission,id))

        db.commit()
        return redirect("/patients")

    patient = db.execute("SELECT * FROM patients WHERE id=?", (id,)).fetchone()
    return render_template("edit.html", patient=patient)


# ---------- DELETE PATIENT ----------

@app.route("/delete/<int:id>")
@login_required
def delete_patient(id):

    db = get_db()
    db.execute("DELETE FROM patients WHERE id=?", (id,))
    db.commit()

    return redirect("/patients")


# ---------- DISCHARGE ----------

@app.route("/discharge/<int:id>")
@login_required
def discharge(id):

    db = get_db()
    db.execute("UPDATE patients SET status='archive' WHERE id=?", (id,))
    db.commit()

    return redirect("/")


# ---------- RETURN FROM ARCHIVE ----------

@app.route("/activate/<int:id>")
@login_required
def activate(id):

    db = get_db()
    db.execute("UPDATE patients SET status='active' WHERE id=?", (id,))
    db.commit()

    return redirect("/archive")


# ---------- RUN ----------

if __name__ == "__main__":

    app.run()
