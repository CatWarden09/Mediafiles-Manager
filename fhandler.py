import os, glob
from PIL import Image

allowed_types = [".jpeg", ".jpg", ".png", ".gif", ".bmp", ".tiff", ".jfif"]



class FileHandler:
    @staticmethod
    def clear_files_list(folder):
        filtered = []

        for f in os.listdir(folder):
            if os.path.splitext(f)[1].lower() in allowed_types:
                filtered.append({"filename": f, "file_path": os.path.join(folder, f)})

        print(filtered)
        # filtered = {
        #     f for f in files_list if os.path.splitext(f)[1].lower() in allowed_types
        # }
        return filtered

    @staticmethod
    def set_image_thumbnail(folder):
        save_path = os.path.join(folder, "thumbnails")
        os.makedirs(save_path, exist_ok= True)

        size = 128,128
        for file in os.listdir(folder):
            if os.path.splitext(file)[1].lower() in allowed_types:
                with Image.open(os.path.join(folder, file)) as img:
                    img.thumbnail(size)
                    thumb_file = os.path.join(save_path, os.path.splitext(file)[0] + ".png")
                    img.save(thumb_file)