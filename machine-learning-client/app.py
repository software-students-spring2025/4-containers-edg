from flask import Flask, jsonify, request
from src.deepface_service import DeepFaceService

app = Flask(__name__)

df = DeepFaceService()


@app.route("/")
def index():
    return "Welcome to the Machine Learning Client"


@app.route("/faces", methods=["POST"])
def add_face():
    json_data = request.get_json()

    if "img" not in json_data or "name" not in json_data:
        return (
            jsonify(
                {"success": False, "message": "Missing required fields (img, name)"}
            ),
            400,
        )

    img = json_data["img"]
    name = json_data["name"]
    res = df.add_face(img, name)

    return res, 201


@app.route("/faces/verify", methods=["POST"])
def verify_face():
    json_data = request.get_json()

    if "img" not in json_data:
        return (
            jsonify({"success": False, "message": "Missing required fields (img)"}),
            400,
        )

    img = json_data["img"]
    res = df.verify_face(img)

    return res, 200


@app.route("/faces/<face_id>", methods=["DELETE"])
def delete_face(face_id):
    res = df.delete_face(face_id)

    return res, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005)
