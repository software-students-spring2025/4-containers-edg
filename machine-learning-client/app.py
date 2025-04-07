from datetime import datetime

from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return "Welcome to the Machine Learning Client"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
