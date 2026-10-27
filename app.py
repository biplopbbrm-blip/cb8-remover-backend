import os
import requests
from flask import Flask, request, Response, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=[
    "https://biplopbbrm-blip.github.io"
])

@app.route("/")
def home():
    return "CB8 Remover AI Backend is running!"

@app.route("/remove-bg", methods=["POST"])
def remove_bg():
    api_key = os.environ.get("REMOVE_BG_API_KEY")
    if not api_key:
        return jsonify({"error": "Server API key is missing"}), 500

    photo = request.files.get("image")
    if not photo:
        return jsonify({"error": "Please upload an image"}), 400

    result = requests.post(
        "https://api.remove.bg/v1.0/removebg",
        headers={"X-Api-Key": api_key},
        files={"image_file": (photo.filename, photo.stream, photo.mimetype)},
        data={"size": "auto"},
        timeout=90
    )

    if result.status_code != 200:
        return jsonify({
            "error": "Background removal failed",
            "details": result.text[:500]
        }), result.status_code

    return Response(
        result.content,
        mimetype="image/png",
        headers={"Content-Disposition": "inline; filename=cb8-removed.png"}
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
