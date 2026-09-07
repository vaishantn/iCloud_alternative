from datetime import datetime
import requests
import urllib3



urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Get_Name:

    @staticmethod

    def get_folders(SYNCTHING_URL, API_KEY):
        headers = {"X-API-Key": API_KEY}
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
                        result = {}
                        result['folder_name'] = folder_name
                        result['file_name'] = name
                        result['size'] = size
                        result['time'] = readable_time

                        return_items.append(result)
                    elif item_type == "FILE_INFO_TYPE_DIRECTORY":
                        print(f"Folder: {folder_name} | Directory: {name}/ - Modified: {readable_time}")
                        result = f"Folder: {folder_name} | Directory: {name}/ - Modified: {readable_time}"
                        return_items.append(result)
        else:
            print('failed', response.status_code)
        return return_items


