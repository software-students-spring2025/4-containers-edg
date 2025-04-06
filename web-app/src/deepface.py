import os
import requests
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv


class DeepFaceService:
    def __init__(self):
        load_dotenv()
        self.deepface_api_url = os.getenv("DEEPFACE_API_URL")
        mongo_uri = os.getenv("MONGO_URI")
        self.client = MongoClient(mongo_uri)
        self.db = self.client.smart_gates
        self.faces = self.db.faces
        self.threshold = float(os.getenv("DEEPFACE_THRESHOLD", 10))

    def add_face(self, image_data, name):
        """
        Add a face to the database for future recognition

        Args:
            image_data (str): Base64 encoded image
            name (str): Name of the person

        Returns:
            dict: Response from DeepFace API with face embeddings
        """
        try:
            face_doc = {"name": name, "img": image_data}
            face_id = self.faces.insert_one(face_doc).inserted_id

            return {
                "success": True,
                "face_id": str(face_id),
                "message": "Face added successfully",
            }

        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}

    def verify_face(self, image_data):
        """
        Verify a face against stored faces

        Args:
            image_data (str): Base64 encoded image
            user_id (str, optional): Specific user ID to verify against

        Returns:
            dict: Verification result
        """
        try:
            # get all stored faces
            stored_faces = list(self.faces.find())

            if not stored_faces:
                return {
                    "success": False,
                    "message": "No matching faces found in database",
                }

            # Verify against each stored face
            best_match = None
            lowest_distance = None

            for face in stored_faces:
                print(f"comparing {face['_id']}")
                response = requests.post(
                    f"{self.deepface_api_url}/verify",
                    json={
                        "img1": image_data,
                        "img2": face["img"],
                        "model_name": "Facenet",
                        "detector_backend": "mtcnn",
                        "distance_metric": "euclidean",
                    },
                )

                if response.status_code == 200:
                    result = response.json()

                    distance = result.get("distance")
                    if lowest_distance is None or distance < lowest_distance:
                        lowest_distance = distance
                        best_match = {
                            "_id": face.get("_id"),
                            "name": face["name"],
                            "distance": distance,
                        }
                        print(f"found best match:\n {best_match}")
                else:
                    return {
                        "success": False,
                        "message": f"Error verifying face: {response.text}",
                    }

            if best_match and best_match["distance"] <= self.threshold:
                return {"success": True, "verified": True, "match": best_match}
            else:
                return {
                    "success": True,
                    "verified": False,
                    "message": "No matching face found",
                }

        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}

    def delete_face(self, face_id):
        """
        Delete a face from the database

        Args:
            face_id (str): ID of the face to delete

        Returns:
            dict: Operation result
        """
        try:
            result = self.faces.delete_one({"_id": ObjectId(face_id)})

            if result.deleted_count > 0:
                return {"success": True, "message": "Face deleted successfully"}
            else:
                return {"success": False, "message": "Face not found"}

        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
