import os
import socket
from flask import (
    Flask,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from pathlib import Path
from get_name import Get_Name
import requests
import urllib3
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from converter import Converter

load_dotenv()

app = Flask(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]

APP_PASSWORD = os.environ["APP_PASSWORD"]


# Dynamic path resolution for cross-platform portability
SYNCED_FOLDER_PATH = os.environ.get(
    "SYNCED_FOLDER_PATH",
    os.path.join(
        os.path.expanduser("~"),
        "Syncthing_save_folder",
    ),
)
os.makedirs(SYNCED_FOLDER_PATH, exist_ok=True)

# Relay & Storage Node Configuration
api = os.environ["SYNCTHING_API_KEY"]

converter = Converter()


sync_url = os.environ["SYNCTHING_URL"]


def is_running(host="127.0.0.1", port=8384):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((host, port)) == 0


def get_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip
def require_login():
    return session.get("logged_in") is True


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password", "")

        if password == APP_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("home"))

        return render_template(
            "login.html",
            error="Incorrect password.",
        ), 401

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
def home():
    if not require_login():
        return redirect(url_for("login"))
    items = Get_Name.get_folders(SYNCTHING_URL=sync_url, API_KEY=api)
    return render_template("index.html", files=items)


@app.route("/upload", methods=["GET"])
def upload():
    if not require_login():
        return redirect(url_for("login"))
    
    return render_template("file_add.html")


@app.route("/upload/complete", methods=["POST"])
def upload_complete():
    if not require_login():
        return redirect(url_for("login"))
    
    if "selected_file" in request.files:
        file = request.files["selected_file"]
        if file.filename != "":
            filename = secure_filename(file.filename)
            file_path = os.path.join(SYNCED_FOLDER_PATH, filename)
            file.save(file_path)
            return redirect("/")

    if "selected_folder" in request.files:
        files = request.files.getlist("selected_folder")
        if files and files[0].filename != "":
            for file in files:
                clean_path = os.path.normpath(file.filename)
                safe_parts = [
                    secure_filename(part) for part in clean_path.split(os.sep)
                ]
                relative_safe_path = os.path.join(*safe_parts)
                file_path = os.path.join(
                    SYNCED_FOLDER_PATH, relative_safe_path
                )
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
        return redirect("/")


@app.route("/add-device", methods=["GET", "POST"])
def get_device_id():
    if not require_login():
        return redirect(url_for("login"))
    
    headers = {"X-API-Key": api}
    response = requests.get(
        f"{sync_url}/rest/system/status", headers=headers, verify=False
    )

    if response.status_code == 200:
        device_id = response.json().get("myID")
        return f"<h3>Scan or enter this Device ID on your phone:</h3><p><code>{device_id}</code></p>"
    return "Failed to fetch Device ID", 500


@app.route("/converter", methods=["GET", "POST"])
def converter_page():
    if not require_login():
        return redirect(url_for("login"))
    if request.method == "POST":
        selected_file = request.form.get("filename")
        target_file = request.form.get("target_format")

        if selected_file and target_file:
            full_input_path = os.path.join(SYNCED_FOLDER_PATH, selected_file)

            if target_file in ["pdf", "docx"]:
                converter.doc_converter(
                    filename=full_input_path, target_format=target_file
                )

            elif target_file in ["jpg", "png", "webp"]:
                format_map = {"jpg": "JPEG", "png": "PNG", "webp": "WEBP"}
                converter.img_converter(
                    start_img=full_input_path,
                    end_img_extension=target_file,
                    file_format=format_map[target_file],
                )

            elif target_file in ["mp3", "wav", "mp4", "mkv"]:
                converter.convert_audio_and_video(
                    input_path=full_input_path, output_ext=target_file
                )

        return redirect("/")

    items = Get_Name.get_folders(SYNCTHING_URL=sync_url, API_KEY=api)
    return render_template("convert.html", files=items)


@app.route("/download/<path:filename>", methods=["GET"])
def download_file(filename):
    if not require_login():
        return redirect(url_for("login"))
    synced_folder = Path(SYNCED_FOLDER_PATH).resolve()

    # Make the requested filename/path absolute so we can validate it.
    requested_file = (synced_folder / filename).resolve()

    # Block unsafe paths, for example:
    # /download/../../Windows/System32/something.txt
    if (
        requested_file != synced_folder
        and synced_folder not in requested_file.parents
    ):
        return "Invalid file path.", 400

    # The laptop must have the file already synced locally.
    if not requested_file.is_file():
        return (
            f"File not found locally: {filename}. "
            "Wait for Syncthing to finish syncing.",
            404,
        )

    return send_from_directory(
        directory=str(synced_folder),
        path=filename,
        as_attachment=True,
        download_name=requested_file.name,
    )


if __name__ == "__main__":
 
    app.run(host="0.0.0.0", port=5000, debug=True) # soon debug=False