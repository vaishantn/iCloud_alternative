import os
import socket
from datetime import datetime
from pathlib import Path

import requests
import urllib3
from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename

from converter import Converter
from get_name import Get_Name


load_dotenv()

app = Flask(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]
csrf = CSRFProtect(app)

APP_PASSWORD = os.environ["APP_PASSWORD"]

BASE_DIR = Path(__file__).resolve().parent

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

if DEMO_MODE:
    SYNCED_FOLDER_PATH = (BASE_DIR / "demo_files").resolve()
else:
    SYNCED_FOLDER_PATH = Path(
        os.getenv(
            "SYNCED_FOLDER_PATH",
            os.path.join(
                os.path.expanduser("~"),
                "Syncthing_savefolder",
            ),
        )
    ).expanduser().resolve()

os.makedirs(SYNCED_FOLDER_PATH, exist_ok=True)

api = os.environ["SYNCTHING_API_KEY"]
sync_url = os.environ["SYNCTHING_URL"]

converter = Converter()


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


def get_demo_files():
    files = []

    for path in sorted(SYNCED_FOLDER_PATH.rglob("*")):
        if path.is_file():
            relative_path = path.relative_to(
                SYNCED_FOLDER_PATH
            ).as_posix()

            files.append(
                {
                    "folder_name": "Demo Files",
                    "file_name": path.name,
                    "relative_path": relative_path,
                    "type": "file",
                    "size": path.stat().st_size,
                    "time": datetime.fromtimestamp(
                        path.stat().st_mtime
                    ).strftime("%Y-%m-%d %H:%M"),
                }
            )

    return files


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

    if DEMO_MODE:
        items = get_demo_files()
    else:
        items = Get_Name.get_folders(
            SYNCTHING_URL=sync_url,
            API_KEY=api,
        )

    return render_template(
        "index.html",
        files=items,
        demo_mode=DEMO_MODE,
    )


@app.route("/upload", methods=["GET"])
def upload():
    if not require_login():
        return redirect(url_for("login"))

    return render_template(
        "file_add.html",
        demo_mode=DEMO_MODE,
    )

    return render_template("file_add.html")


@app.route("/upload/complete", methods=["POST"])
def upload_complete():
    if not require_login():
        return redirect(url_for("login"))

    if DEMO_MODE:
        abort(403, description="Uploading is disabled in the public demo.")

    if "selected_file" in request.files:
        file = request.files["selected_file"]

        if file.filename != "":
            filename = secure_filename(file.filename)
            file_path = os.path.join(SYNCED_FOLDER_PATH, filename)
            file.save(file_path)
            return redirect(url_for("home"))

    if "selected_folder" in request.files:
        files = request.files.getlist("selected_folder")

        if files and files[0].filename != "":
            for file in files:
                clean_path = os.path.normpath(file.filename)

                safe_parts = [
                    secure_filename(part)
                    for part in clean_path.split(os.sep)
                ]

                relative_safe_path = os.path.join(*safe_parts)

                file_path = os.path.join(
                    SYNCED_FOLDER_PATH,
                    relative_safe_path,
                )

                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)

        return redirect(url_for("home"))

    return redirect(url_for("upload"))


@app.route("/add-device", methods=["GET", "POST"])
def get_device_id():
    if not require_login():
        return redirect(url_for("login"))

    if DEMO_MODE:
        abort(
            403,
            description="Adding a Syncthing device is disabled in the public demo.",
        )

    headers = {"X-API-Key": api}

    response = requests.get(
        f"{sync_url}/rest/system/status",
        headers=headers,
        verify=False,
        timeout=10,
    )

    if response.status_code == 200:
        device_id = response.json().get("myID")

        return (
            "<h3>Scan or enter this Device ID on your phone:</h3>"
            f"<p><code>{device_id}</code></p>"
        )

    return "Failed to fetch Device ID", 500


@app.route("/converter", methods=["GET", "POST"])
def converter_page():
    if not require_login():
        return redirect(url_for("login"))

    if request.method == "POST":
        if DEMO_MODE:
            abort(
                403,
                description="File conversion is disabled in the public demo.",
            )

        selected_file = request.form.get("filename")
        target_file = request.form.get("target_format")

        if selected_file and target_file:
            full_input_path = os.path.join(
                SYNCED_FOLDER_PATH,
                selected_file,
            )

            if target_file in ["pdf", "docx"]:
                converter.doc_converter(
                    filename=full_input_path,
                    target_format=target_file,
                )

            elif target_file in ["jpg", "png", "webp"]:
                format_map = {
                    "jpg": "JPEG",
                    "png": "PNG",
                    "webp": "WEBP",
                }

                converter.img_converter(
                    start_img=full_input_path,
                    end_img_extension=target_file,
                    file_format=format_map[target_file],
                )

            elif target_file in ["mp3", "wav", "mp4", "mkv"]:
                converter.convert_audio_and_video(
                    input_path=full_input_path,
                    output_ext=target_file,
                )

        return redirect(url_for("home"))

    if DEMO_MODE:
        items = get_demo_files()
    else:
        items = Get_Name.get_folders(
            SYNCTHING_URL=sync_url,
            API_KEY=api,
        )

    return render_template(
        "convert.html",
        files=items,
        demo_mode=DEMO_MODE,
    )


@app.route("/download/<path:filename>", methods=["GET"])
def download_file(filename):
    if not require_login():
        return redirect(url_for("login"))

    synced_folder = Path(SYNCED_FOLDER_PATH).resolve()
    requested_file = (synced_folder / filename).resolve()

    if (
        requested_file != synced_folder
        and synced_folder not in requested_file.parents
    ):
        return "Invalid file path.", 400

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
    app.run(host="127.0.0.1", port=5000, debug=False)