"""Attendance page Flask backend"""

import os
from flask import Flask, render_template
from pymongo import MongoClient

app = Flask(__name__)

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://admin:password@db:27017")
client = MongoClient(MONGO_URI)
db = client["smartgate"]

@app.route("/attendance")
def attendance():
    """Render attendance records from the MongoDB database"""
    records = list(db.attendance.find().sort("timestamp", -1))
    return render_template("attendance.html", records=records)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

