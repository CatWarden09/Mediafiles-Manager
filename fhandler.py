import os
from PIL import Image

import ffmpeg


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


class FileHandler:
    @staticmethod
    def clear_files_list(folder):
        filtered = []

        for f in os.listdir(folder):
            if os.path.splitext(f)[1].lower() in allowed_types:
                filtered.append({"filename": f, "file_path": os.path.join(folder, f)})

        # print(filtered)
        # filtered = {
        #     f for f in files_list if os.path.splitext(f)[1].lower() in allowed_types
        # }
        return filtered

    @staticmethod
    def create_image_thumbnail(folder):
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

    @staticmethod
    def create_video_thumbnail(folder):
        save_path = os.path.join(folder, "thumbnails")
        for file in os.listdir(folder):

            if os.path.splitext(file)[1].lower() in allowed_video_formats:
                (
                    ffmpeg.input(os.path.join(folder, file), ss=1)
                    .filter("scale", 512, -1)
                    .output(
                        os.path.join(save_path, os.path.splitext(file)[0] + ".png"),
                        vframes=1,
                    )
                    .run()
                )
