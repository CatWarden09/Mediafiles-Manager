import os
from PIL import Image

import ffmpeg
import sqlite3
import config

allowed_image_formats = [".jpeg", ".jpg", ".png", ".gif", ".bmp", ".tiff", ".jfif"]
allowed_video_formats = [
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".webm",
    ".flv",
    ".wmv",
    ".mpeg",
    ".mpg",
    ".m4v",
]

allowed_types = allowed_image_formats + allowed_video_formats


# TODO add a check if the thumbnails folder already exists and skip these methods (for the future features in case user changes folder back to the previous one !- need to check if there are any changes in files)
class FileHandler:

    def __init__(self, db):
        self.db = db

    def clear_files_list(self, folder):
        filtered = []

        for f in os.listdir(folder):
            if os.path.splitext(f)[1].lower() in allowed_types:
                filtered.append({"filename": f, "file_path": os.path.join(folder, f)})

        return filtered

    # TODO merge with video thubmnail method and refactor so it works with filtered file list from the method above (can pass it from main)
    # because now we have 3 separate methods that do similar job with the same list at the same time
    def create_image_thumbnail(self, folder):
        save_path = os.path.join(folder, "thumbnails")
        os.makedirs(save_path, exist_ok=True)

        size = 128, 128
        for file in os.listdir(folder):
            if os.path.splitext(file)[1].lower() in allowed_image_formats:
                with Image.open(os.path.join(folder, file)) as img:
                    img.thumbnail(size)
                    thumb_file = os.path.join(
                        save_path, os.path.splitext(file)[0] + ".png"
                    )
                    img.save(thumb_file)
                file_path = os.path.join(folder, file)
                self.db.save_to_database(file, file_path, thumb_file)

    def create_video_thumbnail(self, folder):
        save_path = os.path.join(folder, "thumbnails")
        for file in os.listdir(folder):

            if os.path.splitext(file)[1].lower() in allowed_video_formats:
                (
                    ffmpeg.input(
                        os.path.join(folder, file),
                        ss=1,
                    )
                    .filter("scale", 512, -1)
                    .output(
                        os.path.join(save_path, os.path.splitext(file)[0] + ".png"),
                        vframes=1,
                        n=None,
                    )
                    .run()
                )
            file_path = os.path.join(folder, file)
            preview_path = os.path.join(save_path, os.path.splitext(file)[0] + ".png")
            self.db.save_to_database(file, file_path, preview_path)


class DatabaseHanlder:
    def __init__(self):

        folder_path = os.path.join(config.assign_script_dir(), "fhandler_data")
        os.makedirs(folder_path, exist_ok=True)
        self.db_path = os.path.join(folder_path, "files.db")

        self.connect_to_database()

        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS Files (
        id INTEGER PRIMARY KEY,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        previewpath TEXT NOT NULL
        )              
        """
        )

        self.save_changes()

    def connect_to_database(self):

        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()

    def save_changes(self):
        self.connection.commit()

    def close_connection(self):
        self.connection.close()

    def save_to_database(self, file_name: str, file_path: str, preview_path: str):
        self.cursor.execute(
            "INSERT INTO Files (filename, filepath, previewpath) VALUES (?, ?, ?)",
            (file_name, file_path, preview_path),
        )
