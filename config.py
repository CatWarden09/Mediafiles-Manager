import sys, os, json

from dotenv import load_dotenv

VERSION = "0.9.8-beta"
DEBUG = False


def assign_script_dir():
    if getattr(sys, "frozen", False):
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    return script_dir


FFMPEG_PATH = os.path.join(assign_script_dir(), "ffmpeg.exe")


def get_ffmpeg_path() -> str:
    return FFMPEG_PATH


env_path = os.path.join(assign_script_dir(), ".env")


def save_to_env(key, value):
    with open(env_path, "a", encoding="utf-8") as f:
        f.write(f"\n{key}={value}")


counter_path = os.path.join(assign_script_dir(), "fhandler_data", "counter.json")


def save_files_count(value: int):
    os.makedirs(os.path.dirname(counter_path), exist_ok=True)

    with open(counter_path, "w", encoding="utf-8") as f:
        json.dump({"FILES_COUNT": value}, f)


def get_files_count():
    if not os.path.exists(counter_path):
        return None

    with open(counter_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("FILES_COUNT")


APP_ICON_PATH = os.path.join(assign_script_dir(), "icons", "app_icon.ico")


def get_app_icon_path():
    return APP_ICON_PATH


def get_files_folder_path():
    load_dotenv()
    return os.getenv("FOLDER_PATH")

def get_thumb_folder_path():
    load_dotenv()
    return os.getenv("THUMB_FOLDER_PATH")