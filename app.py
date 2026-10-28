
import os
import time
import uuid
import requests

from flask import Flask, request, Response, jsonify, send_file
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)

CORS(app, origins=[
    "https://biplopbbrm-blip.github.io",
    "https://web.telegram.org"
])

# Temporary storage for processed PNG images
RESULTS = {}
LINK_LIFETIME = 3600


def clean_old_results():
    now = time.time()
    expired = [
        token for token, item in RESULTS.items()
        if now - item["created"] > LINK_LIFETIME
    ]
    for token in expired:
        RESULTS.pop(token, None)


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

    try:
        result = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            headers={"X-Api-Key": api_key},
            files={
                "image_file": (
                    photo.filename,
                    photo.stream,
                    photo.mimetype
                )
            },
            data={"size": "auto"},
            timeout=90
        )
    except requests.RequestException:
        return jsonify({
            "error": "Could not connect to the background removal service"
        }), 502

    if result.status_code != 200:
        return jsonify({
            "error": "Background removal failed",
            "details": result.text[:300]
        }), result.status_code

    clean_old_results()
    token = uuid.uuid4().hex

    RESULTS[token] = {
        "data": result.content,
        "created": time.time()
    }

    base_url = request.host_url.rstrip("/")
    download_url = f"{base_url}/download/{token}"
    preview_url = f"{base_url}/download/{token}?view=1"

    return jsonify({
        "success": True,
        "download_url": download_url,
        "preview_url": preview_url,
        "filename": "cb8-remover.png"
    })


@app.route("/download/<token>", methods=["GET"])
def download_image(token):
    clean_old_results()
    item = RESULTS.get(token)

    if not item:
        return jsonify({
            "error": "This download link has expired. Please process the image again."
        }), 404

    preview = request.args.get("view") == "1"

    response = send_file(
        BytesIO(item["data"]),
        mimetype="image/png",
        as_attachment=not preview,
        download_name="cb8-remover.png",
        max_age=0
    )

    response.headers["Cache-Control"] = "no-store"
    response.headers["Access-Control-Expose-Headers"] = "Content-Disposition"
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
