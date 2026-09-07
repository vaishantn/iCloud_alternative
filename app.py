from flask import Flask
import requests
import urllib3

app = Flask(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SYNCTHING_URL = "192.168.0.19:8384"
SYNCTHING_API_KEY = "JTjVyLVXZivtzeJCk65XAjp4K9UU37N9"

headers = {
    "X-API-KEY": SYNCTHING_API_KEY
}

@app.route('/', methods=['GET', 'POST'])
def home():
    return "Hello, World!"


if __name__ == "__main__":
    app.run(debug=True)