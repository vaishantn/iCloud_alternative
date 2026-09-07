from flask import Flask, render_template
from get_name import Get_Name
import urllib3

app = Flask(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sync_url = "http://192.168.0.19:8384"
api = "JTjVyLVXZivtzeJCk65XAjp4K9UU37N9"



@app.route('/', methods=['GET', 'POST'])
def home():
    items = Get_Name.get_folders(SYNCTHING_URL=sync_url, API_KEY=api)
    return render_template('index.html', files=items)


if __name__ == "__main__":
    app.run(debug=True)