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
                # most probably the file_path here and the dictionary is no longer needed since everything is in the DB
        return filtered

    # TODO merge with video thubmnail method and refactor so it works with filtered file list from the method above (can pass it from main)
    # because now we have 3 separate methods that do similar job with the same list at the same time

    # TODO move the thumbnails folder to the program dir
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
        # TODO add ffmpeg search in system\program dir
        FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"
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
                    .run(cmd=FFMPEG_PATH)
                )
                file_path = os.path.join(folder, file)
                preview_path = os.path.join(
                    save_path, os.path.splitext(file)[0] + ".png"
                )
                self.db.save_to_database(file, file_path, preview_path)


class DatabaseHandler:
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
        filepath TEXT NOT NULL UNIQUE,
        previewpath TEXT NOT NULL
        )              
        """
        )

        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS Tags(
        id INTEGER PRIMARY KEY,
        tagname TEXT NOT NULL UNIQUE)
        """
        )

        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS Files_tags(
        file_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        PRIMARY KEY (file_id, tag_id),
        FOREIGN KEY (file_id) REFERENCES Files(id),
        FOREIGN KEY (tag_id) REFERENCES Tags(id)
        )
        """
        )

        self.save_changes()

    def connect_to_database(self):

        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON;")

    def save_changes(self):
        self.connection.commit()

    def close_connection(self):
        self.connection.close()

    def save_to_database(self, file_name: str, file_path: str, preview_path: str):
        self.cursor.execute(
            "INSERT INTO Files (filename, filepath, previewpath) VALUES (?, ?, ?)",
            (file_name, file_path, preview_path),
        )

    def save_tag_to_database(self, tag_name: str):
        self.cursor.execute(
            "INSERT INTO Tags (tagname) VALUES (?)",
            (tag_name,),
        )
        self.save_changes()

    def delete_tag_from_database(self, tag_hame: str):
        self.cursor.execute("DELETE FROM Tags WHERE tagname = ?", (tag_hame,))
        self.save_changes()

    def get_all_tagnames(self):
        self.cursor.execute("SELECT tagname FROM Tags")
        tags_list = self.cursor.fetchall()
        return tags_list

    # check if the tag is already in the table and return True if the DB query returns !=Null, return False otherwise
    def tag_exists(self, tag_name: str) -> bool:
        self.cursor.execute("SELECT 1 FROM Tags WHERE tagname = ?", (tag_name,))
        return self.cursor.fetchone() is not None

    def get_previewpath(self, file):
        self.cursor.execute("SELECT previewpath FROM Files WHERE filename = ?", (file,))
        previewpath = self.cursor.fetchone()
        # print(previewpath)
        return previewpath

    def get_all_filenames(self):
        self.cursor.execute("SELECT filename FROM Files")
        files_list = self.cursor.fetchall()
        return files_list
