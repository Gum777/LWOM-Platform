import sys
from pathlib import Path

def get_base_dir() -> Path:
    """程序所在目录：打包后是 exe ，开发时为 backend 文件夹"""
    if getattr(sys, "frozen",False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
DATA_DIR = BASE_DIR / "data"
DB_FILE = DATA_DIR / "lwom.db"
