import main
import os

VERSION = "0.1"


env_path = os.path.join(main.assign_script_dir(), ".env")

def save_to_env(key, value):
    with open(env_path, "a") as f:
        f.write(f"\n{key}={value}")