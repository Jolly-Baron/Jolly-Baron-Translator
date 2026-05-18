import os
import json
from datetime import datetime

MODELS_DIR = "Model"
N_CTX = 32768
N_THREADS = 8
N_BATCH = 2048          # размер батча для обработки промпта
SETTINGS_FILE = "settings.json"

def log(message: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        log(f"Error loading settings: {e}")
    return {}

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        log(f"Error saving settings: {e}")