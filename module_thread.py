# module_thread.py
import threading

# 全局任务字典：task_id -> threading.Thread 实例
_running_tasks = {}
_root = None

def init(root):
    """初始化线程模块，传入 Tkinter 根窗口"""
    global _root
    _root = root
# ---------- 线程管理 ---------
def start_task(task_id, target, args=(), kwargs=None, callback=None):
    """
    启动一个后台线程任务。
    :param task_id:  任务唯一标识符（字符串）
    :param target:   要执行的函数
    :param args:     位置参数（元组）
    :param kwargs:   关键字参数（字典）
    :param callback: 任务完成后的回调函数，接收 (result, error) 两个参数，
                     result 为 target 的返回值，error 为异常信息（若发生异常）
    :return: True 表示成功启动，False 表示任务已存在（正在运行）
    """
    if task_id in _running_tasks and _running_tasks[task_id].is_alive():
        return False

    def wrapper():
        try:
            result = target(*args, **(kwargs or {}))
            if callback:
                _root.after(0, callback, result, None)
        except Exception as e:
            if callback:
                _root.after(0, callback, None, str(e))
        finally:
            # 任务结束后从字典中移除
            if task_id in _running_tasks:
                del _running_tasks[task_id]

    t = threading.Thread(target=wrapper, daemon=True)
    _running_tasks[task_id] = t
    t.start()
    return True
def is_running(task_id):
    """检查指定任务是否正在运行"""
    return task_id in _running_tasks and _running_tasks[task_id].is_alive()
def remove_task(task_id):
    """
    手动从任务字典中移除任务（仅在任务已结束或无需等待时使用）。
    注意：这不会终止线程，只是清理记录，通常由 start_task 自动完成。
    """
    if task_id in _running_tasks:
        del _running_tasks[task_id]
        return True
    return False