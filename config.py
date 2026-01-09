import sys
import os

VERSION = "0.7"


def assign_script_dir():
    if getattr(sys, "frozen", False):
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    return script_dir


env_path = os.path.join(assign_script_dir(), ".env")


def save_to_env(key, value):
    with open(env_path, "a", encoding="utf-8") as f:
        f.write(f"\n{key}={value}")
