import os


allowed_types = [".jpeg", ".png", ".jpg", ".jfif"]


class FileHandler:

    def clear_files_list(self, files_list):
        filtered = [
            f for f in files_list if os.path.splitext(f)[1].lower() in allowed_types
        ]
        return filtered
