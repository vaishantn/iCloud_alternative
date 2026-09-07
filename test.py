from datetime import datetime
import requests
import urllib3

SYNCTHING_URL = "https://192.168.0.19:8384"
API_KEY = "JTjVyLVXZivtzeJCk65XAjp4K9UU37N9"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {
    "X-API-Key": API_KEY
}
class Get_Name:
    
    def get_folders():
        main_url = f"{SYNCTHING_URL}/rest/system/config"
        response = requests.get(main_url, headers=headers, verify=False)
        return_items = []
        if response.status_code == 200:
            print('connected')
            config = response.json()
            folders = config.get('folders', [])

            f_list = []
            for folder in folders:
                f_list.append({           
                    "id": folder.get('id'),
                    "label": folder.get('label') or folder.get('id'),
                    "path": folder.get('path')
                })

            for folder in f_list:
                # Corrected: match 'id' to API parameter and 'label' to display name
                folder_id = folder['id']
                folder_name = folder['label']

                url = f"{SYNCTHING_URL}/rest/db/browse?folder={folder_id}"
                response = requests.get(url, headers=headers, verify=False)
                items = response.json()

                for item in items:
                    item_type = item.get('type')
                    name = item.get('name')
                    size = item.get('size', 0)
                    raw_time = item.get('modTime')
                    
                    if raw_time:
                        dt = datetime.fromisoformat(raw_time)
                        readable_time = dt.strftime("%b %d, %Y at %I:%M %p")
                    else:
                        readable_time = "Unknown time"
                    
                    if item_type == "FILE_INFO_TYPE_FILE":
                        print(f"Folder: {folder_name} | File: {name} ({size} bytes) - Modified: {readable_time}")
                        result = f"Folder: {folder_name} | File: {name} ({size} bytes) - Modified: {readable_time}"
                        return_items.append(result)
                    elif item_type == "FILE_INFO_TYPE_DIRECTORY":
                        print(f"Folder: {folder_name} | Directory: {name}/ - Modified: {readable_time}")
                        result = f"Folder: {folder_name} | Directory: {name}/ - Modified: {readable_time}"
                        return_items.append(result)
        else:
            print('failed', response.status_code)
        return return_items

# Add this call at the bottom so the code executes
if __name__ == "__main__":
    Get_Name.get_folders()