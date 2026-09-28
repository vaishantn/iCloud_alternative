import os
from datetime import datetime
from pathlib import Path

import requests
import urllib3
from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
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
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 1024  # 1 GB upload limit

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
            str(Path.home() / "Syncthing_savefolder"),
        )
    ).expanduser().resolve()

SYNCED_FOLDER_PATH.mkdir(parents=True, exist_ok=True)

# In normal mode, these must come from the user's private .env file.
# Placeholder values let the app start but Syncthing actions will fail
# until the user replaces them with their real configuration.
api = os.getenv("SYNCTHING_API_KEY", "")
sync_url = os.getenv("SYNCTHING_URL", "")

converter = Converter()


def require_login():
    return session.get("logged_in") is True


def get_local_files():
    files = []

    for path in sorted(SYNCED_FOLDER_PATH.rglob("*")):
        if path.is_file():
            relative_path = path.relative_to(SYNCED_FOLDER_PATH).as_posix()

            files.append(
                {
                    "folder_name": "Syncthing Files",
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


def get_syncthing_files():
    if not sync_url or not api:
        raise RuntimeError(
            "Syncthing is not configured. Set SYNCTHING_URL and "
            "SYNCTHING_API_KEY in your .env file."
        )

    return Get_Name.get_folders(
        SYNCTHING_URL=sync_url,
        API_KEY=api,
    )


def path_is_inside_sync_folder(path):
    synced_folder = SYNCED_FOLDER_PATH.resolve()
    resolved_path = Path(path).resolve()

    return (
        resolved_path == synced_folder
        or synced_folder in resolved_path.parents
    )


@app.errorhandler(413)
def request_entity_too_large(error):
    flash("Upload is too large. The maximum allowed upload size is 1 GB.", "error")
    return redirect(url_for("upload"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password", "")

        if password == APP_PASSWORD:
            session.clear()
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

    try:
        items = get_local_files()

    except (requests.RequestException, RuntimeError, ValueError) as exc:
        app.logger.warning("Could not load Syncthing files: %s", exc)
        flash(
            f"Could not connect to Syncthing: {exc}",
            "error",
        )
        items = []

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


@app.route("/upload/complete", methods=["POST"])
def upload_complete():
    if not require_login():
        return redirect(url_for("login"))

    if DEMO_MODE:
        abort(403, description="Uploading is disabled in the public demo.")

    if "selected_file" in request.files:
        uploaded_file = request.files["selected_file"]

        if uploaded_file.filename:
            filename = secure_filename(uploaded_file.filename)

            if not filename:
                flash("That filename is not allowed.", "error")
                return redirect(url_for("upload"))

            file_path = (SYNCED_FOLDER_PATH / filename).resolve()

            if not path_is_inside_sync_folder(file_path):
                abort(400, description="Invalid upload path.")

            uploaded_file.save(str(file_path))
            flash(f"Uploaded {filename}.", "success")
            return redirect(url_for("home"))

    if "selected_folder" in request.files:
        uploaded_files = request.files.getlist("selected_folder")

        if uploaded_files and uploaded_files[0].filename:
            saved_count = 0

            for uploaded_file in uploaded_files:
                # Browser folder uploads commonly use forward slashes,
                # including when the host machine runs Windows.
                submitted_parts = uploaded_file.filename.replace("\\", "/").split("/")

                safe_parts = [
                    secure_filename(part)
                    for part in submitted_parts
                    if part and part not in {".", ".."}
                ]

                if not safe_parts:
                    continue

                relative_safe_path = Path(*safe_parts)
                file_path = (SYNCED_FOLDER_PATH / relative_safe_path).resolve()

                if not path_is_inside_sync_folder(file_path):
                    abort(400, description="Invalid folder upload path.")

                file_path.parent.mkdir(parents=True, exist_ok=True)
                uploaded_file.save(str(file_path))
                saved_count += 1

            if saved_count:
                flash(f"Uploaded {saved_count} file(s).", "success")
                return redirect(url_for("home"))

    flash("Choose a file or folder to upload.", "error")
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

    if not sync_url or not api:
        flash(
            "Syncthing is not configured. Update SYNCTHING_URL and "
            "SYNCTHING_API_KEY in .env.",
            "error",
        )
        return redirect(url_for("home"))

    try:
        response = requests.get(
            f"{sync_url.rstrip('/')}/rest/system/status",
            headers={"X-API-Key": api},
            verify=False,
            timeout=10,
        )
        response.raise_for_status()

        device_id = response.json().get("myID")

        if not device_id:
            raise RuntimeError("Syncthing did not return a device ID.")

        return render_template("device_id.html", device_id=device_id)

    except (requests.RequestException, RuntimeError, ValueError) as exc:
        app.logger.warning("Could not retrieve Syncthing device ID: %s", exc)
        flash(f"Failed to fetch Syncthing device ID: {exc}", "error")
        return redirect(url_for("home"))


@app.route("/converter", methods=["GET", "POST"])
def converter_page():
    if not require_login():
        return redirect(url_for("login"))

    if request.method == "POST":
        items = get_local_files()

        selected_file = request.form.get("filename", "")
        target_file = request.form.get("target_format", "").lower().lstrip(".")

        if not selected_file or not target_file:
            flash("Choose a file and an output format.", "error")
            return redirect(url_for("converter_page"))

        full_input_path = (SYNCED_FOLDER_PATH / selected_file).resolve()

        if not path_is_inside_sync_folder(full_input_path):
            abort(400, description="Invalid file path.")

        if not full_input_path.is_file():
            flash(
                "The selected file was not found locally. "
                "Wait for Syncthing to finish syncing, then try again.",
                "error",
            )
            return redirect(url_for("converter_page"))

        source_extension = full_input_path.suffix.lower().lstrip(".")

        try:
            if source_extension == "docx" and target_file == "pdf":
                output_path = converter.convert_docx_to_pdf(full_input_path)

            elif source_extension == "pdf" and target_file == "docx":
                output_path = converter.convert_pdf_to_docx(full_input_path)

            elif (
                source_extension in {"jpg", "jpeg", "png", "webp"}
                and target_file in {"jpg", "png", "webp"}
            ):
                format_map = {
                    "jpg": "JPEG",
                    "png": "PNG",
                    "webp": "WEBP",
                }

                output_path = converter.img_converter(
                    start_img=full_input_path,
                    end_img_extension=target_file,
                    file_format=format_map[target_file],
                )

            elif (
                source_extension
                in {"mp3", "wav", "mp4", "mkv", "mov", "avi", "m4a"}
                and target_file in {"mp3", "wav", "mp4", "mkv"}
            ):
                output_path = converter.convert_audio_and_video(
                    input_path=full_input_path,
                    output_ext=target_file,
                )

            else:
                flash(
                    f"Conversion from .{source_extension} to .{target_file} "
                    "is not supported.",
                    "error",
                )
                return redirect(url_for("converter_page"))

            flash(
                f"Conversion complete: {Path(output_path).name}",
                "success",
            )

        except (FileNotFoundError, ValueError, RuntimeError) as exc:
            flash(str(exc), "error")

        except Exception:
            app.logger.exception("Unexpected conversion error")
            flash(
                "Conversion failed unexpectedly. Check the container logs.",
                "error",
            )

        return redirect(url_for("home"))

    try:
       items = get_local_files()

    except (requests.RequestException, RuntimeError, ValueError) as exc:
        app.logger.warning("Could not load files for converter: %s", exc)
        flash(f"Could not load Syncthing files: {exc}", "error")
        items = []

    return render_template(
        "convert.html",
        files=items,
        demo_mode=DEMO_MODE,
    )


@app.route("/download/<path:filename>", methods=["GET"])
def download_file(filename):
    if not require_login():
        return redirect(url_for("login"))

    requested_file = (SYNCED_FOLDER_PATH / filename).resolve()

    if not path_is_inside_sync_folder(requested_file):
        abort(400, description="Invalid file path.")

    if not requested_file.is_file():
        return (
            f"File not found locally: {filename}. "
            "Wait for Syncthing to finish syncing.",
            404,
        )

    return send_from_directory(
        directory=str(SYNCED_FOLDER_PATH),
        path=filename,
        as_attachment=True,
        download_name=requested_file.name,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)