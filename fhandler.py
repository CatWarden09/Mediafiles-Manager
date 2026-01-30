import os
from PIL import Image

import ffmpeg
import config

from PySide6.QtCore import QObject, Signal

from functools import singledispatchmethod

from dotenv import load_dotenv

load_dotenv()

ALLOWED_IMAGE_FORMATS = [
    ".jpeg",
    ".jpg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".jfif",
    ".webp",
]
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


class FileScanner(QObject):
    # need to use signal in order for thumbnail creation work in a separate thread like in the main flow (first program launch)
    files_scanned = Signal(set)

    def __init__(self, db, fhandler):
        super().__init__()

        self.db = db
        self.fhandler = fhandler

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

        difference_found = []

        counter = self.count_all_files()
        print("Files counter = ", counter)

        saved_counter = config.get_files_count()

        # for the first program launch
        if saved_counter is None:
            config.save_files_count(counter)
        elif counter != saved_counter:
            config.save_files_count(counter)
            difference_found = self.get_files_difference()

        return difference_found

    def get_files_difference(self):
        root_folder = os.getenv("FOLDER_PATH")
        

        db_files = set(self.db.get_all_filepaths())
        current_files = set()

        for folder, subfolders, files in os.walk(root_folder):
            # create the new subfolders list for the os.walk without the thumbnails folder
            subfolders[:] = [
                subfolder
                for subfolder in subfolders
                if subfolder.lower() != "thumbnails"
            ]

            for filepath in files:
                current_files.add(
                    self.fhandler.normalize_filepath(os.path.join(folder, filepath))
                )

        new_files_paths = current_files - db_files
        deleted_files_paths = db_files - current_files

        difference_found = []
        if new_files_paths:
            self.update_files_list(new_files_paths)
            difference_found.append("new_files")
        if deleted_files_paths:
            print("Deleted files paths are", deleted_files_paths)

            for path in deleted_files_paths:
                self.db.delete_file_by_filepath(path)
            self.db.save_changes()

            difference_found.append("deleted_files")

        return difference_found

    # if the actual files counter > than the one saved in the .env, generate previews for the new files and update files list in the UI
    def update_files_list(self, new_files_paths):
        files_list = self.fhandler.clear_files_list(new_files_paths)
        if files_list:
            self.files_scanned.emit(new_files_paths)
    


# TODO add a check if the thumbnails folder already exists and skip these methods
# (for the future features in case user changes folder back to the previous one !- need to check if there are any changes in files)
# DONE add automatic audio thumbnail creation
# DONE add automatic tags creation for typical files (like images, videos etc.)
class FileHandler(QObject):
    progress = Signal(int, int)
    finished = Signal(str)
    thumb_created = Signal(str, str, str, list)

    def __init__(self, db):
        super().__init__()
        self.db = db

    def normalize_filepath(self, path):
        return os.path.abspath(os.path.normpath(path))

    # a decorator for "imitating" method overloading (to use different file sources like folder or files list)
    @singledispatchmethod
    def clear_files_list(self, files_source):
        raise TypeError("Некорректный список файлов")
    
    # separate cases - №1 for folder (first program launch)
    @clear_files_list.register(str)
    def _(self, folder: str):
        filtered_filepaths = []

        for current_folder, subfolders, files in os.walk(folder):
            # create the new subfolders list for the os.walk without the thumbnails folder
            subfolders[:] = [
                subfolder
                for subfolder in subfolders
                if subfolder.lower() != "thumbnails"
            ]

            # create the filtered by allowed formats file list
            for file in files:
                file_format = os.path.splitext(file)[1].lower()
                if file_format in ALLOWED_TYPES:
                    filtered_filepaths.append(
                        self.normalize_filepath(os.path.join(current_folder, file))
                    )

        return filtered_filepaths
    
    # separate cases - №2 for specific files lists (on new program launches, when new files are detected)
    @clear_files_list.register(set)
    def _(self, files_list: set):
        filtered_filepaths = []
        for file in files_list:
            file_format = os.path.splitext(file)[1].lower()
            if file_format in ALLOWED_TYPES:
                filtered_filepaths.append(self.normalize_filepath(file))

        return filtered_filepaths
    


    def create_thumbnails(self, filepaths):

        folder = config.get_files_folder_path()
        thumb_folder = config.get_thumb_folder_path()

        progress_counter = 0
        tags = []

        save_path = os.path.join(thumb_folder, "thumbnails")
        os.makedirs(save_path, exist_ok=True)

        img_thumb_size = 128, 128
        audio_thumb_file = os.path.join(
            config.assign_script_dir(), "icons", "audio.png"
        )

        for filepath in filepaths:

            filename = os.path.basename(filepath)
            file_format = os.path.splitext(filename)[1].lower()

            # this branch is needed for handling type definition (like if the file format is in image formats, then use Image, if in video formats, then use ffmpeg and so on)
            if file_format in ALLOWED_IMAGE_FORMATS:
                with Image.open(filepath) as img:
                    img.thumbnail(img_thumb_size)
                    thumb_filepath = os.path.join(
                        save_path, os.path.splitext(filename)[0] + ".png"
                    )
                    img.save(thumb_filepath)
                tags = ["Image"]

            elif file_format in ALLOWED_VIDEO_FORMATS:
                (
                    ffmpeg.input(
                        filepath,
                        ss=1,
                    )
                    .filter("scale", 512, -1)
                    .output(
                        os.path.join(save_path, os.path.splitext(filename)[0] + ".png"),
                        vframes=1,
                        n=None,
                        loglevel="quiet",
                    )
                    .run(cmd=config.get_ffmpeg_path())
                )
                thumb_filepath = os.path.join(
                    save_path, os.path.splitext(filename)[0] + ".png"
                )

                tags = ["Video"]

            elif file_format in ALLOWED_AUDIO_FORMATS:
                thumb_filepath = audio_thumb_file
                tags = ["Audio"]

            progress_counter += 1
            self.progress.emit(progress_counter, len(filepaths))
            self.thumb_created.emit(filename, filepath, thumb_filepath, tags)

        self.finished.emit(folder)
