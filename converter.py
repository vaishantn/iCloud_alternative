import os
import platform
import subprocess

import imageio_ffmpeg
from pdf2docx import parse
from PIL import Image


class Converter:
    def __init__(self):
        self.ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

        # Docker supplies /data/syncthing.
        # Native Windows use can set this environment variable to a local folder.
        self.output_dir = os.environ.get(
            "SYNCED_FOLDER_PATH",
            r"C:\Users\vaish\Syncthing_save_folder",
        )

        os.makedirs(self.output_dir, exist_ok=True)

    def _get_output_path(self, input_path, extension):
        filename_only = os.path.basename(str(input_path))
        base_name = os.path.splitext(filename_only)[0]
        clean_ext = extension.lower().lstrip(".")

        output_path = os.path.join(
            self.output_dir,
            f"{base_name}.{clean_ext}",
        )

        counter = 1
        while os.path.exists(output_path):
            output_path = os.path.join(
                self.output_dir,
                f"{base_name}_{counter}.{clean_ext}",
            )
            counter += 1

        return output_path

    def img_converter(self, start_img, end_img_extension, file_format):
        start = str(start_img)

        if not os.path.isfile(start):
            raise FileNotFoundError(f"Image file not found: {start}")

        target_ext = end_img_extension.lower().lstrip(".")

        if target_ext not in {"jpg", "png", "webp"}:
            raise ValueError("Image format must be jpg, png, or webp.")

        output_path = self._get_output_path(start, target_ext)

        with Image.open(start) as img:
            if target_ext == "jpg":
                img.convert("RGB").save(output_path, "JPEG")
            else:
                img.save(output_path, file_format)

        return output_path

    def convert_docx_to_pdf(self, input_path, output_path=None):
        """Convert DOCX to PDF on native Windows when Word is installed."""

        if platform.system() != "Windows":
            raise RuntimeError(
                "DOCX-to-PDF conversion is unavailable in Docker/Linux because it "
                "requires Microsoft Word on Windows. Run the app natively on Windows "
                "to use this conversion."
            )

        try:
            from docx2pdf import convert
        except ImportError as exc:
            raise RuntimeError(
                "DOCX-to-PDF conversion requires the optional docx2pdf package. "
                "Install it in native Windows with: pip install docx2pdf"
            ) from exc

        source = str(input_path)

        if not os.path.isfile(source):
            raise FileNotFoundError(f"DOCX file not found: {source}")

        if output_path is None:
            output_path = self._get_output_path(source, "pdf")

        try:
            convert(source, str(output_path))
        except Exception as exc:
            raise RuntimeError(
                "DOCX-to-PDF conversion failed. Confirm Microsoft Word is installed "
                "and that the document is not already open in Word."
            ) from exc

        return str(output_path)

    def convert_pdf_to_docx(self, input_path, output_path=None):
        """Convert a PDF to DOCX; supported in Docker."""

        source = str(input_path)

        if not os.path.isfile(source):
            raise FileNotFoundError(f"PDF file not found: {source}")

        if output_path is None:
            output_path = self._get_output_path(source, "docx")

        try:
            parse(source, str(output_path))
        except Exception as exc:
            raise RuntimeError(
                "PDF-to-DOCX conversion failed. The PDF may be damaged, encrypted, "
                "or use a layout that cannot be converted."
            ) from exc

        return str(output_path)

    def convert_audio_and_video(self, input_path, output_ext):
        start = str(input_path)

        if not os.path.isfile(start):
            raise FileNotFoundError(f"Media file not found: {start}")

        target_ext = output_ext.lower().lstrip(".")

        if target_ext not in {"mp3", "wav", "mp4", "mkv"}:
            raise ValueError("Media format must be mp3, wav, mp4, or mkv.")

        output_path = self._get_output_path(start, target_ext)

        result = subprocess.run(
            [
                self.ffmpeg,
                "-y",
                "-i",
                start,
                output_path,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"FFmpeg conversion failed:\n{result.stderr[-1500:]}"
            )

        return output_path