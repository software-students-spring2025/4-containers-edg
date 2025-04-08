"""Web app for SmartGate: handles login, session, and attendance filtering."""

import os

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
    return redirect(url_for("signin"))


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


# @app.route("/signin/process", methods=["POST"])
# def process_signin():
"""Process facial recognition for signin."""
# This would call the DeepFace service to identify the user
# from the captured image and record attendance

# TODO: make a reqeust: POST localhost:5005/faces

# {
#     faceId: ref-> Faces
#     timestamp: <date>
# }

# return redirect(url_for("signin_success", attendance_id=))


# @app.route("/signin/success/<attendance_id>")
# def signin_success(attendance_id):
#     """Show success message after signin."""
# attendance = db.attendance.find_one({"_id": attendance_id})
#     return render_template("signin_success.html", user=user)
#
# @app.route("/attendance/<face_id>")
# def attendance(face_id):
#     records = list(db.attendance.find({"face_id": face_id}).sort("timestamp", -1))
#     return render_template("attendance.html", records=records, user_id=user_id)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
