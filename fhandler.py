import os
from PIL import Image

import ffmpeg
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
    def __init__(self, db):
        self.db = db

    def count_all_files(self):
        folder = os.getenv("FOLDER_PATH")

        counter = 0

        for _, subfolders, files in os.walk(folder):
            # create the new subfolders list for the os.walk without the thumbnails folder
            subfolders[:] = [
                subfolder
                for subfolder in subfolders
                if subfolder.lower() != "thumbnails"
            ]
            counter += len(files)
        return counter

    def compare_files_count(self):
        counter = self.count_all_files()

        # for the first program launch
        if os.getenv("FILES_COUNT") is None:
            config.save_to_env("FILES_COUNT", counter)
        elif counter != os.getenv("FILES_COUNT"):
            self.get_files_difference()

    def get_files_difference(self):
        folder = os.getenv("FOLDER_PATH")

        db_files = set(self.db.get_all_filepaths())
        current_files = set()

        for folder, subfolders, files in os.walk(folder):
            # create the new subfolders list for the os.walk without the thumbnails folder
            subfolders[:] = [
                subfolder
                for subfolder in subfolders
                if subfolder.lower() != "thumbnails"
            ]

            for filepath in files:
                current_files.add(os.path.join(folder, filepath))

        new_files_paths = current_files - db_files
        deleted_files_paths = db_files - current_files

        if new_files_paths:
            self.update_files_list(new_files_paths)
        if deleted_files_paths:
            self.db.delete_file_by_filepath(deleted_files_paths)

    # if the actual files counter != the one saved in the .env, generate previews for the new files and update files list in the UI
    def update_files_list(self, new_files_paths):
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


