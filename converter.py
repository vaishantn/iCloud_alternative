import subprocess
import sys

# Uses subprocess to call pip on the current interpreter
subprocess.check_call(
    [sys.executable, "-m", "pip", "install", "imageio_ffmpeg"]
)

from PIL import Image
from docx2pdf import convert
import os
from pdf2docx import parse
import subprocess
import imageio_ffmpeg

def img_converter(start_img, end_img_extension, file_format):
    start = str(start_img)
    n = os.path.splitext(start)[0]
    img = Image.open(start)
    img.convert("RGB").save(f"{n}{end_img_extension}", f"{file_format}")

def doc_converter(filename, to_PDF_or_to_docx):
    ans = str(to_PDF_or_to_docx)
    if ans.lower() == 'docx':
        start = str(filename)
        n = os.path.splitext(start)[0]
        convert(start, f"{n}.pdf")
    else:
        start = str(filename)
        n = os.path.splitext(start)[0]
        parse(start, f"{n}.docx")

ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

def convert_audio_and_video(input_path, output_path):
    cmd = [ffmpeg, "-y", "-i", input_path, output_path]
    subprocess.run(cmd, check=True)