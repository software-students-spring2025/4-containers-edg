"""Web app for SmartGate: handles login, session, and attendance filtering."""

import os
import json
import base64
import requests
from datetime import datetime

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
    jsonify,
)
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecret")
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://admin:password@db:27017")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
DEEPFACE_API_URL = os.environ.get("DEEPFACE_API_URL", "http://localhost:5005")

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
    faces = list(db.faces.find())

    return render_template("admin.html", records=records, faces=faces)


@app.route("/admin/add", methods=["GET", "POST"])
def admin_add_user():
    """Admin page to add new users with facial recognition."""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        # Process form submission
        name = request.form.get("name")
        image_data = request.form.get("image_data")

        if not name or not image_data:
            flash("Name and face image are required", "error")
            return render_template("admin_add_user.html")

        # Process the image data (remove data:image/jpeg;base64, prefix)
        image_data = image_data.split(",")[1] if "," in image_data else image_data

        # Call the DeepFace API to add the face
        try:
            response = requests.post(
                f"{DEEPFACE_API_URL}/faces",
                json={"img": image_data, "name": name},
                timeout=10,
            )

            if response.status_code == 201:
                result = response.json()
                if result.get("success"):
                    # Create user in database with face_id
                    user_id = db.users.insert_one(
                        {
                            "name": name,
                            "face_id": result.get("face_id"),
                            "created_at": datetime.now(),
                        }
                    ).inserted_id

                    flash(
                        f"User {name} added successfully with face recognition",
                        "success",
                    )
                    return redirect(url_for("admin_dashboard"))
                else:
                    flash(f"Error adding face: {result.get('message')}", "error")
            else:
                flash(
                    f"Error communicating with DeepFace API: {response.status_code}",
                    "error",
                )

        except requests.RequestException as e:
            flash(f"Error connecting to DeepFace service: {str(e)}", "error")

    return render_template("admin_add_user.html")


@app.route("/signin", methods=["GET"])
def signin():
    """Facial recognition signin page."""
    return render_template("signin.html")


@app.route("/process_signin", methods=["POST"])
def process_signin():
    """Process facial recognition for signin."""
    if "image" not in request.form:
        return jsonify({"success": False, "message": "No image provided"}), 400

    # Get image data
    image_data = request.form.get("image")
    image_data = image_data.split(",")[1] if "," in image_data else image_data

    # Call DeepFace API to verify the face
    try:
        response = requests.post(
            f"{DEEPFACE_API_URL}/faces/verify", json={"img": image_data}, timeout=10
        )

        if response.status_code == 200:
            result = response.json()

            if result.get("success") and result.get("verified"):
                match = result.get("match", {})
                face_id = match.get("_id")

                # Find the user associated with this face
                user = db.users.find_one({"face_id": face_id})

                if user:
                    # Record attendance
                    attendance_id = db.attendance.insert_one(
                        {
                            "user_id": str(user["_id"]),
                            "face_id": face_id,
                            "name": user["name"],
                            "timestamp": datetime.now(),
                            "status": "check-in",
                        }
                    ).inserted_id

                    return jsonify(
                        {
                            "success": True,
                            "redirect": url_for(
                                "signin_success", user_id=str(user["_id"])
                            ),
                        }
                    )
                else:
                    return jsonify(
                        {
                            "success": False,
                            "message": "Face recognized but no user found",
                        }
                    )
            else:
                return jsonify({"success": False, "message": "Face not recognized"})
        else:
            return jsonify(
                {
                    "success": False,
                    "message": f"Error communicating with DeepFace API: {response.status_code}",
                }
            )

    except requests.RequestException as e:
        return jsonify(
            {
                "success": False,
                "message": f"Error connecting to DeepFace service: {str(e)}",
            }
        )


@app.route("/signin/success/<user_id>")
def signin_success(user_id):
    """Show success message after signin."""
    user = db.users.find_one({"_id": user_id})
    if not user:
        return redirect(url_for("signin"))

    # Get most recent attendance record
    attendance = db.attendance.find_one({"user_id": user_id}, sort=[("timestamp", -1)])

    return render_template("signin_success.html", user=user, attendance=attendance)


@app.route("/attendance/<user_id>")
def attendance(user_id):
    """Show attendance records for a specific user."""
    user = db.users.find_one({"_id": user_id})
    if not user:
        return redirect(url_for("signin"))

    records = list(db.attendance.find({"user_id": user_id}).sort("timestamp", -1))
    return render_template("attendance.html", records=records, user=user)


@app.route("/logout")
def logout():
    """Logs out the current user or admin and clears session."""
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
