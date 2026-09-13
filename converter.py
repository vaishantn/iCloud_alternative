import os
import subprocess
from docx2pdf import convert
import imageio_ffmpeg
from pdf2docx import parse
from PIL import Image


class Converter:

    def __init__(self):
        self.ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        self.output_dir = r"C:\Users\vaish\Syncthing_save_folder"

    def _get_output_path(self, input_path, extension):
        # Extract just the filename without folders (e.g., "photo.png" -> "photo")
        filename_only = os.path.basename(str(input_path))
        base_name = os.path.splitext(filename_only)[0]

        # Clean extension formatting (removes leading dot if present)
        clean_ext = extension.lstrip(".")

        # Combine folder, base name, and clean extension
        return os.path.join(self.output_dir, f"{base_name}.{clean_ext}")

    def img_converter(self, start_img, end_img_extension, file_format):
        start = str(start_img)
        output_path = self._get_output_path(start, end_img_extension)

        with Image.open(start) as img:
            img.convert("RGB").save(output_path, f"{file_format}")

    def doc_converter(self, filename, target_format):
        ans = str(target_format).lower().lstrip(".")
        start = str(filename)

        if ans == "docx":
            output_path = self._get_output_path(start, "docx")
            parse(start, output_path)
        else:
            output_path = self._get_output_path(start, "pdf")
            convert(start, output_path)

    def convert_audio_and_video(self, input_path, output_ext):
        start = str(input_path)
        output_path = self._get_output_path(start, output_ext)

        cmd = [self.ffmpeg, "-y", "-i", start, output_path]
        subprocess.run(cmd, check=True)