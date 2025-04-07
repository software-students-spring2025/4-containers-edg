from flask import Flask, render_template
from pymongo import MongoClient
import os

app = Flask(__name__)

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://admin:password@mongodb:27017")
client = MongoClient(MONGO_URI)
db = client["smartgate"]

@app.route("/attendance")
def attendance():
    records = list(db.attendance.find().sort("timestamp", -1))
    return render_template("attendance.html", records=records)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
