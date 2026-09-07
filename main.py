import requests
import urllib3

SYNCTHING_URL = "http://127.0.0.1:8384"
API_KEY = "iYFR5ef9KvinxMCk924ZnnWGKwm4ReEJ"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {
    "X-API-KEY": API_KEY
}

response = requests.get(f"{SYNCTHING_URL}/rest/system/status", headers=headers, verify=False)

if response.status_code == 200:
    print('connected')
    print(response.json())

else:
    print('faild')
