"""Web app for SmartGate: handles login, session, and attendance filtering."""

import os
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, session, url_for
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecret")
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://admin:password@db:27017")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
DEEEPFACE_API_URL = os.environ.get("DEEPFACE_API_RUL", "http://localhost:5005")

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


@app.route("/admin/add")
def admin_add_user():
    """Admin page to add new users with facial recognition."""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    user_id = request.form.get("user_id")
    name = request.form.get("name")

    # Check if user already exists
    existing_user = db.users.find_one({"user_id": user_id})
    if existing_user:
        flash("User ID already exists", "error")
        return render_template("admin_add_user.html")

    return render_template("admin_add_user.html")


@app.route("/signin")
def signin():
    """Facial recognition signin page."""
    return render_template("signin.html")


@app.route("/process_signin", methods=["POST"])
def process_signin():
    """Process facial recognition for signin."""
    # This would call the DeepFace service to identify the user
    # from the captured image and record attendance

    # TODO: make a reqeust: POST localhost:5005/faces

    # {
    #     faceId: ref-> Faces
    #     timestamp: <date>
    # }

    return redirect(url_for("signin_success", user_id=recognized_user_id))


@app.route("/signin/success/<attendanceId>")
def signin_success(attendanceId):
    """Show success message after signin."""
    user = db.attendance.find_one({"_id": attendanceId})
    return render_template("signin_success.html", user=user)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
