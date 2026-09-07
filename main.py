import requests

SYNCTHING_URL = "http://127.0.0.1:8384"
API_KEY = "iYFR5ef9KvinxMCk924ZnnWGKwm4ReEJ"

headers = {
    "X-API-KEY": API_KEY
}

response = requests.get(f"{SYNCTHING_URL}/rest/system/status", headers=headers)

if response.status_code == 200:
    print('connected')
    print(response.json())

else:
    print('faild')
