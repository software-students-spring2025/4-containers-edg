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
    g,
)
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecret")
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://admin:password@db:27017")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
DEEPFACE_API_URL = os.environ.get("DEEPFACE_API_URL", "http://localhost:5005")


def get_db():
    """Get MongoDB connection from flask.g cache."""
    if "db" not in g:
        client = MongoClient(MONGO_URI)
        g.db = client["smartgate"]
    return g.db


@app.route("/")
def index():
    """Redirect to signin page."""
    return redirect(url_for("signin"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Handle admin login via password."""
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin password", "error")
    return render_template("admin_login.html")


@app.route("/admin")
def admin_dashboard():
    """Display admin dashboard with attendance and face records."""
    db = get_db()
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    records = list(db.attendance.find().sort("timestamp", -1))
    faces = list(db.faces.find())
    return render_template("admin.html", records=records, faces=faces)


@app.route("/admin/add", methods=["GET", "POST"])
def admin_add_user():
    """Allow admin to add new face records using DeepFace API."""
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    if request.method == "POST":
        name = request.form.get("name")
        image_data = request.form.get("image_data")
        if not name or not image_data:
            flash("Name and face image are required", "error")
            return render_template("admin_add_user.html")
        try:
            response = requests.post(
                f"{DEEPFACE_API_URL}/faces",
                json={"img": image_data, "name": name},
                timeout=30,
            )
            result = response.json()
            if result.get("success"):
                flash(
                    f"User {name} added successfully with face recognition", "success"
                )
                return redirect(url_for("admin_dashboard"))
            flash(f"Error adding face: {result.get('message')}", "error")
        except requests.RequestException as e:
            flash(f"Error connecting to DeepFace service: {str(e)}", "error")
    return render_template("admin_add_user.html")


@app.route("/signin", methods=["GET"])
def signin():
    """Display signin page for face recognition."""
    return render_template("signin.html")


@app.route("/process_signin", methods=["POST"])
def process_signin():
    """Process submitted face image for signin using DeepFace."""
    db = get_db()
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


@app.route("/signin/success/<face_id>/<attendance_id>")
def signin_success(face_id, attendance_id):
    """Show success message after signin."""
    db = get_db()
    user = db.faces.find_one({"_id": ObjectId(face_id)})

    records = db.attendance.find_one({"_id": attendance_id})

    return render_template("signin_success.html", user=user, attendance=records)


@app.route("/attendance/<user_id>")
def attendance(user_id):
    """Show individual user's attendance records."""
    db = get_db()
    user = db.faces.find_one({"_id": ObjectId(user_id)})
    if not user:
        return redirect(url_for("signin"))
    records = list(db.attendance.find({"face_id": user_id}).sort("timestamp", -1))
    return render_template("attendance.html", records=records, user=user)


@app.route("/logout")
def logout():
    """Clear session and logout user/admin."""
    session.clear()
    return redirect(url_for("index"))


@app.route("/admin/delete", methods=["GET"])
def admin_delete_page():
    """Display all face records in a deletable admin view."""
    db = get_db()
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    faces = db.faces.find()
    return render_template("admin_delete.html", faces=faces)


@app.route("/admin/delete/<face_id>", methods=["POST"])
def delete_face(face_id):
    """Delete a specific face record by ID."""
    db = get_db()
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    db.faces.delete_one({"_id": ObjectId(face_id)})
    flash("Face record deleted successfully.", "success")
    return redirect(url_for("admin_delete_page"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
