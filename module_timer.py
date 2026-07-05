# module_timer.py
import tkinter as tk

# 定时器状态变量
_after_id = None
_is_running = False
_interval = 0          # 秒
_callback = None       # 要执行的刷新函数
_root = None           # 主窗口 Tk 对象

def init_timer(root, callback):
    """
    初始化定时器，传入主窗口对象和刷新回调函数
    :param root: tk.Tk 实例
    :param callback: 要定时执行的函数
    """
    global _root, _callback
    _root = root
    _callback = callback

def set_interval(seconds):
    """设置刷新间隔（秒）"""
    global _interval
    _interval = seconds

def start(interval=None):
    """
    启动定时刷新
    :param interval: 可选，指定间隔（秒），若不传则使用当前 _interval
    """
    global _is_running, _after_id, _interval
    if interval is not None:
        _interval = interval
    if _interval <= 0:
        return
    stop()  # 先停止现有定时器
    _is_running = True
    _loop()

def stop():
    """停止定时刷新"""
    global _is_running, _after_id
    _is_running = False
    if _after_id is not None and _root is not None:
        _root.after_cancel(_after_id)
        _after_id = None

def _loop():
    """内部循环函数，由 after 调度"""
    global _after_id, _is_running, _interval, _root, _callback
    if not _is_running or _interval <= 0:
        return
    # 执行回调
    if _callback is not None:
        try:
            _callback()
        except Exception as e:
            print(f"定时刷新回调执行出错: {e}")
    # 调度下一次
    _after_id = _root.after(int(_interval * 1000), _loop)

def is_running():
    """返回当前是否在运行"""
    return _is_running

def get_interval():
    """获取当前间隔"""
    return _interval