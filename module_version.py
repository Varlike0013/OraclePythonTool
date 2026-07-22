#module_version.py

import json
import os
import shutil
import sys
import subprocess
import tempfile
from packaging.version import Version

VERSION = "0.1.0"

# 远程配置路径
REMOTE_BASE = r"\\10.240.144.99\f\LeiHuang\varlike"
REMOTE_CONFIG_PATH = r"\\10.240.144.99\f\LeiHuang\varlike\saves.json"

def get_remote_version():
    """
    从远程共享路径的 JSON 文件中读取 app_version 字段。
    若读取失败，返回 None。
    """
    try:
        with open(REMOTE_CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("app_version")
    except Exception:
        return None
def get_local_version():
    """返回本地版本号"""
    return VERSION
def check_version_status():
    """
    检查版本状态，返回 (status_code, message)
    status_code:
        0: 本地已是最新
        1: 发现新版本
        -1: 获取远程版本失败（网络/路径错误、格式错误等）
    """
    local_ver = get_local_version()
    remote_ver = get_remote_version()

    if remote_ver is None:
        return -1, "未获取到云端版本号，请检查网络或路径设置"

    try:
        if Version(remote_ver) > Version(local_ver):
            return 1, f"发现新版本 {remote_ver}，当前版本 {local_ver}"
        else:
            return 0, f"已经是最新版本 {local_ver}"
    except Exception:
        return -1, "版本号格式错误，无法比较"
def perform_update():
    # 检查远程路径是否存在
    if not os.path.exists(REMOTE_BASE):
        return False, "远程更新目录不存在"

    # 确定本地程序目录
    if getattr(sys, 'frozen', False):
        local_dir = os.path.dirname(sys.executable)
    else:
        local_dir = os.getcwd()

    # 在程序目录下创建临时文件夹
    temp_update_dir = os.path.join(local_dir, "_Varlike_update_temp")
    # 如果已存在，先删除（避免残留）
    if os.path.exists(temp_update_dir):
        shutil.rmtree(temp_update_dir, ignore_errors=True)
    os.makedirs(temp_update_dir, exist_ok=True)

    exe_name = "Varlike.exe"  # 固定 exe 名称

    EXCLUDE_FILES = ["saves.json"]
    EXCLUDE_DIRS = ["_internal/instantclient_19_31"]

    try:
        for root, dirs, files in os.walk(REMOTE_BASE):
            rel_path = os.path.relpath(root, REMOTE_BASE).replace('\\', '/')
            # 跳过排除目录
            skip = any(rel_path.startswith(exclude_dir) for exclude_dir in EXCLUDE_DIRS)
            if skip:
                dirs[:] = []
                continue
            target_dir = os.path.join(temp_update_dir, rel_path)
            os.makedirs(target_dir, exist_ok=True)
            for file in files:
                if file in EXCLUDE_FILES:
                    continue
                src = os.path.join(root, file)
                dst = os.path.join(target_dir, file)
                shutil.copy2(src, dst)
    except Exception as e:
        shutil.rmtree(temp_update_dir, ignore_errors=True)
        return False, f"复制文件到临时目录失败: {e}"

    # 生成批处理脚本
    batch_path = os.path.join(temp_update_dir, "update.bat")

    if getattr(sys, 'frozen', False):
        # 打包环境：自动执行批处理并退出
        batch_content = f"""@echo off
        ping 127.0.0.1 -n 3 > nul
        echo 正在更新文件...
        xcopy /E /Y /I "{temp_update_dir}" "{local_dir}"
        :: 备份旧 exe 并替换（若存在 _new 则使用）
        move /Y "{os.path.join(local_dir, exe_name)}" "{os.path.join(local_dir, exe_name)}.old" 2>nul
        move /Y "{os.path.join(temp_update_dir, exe_name)}" "{os.path.join(local_dir, exe_name)}" 2>nul
        :: 清理临时目录
        rmdir /S /Q "{temp_update_dir}"
        :: 删除旧备份
        del "{os.path.join(local_dir, exe_name)}.old" 2>nul
        start "" "{os.path.join(local_dir, exe_name)}"
        del "%~f0"
        """
        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        # 启动批处理（隐藏窗口），然后退出当前进程
        subprocess.Popen([batch_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return True, "更新已启动，程序即将重启。"
    else:
        # 开发环境：仅生成批处理文件，提示用户手动执行
        batch_content = f"""@echo off
        echo 请手动运行此批处理以更新文件。
        echo 将复制临时目录内容到 {local_dir}
        pause
        xcopy /E /Y /I "{temp_update_dir}" "{local_dir}"
        echo 更新完成，按任意键退出。
        pause
        """
        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        return True, f"更新文件已准备就绪，请手动运行批处理文件:\n{batch_path}"