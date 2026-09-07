from flask import Flask, render_template, request, redirect, url_for
from get_name import Get_Name
import urllib3
import os
from werkzeug.utils import secure_filename
app = Flask(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sync_url = "http://192.168.0.19:8384"
api = "JTjVyLVXZivtzeJCk65XAjp4K9UU37N9"

SYNCED_FOLDER_PATH = "C:/Users/vaish/Syncthing_save_folder"


@app.route('/')
def home():
    items = Get_Name.get_folders(SYNCTHING_URL=sync_url, API_KEY=api)
    return render_template('index.html', files=items)

@app.route('/upload', methods=['POST'])
def upload():
    return render_template('file_add.html')

@app.route('/upload/complete', methods=['POST'])
def upload_complete():
    # Fixed typo: changed 'seleceted_file' to 'selected_file'
    if 'selected_file' in request.files:
        file = request.files['selected_file']
        if file.filename != '':
            filename = secure_filename(file.filename)
            file_path= os.path.join(SYNCED_FOLDER_PATH, filename)
            file.save(file_path)
            print(f'done {file.filename}')
            return redirect('/')

    # Fixed typo: changed 'seleceted_folder' to 'selected_folder'
    if 'selected_folder' in request.files:
        files = request.files.getlist('selected_folder')
        if files and files[0].filename != '':
            for file in files:
                    # Normalize path for the OS
                    clean_path = os.path.normpath(file.filename)    
                    safe_parts = [
                secure_filename(part) for part in clean_path.split(os.sep)
                ]
                    relative_safe_path = os.path.join(*safe_parts)
                    file_path= os.path.join(SYNCED_FOLDER_PATH, relative_safe_path)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    file.save(file_path)
        return redirect('/')
            
if __name__ == "__main__":
    app.run(debug=True)