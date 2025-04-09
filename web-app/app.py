"""Web app for SmartGate: handles login, session, and attendance filtering."""

import os
from datetime import datetime

import requests
from bson.objectid import ObjectId
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
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
    db = get_db()
    """Admin dashboard showing all attendance records."""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    records = list(db.attendance.find().sort("timestamp", -1))

    faces = list(db.faces.find())

    return render_template("admin.html", records=records, faces=faces)


@app.route("/admin/add", methods=["GET", "POST"])
def admin_add_user():
    db = get_db()
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

        # Call the DeepFace API to add the face
        try:
            response = requests.post(
                f"{DEEPFACE_API_URL}/faces",
                json={"img": image_data, "name": name},
                timeout=30,
            )

            result = response.json()
            if result.get("success"):
                flash(
                    f"User {name} added successfully with face recognition",
                    "success",
                )
                return redirect(url_for("admin_dashboard"))

            flash(f"Error adding face: {result.get('message')}", "error")

        except requests.RequestException as e:
            flash(f"Error connecting to DeepFace service: {str(e)}", "error")

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
    db = get_db()
    """Process facial recognition for signin."""
    if "image" not in request.form:
        return jsonify({"success": False, "message": "No image provided"}), 400

    # Get image data
    image_data = request.form.get("image")

    # Call DeepFace API to verify the face
    try:
        response = requests.post(
            f"{DEEPFACE_API_URL}/faces/verify", json={"img": image_data}, timeout=30
        )

        if response.status_code == 200:
            result = response.json()

            if result.get("success") and result.get("verified"):
                match = result.get("match", {})
                face_id = match["_id"]

                attendance_id = db.attendance.insert_one(
                    {
                        "face_id": face_id,
                        "name": match["name"],
                        "timestamp": datetime.now(),
                    }
                ).inserted_id

                return jsonify(
                    {
                        "success": True,
                        "redirect": url_for(
                            "signin_success",
                            face_id=str(face_id),
                            attendance_id=str(attendance_id),
                        ),
                    }
                )

            return jsonify({"success": False, "message": "Face not recognized"})

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
    user = db.faces.find_one({"_id": ObjectId(face_id)})

    records = db.attendance.find_one({"_id": attendance_id})

    return render_template("signin_success.html", user=user, attendance=records)


@app.route("/attendance/<user_id>")
def attendance(user_id):
    """Show attendance records for a specific user."""
    user = db.faces.find_one({"_id": ObjectId(user_id)})

    if not user:
        return redirect(url_for("signin"))

    records = list(db.attendance.find({"face_id": user_id}).sort("timestamp", -1))

    return render_template("attendance.html", records=records, user=user)


@app.route("/logout")
def logout():
    """Logs out the current user or admin and clears session."""
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
