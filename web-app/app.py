"""Web app for SmartGate: handles login, session, and attendance filtering."""

import os
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecret")
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://admin:password@db:27017")
client = MongoClient(MONGO_URI)
db = client["smartgate"]


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


@app.route("/logout")
def logout():
    """Logs out the current user and clears session."""
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
