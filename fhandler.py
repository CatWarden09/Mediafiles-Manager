import os
from PIL import Image

import ffmpeg
import sqlite3
import config

from dotenv import load_dotenv

load_dotenv()

ALLOWED_IMAGE_FORMATS = [".jpeg", ".jpg", ".png", ".gif", ".bmp", ".tiff", ".jfif"]
ALLOWED_VIDEO_FORMATS = [
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
ALLOWED_AUDIO_FORMATS = [
    ".mp3",
    ".wav",
    ".flac",
    ".aac",
    ".ogg",
    ".opus",
    ".m4a",
    ".wma",
    ".aiff",
    ".alac",
]

ALLOWED_TYPES = ALLOWED_IMAGE_FORMATS + ALLOWED_VIDEO_FORMATS + ALLOWED_AUDIO_FORMATS

class FileScanner:
    def count_all_files():
        folder = os.getenv("FOLDER_PATH")
        
        counter = 0
        
        for _, subfolders, files in os.walk(folder):
            # create the new subfolders list for the os.walk without the thumbnails folder
            subfolders[:] = [subfolder for subfolder in subfolders if subfolder.lower() != "thumbnails"] 
            counter += len(files)
        return counter


    def save_files_count(counter):
        pass

    def compare_files_count():
        pass

        # if the actual files counter if > than the one saved in the .env, generate previews for the new files and update files list in the UI
    def update_files_list():
        pass


# TODO add a check if the thumbnails folder already exists and skip these methods
# (for the future features in case user changes folder back to the previous one !- need to check if there are any changes in files)
# TODO add automatic audio thumbnail creation
# TODO add automatic tags creation for typical files (like images, videos etc.)
class FileHandler:

    def __init__(self, db):
        self.db = db

    def create_audio_thumbnail(self, folder):
        thumb_file = os.path.join(config.assign_script_dir(), "icons", "audio.png")
        print(folder)
        for item in folder:
            filename = item["filename"]
            file_path = item["file_path"]
            if os.path.splitext(filename)[1].lower() in ALLOWED_AUDIO_FORMATS:
                self.db.save_to_database(filename, file_path, thumb_file)
                self.db.save_current_item_tags(filename, ["Audio"])

    def clear_files_list(self, folder):
        filtered = []

        for f in os.listdir(folder):
            if os.path.splitext(f)[1].lower() in ALLOWED_TYPES:
                filtered.append({"filename": f, "file_path": os.path.join(folder, f)})
                # TODO deprecate the dictionary
                # most probably the file_path here and the dictionary is no longer needed since everything is in the DB
        self.create_audio_thumbnail(filtered)
        return filtered

    # TODO merge with video thubmnail method and refactor so it works with filtered file list from the method above (can pass it from main)
    # because now we have 3 separate methods that do similar job with the same list at the same time

    def create_image_thumbnail(self, folder):
        save_path = os.path.join(folder, "thumbnails")
        os.makedirs(save_path, exist_ok=True)

        size = 128, 128
        for file in os.listdir(folder):
            if os.path.splitext(file)[1].lower() in ALLOWED_IMAGE_FORMATS:
                with Image.open(os.path.join(folder, file)) as img:
                    img.thumbnail(size)
                    thumb_file = os.path.join(
                        save_path, os.path.splitext(file)[0] + ".png"
                    )
                    img.save(thumb_file)
                file_path = os.path.join(folder, file)
                self.db.save_to_database(file, file_path, thumb_file)
                self.db.save_current_item_tags(file, ["Image"])

    def create_video_thumbnail(self, folder):
        save_path = os.path.join(folder, "thumbnails")
        # TODO add ffmpeg search in system\program dir
        
        for file in os.listdir(folder):

            if os.path.splitext(file)[1].lower() in ALLOWED_VIDEO_FORMATS:
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
                    .run(cmd=config.get_ffmpeg_path())
                )
                file_path = os.path.join(folder, file)
                preview_path = os.path.join(
                    save_path, os.path.splitext(file)[0] + ".png"
                )
                self.db.save_to_database(file, file_path, preview_path)
                self.db.save_current_item_tags(file, ["Video"])


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
        filename TEXT NOT NULL UNIQUE,
        filepath TEXT NOT NULL UNIQUE,
        previewpath TEXT NOT NULL,
        description TEXT
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
        FOREIGN KEY (file_id) REFERENCES Files(id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES Tags(id) ON DELETE CASCADE
        )
        """
        )

        self.cursor.execute(
            """INSERT OR IGNORE INTO Tags(tagname) VALUES
            ("Audio"),
            ("Video"),
            ("Image")
            """
        )

        self.save_changes()

    def connect_to_database(self):

        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()

        # need to activate foreign_keys on every DB connection
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
        rows = self.cursor.fetchall()
        return [r[0] for r in rows]

    # Get all tag names assigned to a file:
    # 1. Start from Tags table
    # 2. Join Files_tags to find tag-file links
    # 3. Join Files to know which file each tag belongs to
    # 4. Filter by file name
    def get_current_item_tags(self, item):
        self.cursor.execute(
            """
            SELECT t.tagname
            FROM Tags t
            
            JOIN Files_tags ft on ft.tag_id = t.id
            JOIN Files f ON ft.file_id = f.id
            WHERE f.filename = ?

        """,
            (item,),
        )
        rows = self.cursor.fetchall()
        return [r[0] for r in rows]

    def save_current_item_tags(self, item, tags_list):
        for tag in tags_list:
            self.cursor.execute(
                """INSERT OR IGNORE INTO Files_tags (file_id, tag_id)
                SELECT f.id, t.id
                FROM Files f
                JOIN Tags t ON t.tagname = ?
                WHERE f.filename = ?
                
                """,
                (tag, item),
            )
        self.save_changes()

    # Delete all tag-file pairs where ids of tags and files are equal to the method arguments
    def delete_current_item_tags(self, item, tags_list):
        for tag in tags_list:
            self.cursor.execute(
                """
                DELETE FROM Files_tags
                WHERE file_id = (SELECT id FROM Files WHERE filename = ?)
                AND tag_id = (SELECT id FROM Tags WHERE tagname = ?)

                """,
                (item, tag),
            )
        self.save_changes()

    # check if the tag is already in the table and return True if the DB query returns !=Null, return False otherwise
    def tag_exists(self, tag_name: str) -> bool:
        self.cursor.execute("SELECT 1 FROM Tags WHERE tagname = ?", (tag_name,))
        return self.cursor.fetchone() is not None

    def get_previewpath(self, file):
        self.cursor.execute("SELECT previewpath FROM Files WHERE filename = ?", (file,))
        row = self.cursor.fetchone()
        # print(previewpath)

        return row[0]

    def get_all_filenames(self):
        self.cursor.execute("SELECT filename FROM Files")
        rows = self.cursor.fetchall()
        return [r[0] for r in rows]

    def get_filepath(self, file):
        self.cursor.execute("SELECT filepath FROM Files where filename = ?", (file,))
        row = self.cursor.fetchone()
        return row[0]

    def get_files_by_tags(self, tags_list):
        if not tags_list:
            return []
        placeholders = ", ".join(["?"] * len(tags_list))
        query = f"""
            SELECT f.filename
            FROM Files f
            JOIN Files_tags ft on ft.file_id = f.id
            JOIN Tags t ON ft.tag_id = t.id
            WHERE t.tagname IN ({placeholders})
            GROUP BY f.id
            HAVING COUNT(DISTINCT t.tagname) = ?
        """
        params = tags_list + [len(tags_list)]
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        return [r[0] for r in rows]

    def get_files_by_text(self, description):
        query = "SELECT filename FROM Files WHERE description LIKE ? OR filename LIKE ?"
        self.cursor.execute(query, (f"%{description}%", f"%{description}%"))
        rows = self.cursor.fetchall()
        return [r[0] for r in rows]

    def update_file_description(self, file, description: str):
        self.cursor.execute(
            "UPDATE Files SET description = ? WHERE filename = ?", (description, file)
        )
        self.save_changes()

    def get_file_description(self, file):
        self.cursor.execute("SELECT description FROM Files WHERE filename = ?", (file,))
        row = self.cursor.fetchone()
        return row[0]
