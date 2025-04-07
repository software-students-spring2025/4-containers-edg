"""Web app for SmartGate: handles login, session, and attendance filtering."""

import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecret")
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://admin:password@db:27017")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

client = MongoClient(MONGO_URI)
db = client["smartgate"]


@app.route("/")
def index():
    """Home page - redirect to login if not logged in, otherwise show attendance."""
    if "user_id" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("attendance"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handles user login and saves user_id to session."""
    if request.method == "POST":
        user_id = request.form["user_id"]
        session["user_id"] = user_id
        return redirect(url_for("attendance"))
    return render_template("login.html")


@app.route("/attendance")
def attendance():
    """Shows attendance records for the logged-in user."""
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_id = session["user_id"]
    records = list(db.attendance.find({"user_id": user_id}).sort("timestamp", -1))
    return render_template("attendance.html", records=records, user_id=user_id)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Handles admin login with password verification."""
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid admin password", "error")
    return render_template("admin_login.html")


@app.route("/admin")
def admin_dashboard():
    """Admin dashboard showing all attendance records."""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    # Get all attendance records, sorted by timestamp (newest first)
    records = list(db.attendance.find().sort("timestamp", -1))
    
    # Get all unique users
    users = db.users.find()
    
    return render_template("admin.html", records=records, users=users)


@app.route("/admin/add", methods=["GET", "POST"])
def admin_add_user():
    """Admin page to add new users with facial recognition."""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    if request.method == "POST":
        user_id = request.form.get("user_id")
        name = request.form.get("name")
        
        # Check if user already exists
        existing_user = db.users.find_one({"user_id": user_id})
        if existing_user:
            flash("User ID already exists", "error")
            return render_template("admin_add_user.html")
        
        # Save user to database
        db.users.insert_one({
            "user_id": user_id,
            "name": name,
            "created_at": datetime.now()
        })
        
        # Redirect to facial enrollment page
        return redirect(url_for("admin_enroll_face", user_id=user_id))
    
    return render_template("admin_add_user.html")


@app.route("/admin/enroll/<user_id>", methods=["GET", "POST"])
def admin_enroll_face(user_id):
    """Page to capture and enroll user's face."""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    user = db.users.find_one({"user_id": user_id})
    if not user:
        flash("User not found", "error")
        return redirect(url_for("admin_add_user"))
    
    if request.method == "POST":
        # Handle face image submission to DeepFace service
        # This would typically involve calling the DeepFace API
        flash("Face enrolled successfully", "success")
        return redirect(url_for("admin_dashboard"))
    
    return render_template("admin_enroll_face.html", user=user)


@app.route("/signin")
def signin():
    """Facial recognition signin page."""
    return render_template("signin.html")


@app.route("/process_signin", methods=["POST"])
def process_signin():
    """Process facial recognition for signin."""
    # This would call the DeepFace service to identify the user
    # from the captured image and record attendance
    
    # For demo purposes, let's assume we identified a user
    recognized_user_id = "demo_user"  # In reality, this would come from the face recognition service
    
    # Record attendance
    db.attendance.insert_one({
        "user_id": recognized_user_id,
        "timestamp": datetime.now(),
        "status": "check-in"
    })
    
    return redirect(url_for("signin_success", user_id=recognized_user_id))


@app.route("/signin/success/<user_id>")
def signin_success(user_id):
    """Show success message after signin."""
    user = db.users.find_one({"user_id": user_id})
    return render_template("signin_success.html", user=user)


@app.route("/logout")
def logout():
    """Logs out the current user and clears session."""
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)