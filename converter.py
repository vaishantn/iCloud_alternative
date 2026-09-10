from PIL import Image
from docx2pdf import convert
import os
from pdf2docx import parse
import subprocess
import imageio_ffmpeg


class Converter:
    def __init__(self):
        self.ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()


    @staticmethod
    def img_converter(start_img, end_img_extension, file_format):
        start = str(start_img)
        n = os.path.splitext(start)[0]
        img = Image.open(start)
        img.convert("RGB").save(f"{n}{end_img_extension}", f"{file_format}")

    @staticmethod
    def doc_converter(filename, target_format):
        ans = str(target_format)
        if ans.lower() == 'docx':
            start = str(filename)
            n = os.path.splitext(start)[0]
            parse(start, f"{n}.docx")
        else:
            start = str(filename)
            n = os.path.splitext(start)[0]
            convert(start, f"{n}.pdf")

    def convert_audio_and_video(self,input_path, output_ext):
        start = str(input_path)
        n = os.path.splitext(start)[0]
        cmd = [self.ffmpeg, "-y", "-i", input_path,f"{n}{output_ext}"]
        subprocess.run(cmd, check=True)