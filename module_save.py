#module_save.py
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
    },
    "app_version": "0.0.0",
}
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            # 合并默认配置，修补缺失或类型错误的字段
            merged = _merge_dicts(DEFAULT_CONFIG, user_config)
            return merged
        except (json.JSONDecodeError, Exception):
            # 文件损坏或格式错误，重建默认配置
            save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
def save_app_version(version):
    """
    将当前应用版本号保存到配置文件中。
    :param version: 版本号字符串，如 "1.0.0"
    """
    config = load_config()
    config["app_version"] = version
    save_config(config)
def _merge_dicts(default, user):
    """
    递归合并字典，确保 user 中拥有 default 的所有键，且类型一致。
    若 user 中缺少字段或类型不匹配，则从 default 中补充/替换。
    保留 user 中的额外字段。
    """
    for key, default_val in default.items():
        if key not in user:
            user[key] = default_val
        elif isinstance(default_val, dict):
            if not isinstance(user[key], dict):
                user[key] = default_val
            else:
                _merge_dicts(default_val, user[key])
        # 对于非字典类型，若类型不一致，用默认值替换
        elif not isinstance(user[key], type(default_val)):
            user[key] = default_val
    return user
