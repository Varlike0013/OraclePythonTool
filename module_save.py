import json
import os

CONFIG_FILE = "saves.json"
DEFAULT_CONFIG = {
    "user": {
        "last_user_emp": "",
        "last_user_pws": "",
        "remember_me": False,
    },
    "settings": {
        "window": {"width": 960, "height": 540, "x": 300, "y": 200, "maximized": False},
        "misc": {"auto_refresh_interval": 0, "auto_refresh_enabled":False,"show_confirmation_dialog": False,"floor_B2":True,"floor_B3":True,"floor_B4":True},
    }
}
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

