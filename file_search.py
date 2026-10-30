from datetime import datetime
from pathlib import Path

class FileSearch:
    def __init__(self, folder_path):
        self.folder_path = Path(folder_path).expanduser().resolve()
        self.folder_path.mkdir(parents=True, exist_ok=True)

    def list_files(self):
        files = []

        for path in sorted(self.folder_path.rglob("*")):
            if not path.is_file():
                continue

            try:
                relative_path = path.relative_to(self.folder_path).as_posix()

                stat = path.stat()

                files.append({
                    "folder_name": "Syncthing Files",
                    "file_name": path.name,
                    "relative_path": relative_path,
                    "type": "file",
                    "size": stat.st_size,
                    "time": datetime.fromtimestamp(
                        stat.st_mtime
                    ).strftime("%Y-%m-%d %H:%M"),
                })
            except OSError:
                continue

        return files

    def search(self, item):

        if not isinstance(item, str):
            raise TypeError("querry must be string")
        item = item.strip().casefold()
        files = self.list_files()

        if not item:
            return files

        return [
            file for file in files
            if item in file["file_name"].casefold()
            or item in file["relative_path"].casefold()
        ] 