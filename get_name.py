from datetime import datetime

import requests
import urllib3


urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)


class Get_Name:
    @staticmethod
    def get_folders(SYNCTHING_URL, API_KEY):
        headers = {"X-API-Key": API_KEY}

        main_url = f"{SYNCTHING_URL}/rest/system/config"

        response = requests.get(
            main_url,
            headers=headers,
            verify=False,
            timeout=10,
        )

        return_items = []

        if response.status_code != 200:
            print("Failed to connect:", response.status_code)
            return return_items

        print("Connected")

        config = response.json()
        folders = config.get("folders", [])

        for folder in folders:
            # Use the actual Syncthing folder ID.
            folder_id = folder.get("id")
            folder_name = folder.get("label") or folder_id

            if not folder_id:
                continue

            browse_url = f"{SYNCTHING_URL}/rest/db/browse"

            browse_response = requests.get(
                browse_url,
                headers=headers,
                params={"folder": folder_id},
                verify=False,
                timeout=10,
            )

            if browse_response.status_code != 200:
                print(
                    f"Could not browse {folder_name}: "
                    f"{browse_response.status_code}"
                )
                continue

            items = browse_response.json()

            for item in items:
                item_type = item.get("type")
                name = item.get("name")
                size = item.get("size", 0)
                raw_time = item.get("modTime")

                if not name:
                    continue

                if raw_time:
                    try:
                        dt = datetime.fromisoformat(
                            raw_time.replace("Z", "+00:00")
                        )

                        readable_time = dt.strftime(
                            "%b %d, %Y at %I:%M %p"
                        )

                    except ValueError:
                        readable_time = raw_time

                else:
                    readable_time = "Unknown time"

                # Newer Syncthing versions may send type as an integer.
                is_file = item_type in {
                    "FILE_INFO_TYPE_FILE",
                    1,
                }

                is_folder = item_type in {
                    "FILE_INFO_TYPE_DIRECTORY",
                    2,
                }

                if is_file:
                    print(
                        f"Folder: {folder_name} | "
                        f"File: {name} ({round(size / (1024 * 1024), 2)} bytes)"
                    )

                    return_items.append(
                        {
                            "folder_name": folder_name,
                            "folder_id": folder_id,
                            "file_name": name,
                            "relative_path": name,
                            "type": "file",
                            "size": round(size / (1024 * 1024), 2),
                            "time": readable_time,
                        }
                    )

                elif is_folder:
                    print(
                        f"Folder: {folder_name} | "
                        f"Directory: {name}/"
                    )

                    return_items.append(
                        {
                            "folder_name": folder_name,
                            "folder_id": folder_id,
                            "file_name": name,
                            "relative_path": name,
                            "type": "folder",
                            "size": "-",
                            "time": readable_time,
                        }
                    )

                else:
                    print(
                        f"Skipping unknown item type: "
                        f"{item_type} for {name}"
                    )

        return return_items