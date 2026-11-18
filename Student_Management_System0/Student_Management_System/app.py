import os
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from cloudant_db import CloudantStore

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-before-deployment")
db = CloudantStore()

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user"): return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Administrator access required.", "warning")
            return redirect(url_for("students"))
        return fn(*args, **kwargs)
    return wrapper

@app.context_processor
def globals_for_templates():
    return {"current_user": session.get("user"), "current_role": session.get("role")}

@app.route("/")
def index():
    return redirect(url_for("dashboard") if session.get("user") else url_for("login"))

@app.route("/setup", methods=["GET", "POST"])
def setup():
    if db.count({"type":"user"}) > 0:
        flash("Setup is already complete. Please sign in.", "info")
        return redirect(url_for("login"))
    if request.method == "POST":
        username=request.form.get("username","").strip().lower()
        password=request.form.get("password","")
        if len(username)<3 or len(password)<8:
            flash("Username must be 3+ characters and password 8+ characters.", "warning")
        else:
            db.insert({"type":"user","username":username,"password_hash":generate_password_hash(password),"role":"admin"})
            flash("Administrator created. Sign in to continue.", "success")
            return redirect(url_for("login"))
    return render_template("setup.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        user=db.find_one({"type":"user","username":request.form.get("username","").strip().lower()})
        if user and check_password_hash(user.get("password_hash",""),request.form.get("password","")):
            session["user"]=user["username"]; session["role"]=user.get("role","staff")
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    students=db.find({"type":"student"})
    courses=sorted(set(s.get("course","Other") for s in students))
    avg=round(sum(float(s.get("attendance",0) or 0) for s in students)/len(students),1) if students else 0
    recent=sorted(students,key=lambda s:s.get("created_at",""),reverse=True)[:5]
    return render_template("dashboard.html",total=len(students),courses=courses,avg=avg,recent=recent,
        labels=courses,counts=[sum(1 for s in students if s.get("course")==c) for c in courses])

@app.route("/students")
@login_required
def students():
    q=request.args.get("q","").strip().lower()
    data=db.find({"type":"student"})
    if q: data=[s for s in data if q in s.get("name","").lower() or q in s.get("roll","").lower() or q in s.get("course","").lower()]
    data.sort(key=lambda s:s.get("name","").lower())
    return render_template("students.html",students=data,q=q)

def form_data():
    return {"name":request.form.get("name","").strip(),"roll":request.form.get("roll","").strip().upper(),
        "course":request.form.get("course","").strip(),"email":request.form.get("email","").strip(),
        "phone":request.form.get("phone","").strip(),"grade":request.form.get("grade","N/A").upper(),
        "attendance":float(request.form.get("attendance","0") or 0),"updated_at":datetime.now(timezone.utc).isoformat()}

@app.route("/students/add",methods=["GET","POST"])
@login_required
def add_student():
    if request.method=="POST":
        data=form_data()
        if not data["name"] or not data["roll"] or not data["course"]:
            flash("Name, roll number and course are required.","warning")
        elif not 0<=data["attendance"]<=100:
            flash("Attendance must be between 0 and 100.","warning")
        elif db.find_one({"type":"student","roll":data["roll"]}):
            flash("That roll number already exists.","danger")
        else:
            data.update(type="student",created_at=datetime.now(timezone.utc).isoformat())
            db.insert(data); flash("Student added successfully.","success")
            return redirect(url_for("students"))
    return render_template("student_form.html",student=None,title="Add student")

@app.route("/students/<sid>/edit",methods=["GET","POST"])
@login_required
def edit_student(sid):
    s=db.get(sid)
    if s.get("type")!="student": return redirect(url_for("students"))
    if request.method=="POST":
        data=form_data()
        duplicate=db.find_one({"type":"student","roll":data["roll"]})
        if not data["name"] or not data["roll"] or not data["course"] or not 0<=data["attendance"]<=100:
            flash("Check required fields and attendance range.","warning")
        elif duplicate and duplicate.get("_id")!=sid: flash("Roll number already exists.","danger")
        else:
            s.update(data); db.update(s); flash("Student updated.","success")
            return redirect(url_for("students"))
    return render_template("student_form.html",student=s,title="Edit student")

@app.route("/students/<sid>/delete",methods=["POST"])
@login_required
@admin_required
def delete_student(sid):
    s=db.get(sid)
    if s.get("type")=="student": db.delete(s); flash("Student deleted.","success")
    return redirect(url_for("students"))

@app.route("/attendance")
@login_required
def attendance():
    data=db.find({"type":"student"}); data.sort(key=lambda s:s.get("name","").lower())
    return render_template("attendance.html",students=data)

@app.route("/attendance/<sid>",methods=["POST"])
@login_required
def save_attendance(sid):
    s=db.get(sid)
    try:
        n=float(request.form.get("attendance",""))
        if not 0<=n<=100: raise ValueError()
        s["attendance"]=n; db.update(s); flash("Attendance updated.","success")
    except ValueError: flash("Enter a percentage from 0 to 100.","danger")
    return redirect(url_for("attendance"))

@app.route("/grades")
@login_required
def grades():
    data=db.find({"type":"student"}); data.sort(key=lambda s:s.get("name","").lower())
    return render_template("grades.html",students=data)

@app.route("/grades/<sid>",methods=["POST"])
@login_required
def save_grade(sid):
    s=db.get(sid); grade=request.form.get("grade","N/A").upper()
    if grade not in {"N/A","A+","A","B+","B","C","D","F"}: flash("Invalid grade.","danger")
    else: s["grade"]=grade; db.update(s); flash("Grade updated.","success")
    return redirect(url_for("grades"))

@app.errorhandler(Exception)
def errors(error):
    app.logger.exception(error)
    return render_template("error.html"),500

if __name__=="__main__":
    app.run(host="127.0.0.1",port=int(os.getenv("PORT",5000)),debug=os.getenv("FLASK_DEBUG","false").lower()=="true")
