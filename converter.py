import os
import subprocess

from docx2pdf import convert
import imageio_ffmpeg
from pdf2docx import parse
from PIL import Image


class Converter:
    def __init__(self):
        self.ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

        # Hard-coded for your current Windows machine
        self.output_dir = r"C:\Users\vaish\Syncthing_save_folder"

        # Makes sure the folder exists before conversion starts
        os.makedirs(self.output_dir, exist_ok=True)

    def _get_output_path(self, input_path, extension):
        filename_only = os.path.basename(str(input_path))
        base_name = os.path.splitext(filename_only)[0]
        clean_ext = extension.lower().lstrip(".")

        output_path = os.path.join(
            self.output_dir,
            f"{base_name}.{clean_ext}",
        )

        # Prevent accidental overwriting when a converted file already exists
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
            # JPG/JPEG cannot contain transparency.
            if target_ext == "jpg":
                img.convert("RGB").save(output_path, "JPEG")
            else:
                img.save(output_path, file_format)

        return output_path

    def doc_converter(self, filename, target_format):
        start = str(filename)

        if not os.path.isfile(start):
            raise FileNotFoundError(f"Document file not found: {start}")

        source_ext = os.path.splitext(start)[1].lower()
        target_ext = target_format.lower().lstrip(".")

        if target_ext == "docx":
            if source_ext != ".pdf":
                raise ValueError(
                    "PDF-to-DOCX conversion requires a .pdf input file."
                )

            output_path = self._get_output_path(start, "docx")
            parse(start, output_path)
            return output_path

        if target_ext == "pdf":
            if source_ext not in {".docx", ".doc"}:
                raise ValueError(
                    "DOCX-to-PDF conversion requires a .docx or .doc input file."
                )

            output_path = self._get_output_path(start, "pdf")
            convert(start, output_path)
            return output_path

        raise ValueError("Document target format must be pdf or docx.")

    def convert_audio_and_video(self, input_path, output_ext):
        start = str(input_path)

        if not os.path.isfile(start):
            raise FileNotFoundError(f"Media file not found: {start}")

        target_ext = output_ext.lower().lstrip(".")

        if target_ext not in {"mp3", "wav", "mp4", "mkv"}:
            raise ValueError(
                "Media format must be mp3, wav, mp4, or mkv."
            )

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