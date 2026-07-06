import tkinter as tk
from tkinter import ttk, messagebox,simpledialog
import traceback
import os
import re
import sys
import module_oracle
import module_login
import module_save
import module_timer
import csv
import time
import threading

# ---------- 全局变量（用于跨函数共享）----------
content_frame = None         # 内容区域框架
status_label = None          # 底部状态栏 Label
user_label = None            # 最底部用户信息栏
current_tree = None          # 当前表格树
current_columns = None       # 当前表格表头
#流程相关
current_dip_route = None
current_pack_route = None
current_rework_route = None
#服务器IP
server_ip = None

# ---------- 资源载入 ---------
def resource_path(relative_path):
    """获取打包后资源的绝对路径"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
def copy_to_clipboard(text):
    root.clipboard_clear()
    root.clipboard_append(text)
def split_to_quoted_string(s):
    """输入 "a b c" 输出 "'a','b','c'"""
    parts = s.split()
    return ','.join([f"'{p}'" for p in parts]) if parts else ''
def clean_sn_input(sn_input):
    """分割输入，并去除每个部分的引号"""
    parts = re.split(r'[,\s]+', sn_input)
    return [p.strip().strip("'\"") for p in parts if p.strip()]
# ---------- 通用输入ui --------
def update_status_safe(text):
    """线程安全地更新状态栏"""
    if threading.current_thread() is threading.main_thread():
        status_label.config(text=text)
    else:
        root.after(0, lambda: status_label.config(text=text))
def _ui_input_one(title, confirm_callback,
                  label="输入:", btn_text="确定", warning_msg="请输入内容"):
    """
    通用单输入界面
    :param title:             标题文本
    :param confirm_callback:  点击确定时的回调函数，接收 (value)
    :param label:             输入框前的标签文本
    :param btn_text:          确定按钮上的文本
    :param warning_msg:       输入框为空时的警告提示
    """
    global content_frame
    for widget in content_frame.winfo_children():
        widget.destroy()

    center_frame = tk.Frame(content_frame)
    center_frame.pack(expand=True)

    tk.Label(center_frame, text=title, font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

    tk.Label(center_frame, text=label).grid(row=1, column=0, padx=5, pady=5, sticky="e")
    entry = tk.Entry(center_frame)
    entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    def on_confirm():
        value = entry.get().strip()
        if not value:
            messagebox.showwarning("提示", warning_msg)
            return
        confirm_callback(value)

    btn = tk.Button(center_frame, text=btn_text, command=on_confirm)
    btn.grid(row=2, column=0, columnspan=2, pady=10)
def _ui_input_two(title, confirm_callback,
                  label_1="输入1:", label_2="输入2:",
                  btn_text="确定", warning_msg="请至少输入一个条件"):
    """
    通用双输入界面
    :param title:             标题文本
    :param confirm_callback:  点击确定时的回调函数，接收 (value1, value2)
    :param label_1:           第一个输入框前的标签文本
    :param label_2:           第二个输入框前的标签文本
    :param btn_text:          确定按钮上的文本
    :param warning_msg:       两个输入框均为空时的警告提示
    """
    global content_frame
    for widget in content_frame.winfo_children():
        widget.destroy()

    center_frame = tk.Frame(content_frame)
    center_frame.pack(expand=True)

    tk.Label(center_frame, text=title, font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

    tk.Label(center_frame, text=label_1).grid(row=1, column=0, padx=5, pady=5, sticky="e")
    entry1 = tk.Entry(center_frame)
    entry1.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    tk.Label(center_frame, text=label_2).grid(row=2, column=0, padx=5, pady=5, sticky="e")
    entry2 = tk.Entry(center_frame)
    entry2.grid(row=2, column=1, padx=5, pady=5, sticky="w")

    def on_confirm():
        val1 = entry1.get().strip()
        val2 = entry2.get().strip()
        if not val1 and not val2:
            messagebox.showwarning("提示", warning_msg)
            return
        confirm_callback(val1, val2)

    btn = tk.Button(center_frame, text=btn_text, command=on_confirm)
    btn.grid(row=3, column=0, columnspan=2, pady=10)
def _ui_input_three(title, confirm_callback,
                    label_1="输入1:", label_2="输入2:", label_3="输入3:",
                    btn_text="确定", warning_msg="请至少输入一个条件"):
    """
    通用三输入界面
    :param title:             标题文本
    :param confirm_callback:  点击确定时的回调函数，接收 (value1, value2, value3)
    :param label_1:           第一个输入框前的标签文本
    :param label_2:           第二个输入框前的标签文本
    :param label_3:           第三个输入框前的标签文本
    :param btn_text:          确定按钮上的文本
    :param warning_msg:       三个输入框均为空时的警告提示
    """
    global content_frame
    for widget in content_frame.winfo_children():
        widget.destroy()

    center_frame = tk.Frame(content_frame)
    center_frame.pack(expand=True)

    tk.Label(center_frame, text=title, font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

    tk.Label(center_frame, text=label_1).grid(row=1, column=0, padx=5, pady=5, sticky="e")
    entry1 = tk.Entry(center_frame)
    entry1.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    tk.Label(center_frame, text=label_2).grid(row=2, column=0, padx=5, pady=5, sticky="e")
    entry2 = tk.Entry(center_frame)
    entry2.grid(row=2, column=1, padx=5, pady=5, sticky="w")

    tk.Label(center_frame, text=label_3).grid(row=3, column=0, padx=5, pady=5, sticky="e")
    entry3 = tk.Entry(center_frame)
    entry3.grid(row=3, column=1, padx=5, pady=5, sticky="w")

    def on_confirm():
        val1 = entry1.get().strip()
        val2 = entry2.get().strip()
        val3 = entry3.get().strip()
        if not val1 and not val2 and not val3:
            messagebox.showwarning("提示", warning_msg)
            return
        confirm_callback(val1, val2, val3)

    btn = tk.Button(center_frame, text=btn_text, command=on_confirm)
    btn.grid(row=4, column=0, columnspan=2, pady=10)
def ui_select_two_routes(columns, rows, on_selected, title="请选择恰好两个流程"):
    """
    通用路由选择界面，强制用户选择恰好两个路由（一个D开头，一个P开头），
    选择完成后通过回调返回 (dip, pack)。

    :param columns:      列名列表（如 ['ROUTE_ID', 'ROUTE_NAME']）
    :param rows:         数据行列表，每行为 (ROUTE_ID, ROUTE_NAME)
    :param on_selected:  回调函数，接收 (dip, pack) 两个参数
    :param title:        界面标题
    """
    global content_frame, status_label

    # 清空内容区域
    for widget in content_frame.winfo_children():
        widget.destroy()

    if not rows:
        tk.Label(content_frame, text="没有查询到流程信息", font=("Arial", 12)).pack(pady=20)
        status_label.config(text="无流程信息")
        return

    # ---------- 居中容器 ----------
    center_frame = tk.Frame(content_frame)
    center_frame.place(relx=0.5, rely=0.5, anchor="center")

    # 标题
    tk.Label(center_frame, text=title, font=("Arial", 12, "bold")).pack(pady=10)

    # 流程列表容器
    list_frame = tk.Frame(center_frame)
    list_frame.pack(pady=10)

    # 存储每个流程的 (BooleanVar, route_id, route_name)
    route_vars = []

    for idx, row in enumerate(rows):
        route_id = row[0] if row else ""
        route_name = row[1] if len(row) > 1 else ""
        var = tk.BooleanVar(value=False)

        row_frame = tk.Frame(list_frame)
        row_frame.pack(anchor="w", pady=2)

        cb = tk.Checkbutton(row_frame, variable=var,
                            command=lambda v=var: on_check(v))
        cb.pack(side=tk.LEFT)

        lbl = tk.Label(row_frame, text=f"{route_id} - {route_name}")
        lbl.pack(side=tk.LEFT, padx=5)

        route_vars.append((var, route_id, route_name))

    def on_check(clicked_var):
        """限制选中数量不超过2个"""
        selected = sum(1 for v, _, _ in route_vars if v.get())
        if selected > 2:
            clicked_var.set(False)
            messagebox.showwarning("选择限制", "只能选择两个流程，不能超过两个")
            selected = sum(1 for v, _, _ in route_vars if v.get())
        status_label.config(text=f"已选择 {selected} 个流程（必须恰好选2个）")

    def on_confirm():
        selected_routes = [(r_id, r_name) for v, r_id, r_name in route_vars if v.get()]
        if len(selected_routes) != 2:
            messagebox.showinfo("提示", "必须恰好选择两个流程")
            return

        # --- 新分配逻辑：P开头 → pack，另一个 → dip ---
        pack_candidates = [name for _, name in selected_routes if name.upper().startswith('P')]
        if len(pack_candidates) != 1:
            messagebox.showerror("分配失败", "请选择恰好一个P开头的流程，另一个为非P开头")
            return
        pack = pack_candidates[0]
        # 另一个给 dip
        dip = [name for _, name in selected_routes if name != pack][0]  # 剩余那个

        # 调用回调，传递选中的 dip 和 pack
        on_selected(dip, pack)

    # 确认按钮
    btn = tk.Button(center_frame, text="确认选择", command=on_confirm, width=12)
    btn.pack(pady=15)

    status_label.config(text="请选择恰好两个流程（D开头和P开头各一个）")
def ui_table_tree(cols, rows, menu_builder=None):
    """
    通用表格显示函数，支持自定义右键菜单（通过 menu_builder）。
    :param cols: 列名列表
    :param rows: 数据行列表
    :param menu_builder: 可选，自定义菜单构建函数，接收参数 (menu, tree, columns, row_id, col_index, col_name, values, cell_value, first_col_value)
                         如果不提供，则使用默认菜单（复制 + 查看流程）。
    """
    global content_frame, status_label, current_tree, current_columns

    # 清空内容区域
    for widget in content_frame.winfo_children():
        widget.destroy()

    if not rows:
        label = tk.Label(content_frame, text="没有查询到数据")
        label.pack(pady=20)
        current_time = time.strftime("%H:%M:%S")
        status_label.config(text=f" 查询无记录 | 部分右键功能需要登陆 | 执行时间: {current_time}")
        return

    # 创建表格框架
    frame = tk.Frame(content_frame)
    frame.pack(fill=tk.BOTH, expand=True)

    v_scrollbar = ttk.Scrollbar(frame)
    v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    h_scrollbar = ttk.Scrollbar(frame, orient=tk.HORIZONTAL)
    h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    tree = ttk.Treeview(frame, columns=cols, show="headings",
                        yscrollcommand=v_scrollbar.set,
                        xscrollcommand=h_scrollbar.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    current_tree = tree
    current_columns = cols

    v_scrollbar.config(command=tree.yview)
    h_scrollbar.config(command=tree.xview)

    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=100, anchor="center")

    for row in rows:
        tree.insert("", tk.END, values=row)

    current_time = time.strftime("%H:%M:%S")
    status_label.config(text=f" 查询结果：共 {len(rows)} 条记录 | 部分右键功能需要登陆 | 执行时间: {current_time}")

    # ---------- 右键菜单 ----------
    def show_popup(event):
        row_id = current_tree.identify_row(event.y)
        col_id = current_tree.identify_column(event.x)
        if not row_id or not col_id:
            return
        col_index = int(col_id[1:]) - 1
        col_name = current_columns[col_index]
        values = current_tree.item(row_id, 'values')
        cell_value = values[col_index] if col_index < len(values) else ""
        first_col_value = values[0] if values else None

        menu = tk.Menu(root, tearoff=0)
        if menu_builder:
            # 使用自定义菜单构建器
            menu_builder(menu, current_tree, current_columns, row_id, col_index, col_name, values, cell_value, first_col_value)
        else:
            # 默认菜单：复制当前值 + 查看当前值
            menu.add_command(label=f"复制 {col_name}", command=lambda: copy_to_clipboard(cell_value))
            menu.add_command(label="查看当前值", command=lambda:show_cell_value(cell_value,col_name))
        menu.post(event.x_root, event.y_root)
    # ---------- 左键双击 ----------
    def on_double_click(event):
        row_id = current_tree.identify_row(event.y)
        col_id = current_tree.identify_column(event.x)
        if not row_id or not col_id:
            return
        col_index = int(col_id[1:]) - 1
        col_name = current_columns[col_index]
        values = current_tree.item(row_id, 'values')
        cell_value = values[col_index] if col_index < len(values) else ""
        # 默认：显示单元格值
        show_cell_value(cell_value,col_name)
    current_tree.bind("<Double-1>", on_double_click)
    current_tree.bind("<Button-3>", show_popup)
def show_cell_value(value,title="单元格值"):
    """
    弹窗显示单元格内容，支持复制（多行文本框，可选中）
    :param value: 要显示的内容
    """
    if not value:
        value = "(空)"
    win = tk.Toplevel(root)
    win.title(title)
    win.geometry("400x250")
    win.transient(root)
    win.grab_set()

    # 相对于主窗口居中
    root.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() - 400) // 2
    y = root.winfo_y() + (root.winfo_height() - 250) // 2
    win.geometry(f"+{x}+{y}")

    # 多行文本框
    text = tk.Text(win, wrap=tk.WORD, height=10, width=50)
    text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
    text.insert(tk.END, value)
    text.config(state=tk.DISABLED)  # 只读，但可选中复制
def show_notification(message):
    """
    在屏幕右下角显示通知窗口（多行信息）
    :param message: 要显示的消息文本（可包含换行符）
    """
    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.geometry("300x120")
    win.attributes("-topmost", True)
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = screen_width - 320
    y = screen_height - 200
    win.geometry(f"+{x}+{y}")
    frame = tk.Frame(win, bg="#e6f3ff", bd=2, relief=tk.RIDGE)
    frame.pack(fill=tk.BOTH, expand=True)
    icon = tk.Label(frame, text="❓", font=("Arial", 20), bg="#e6f3ff")
    icon.pack(side=tk.LEFT, padx=10, pady=10, anchor="n")
    text_label = tk.Label(frame, text=message, font=("微软雅黑", 10), bg="#e6f3ff",
                          wraplength=240, justify=tk.LEFT, anchor="nw")
    text_label.pack(side=tk.LEFT, padx=5, pady=10, fill=tk.BOTH, expand=True)
    btn_close = tk.Button(frame, text="✕", command=win.destroy, bd=0, bg="#e6f3ff", fg="#666", font=("Arial", 10))
    btn_close.pack(side=tk.RIGHT, padx=5, pady=5, anchor="n")
    win.after(8000, win.destroy)  # 8秒后自动关闭
    win.bind("<Button-1>", lambda e: win.destroy())
# ---------- 问题处理功能  ----------
def query_issue(notify=False):
    """
    查询问题记录，显示表格，并自定义右键菜单（包含筛选、排序、回复OK等）
    :param notify: 是否启用通知
    """
    global content_frame, status_label
    try:
        columns, rows = module_oracle.fetch_rework_records()
    except Exception as e:
        messagebox.showerror("查询错误", str(e))
        return
    if not rows:
        ui_table_tree(columns, [])
        return
    if notify:
        config = module_save.load_config()
        show_dialog = config.get('settings', {}).get('misc', {}).get('show_confirmation_dialog', False)
        if show_dialog:
            max_row = max(rows, key=lambda r: r[0])
            line = max_row[1] if len(max_row) > 1 else ""
            problem = max_row[2] if len(max_row) > 2 else ""
            reason = max_row[3] if len(max_row) > 3 else ""
            requirement = max_row[4] if len(max_row) > 4 else ""
            reporter = max_row[6] if len(max_row) > 6 else ""

            info_lines = [
                f"线别: {line}",
                f"问题描述: {problem}",
                f"提交原因: {reason}",
                f"产线要求: {requirement}",
                f"提报人: {reporter}"
            ]
            detail = "\n".join(info_lines)
            if len(detail) > 200:
                detail = detail[:200] + "..."

            msg = f"发现 {len(rows)} 条新记录\n{detail}"
            show_notification(msg)
    # 自定义菜单构建器
    FORMAT_COPY_COLUMNS = ['SERIAL_NUMBER']
    def custom_menu(menu, tree, columns, row_id, col_index, col_name, values, cell_value, first_col_value):
        menu.add_command(label=f"复制 {col_name}", command=lambda: copy_to_clipboard(cell_value))
        menu.add_command(label="查看当前值", command=lambda: show_cell_value(cell_value,col_name))
        menu.add_command(label=f"筛选 '{cell_value}'", command=lambda: filter_by_column(col_name, cell_value, tree, columns))
        menu.add_separator()
        if col_name in FORMAT_COPY_COLUMNS:
            menu.add_command(label=f"格式复制 {format_copy_match(cell_value)}", command=lambda:copy_to_clipboard(format_copy_match(cell_value)))
            menu.add_command(label="格式查询", command=lambda:query_match(cell_value))
        # 登录后功能
        if module_login.is_logined():
            menu.add_separator()
            menu.add_command(label="回复OK", command=lambda idx=first_col_value: review_question(idx, module_login.current_user,"OK"))
            menu.add_command(label="回复", command=lambda idx=first_col_value: review_question(idx, module_login.current_user))
    ui_table_tree(columns, rows, menu_builder=custom_menu)
def query_match(str_value):
    # 检测是否同时包含 SN 和 BGA 模式
    if re.search(r'SN\s*:', str_value, re.I) and re.search(r'BGA\s*:', str_value, re.I):
        query_format_sn_bga(format_copy_SN_BGA(str_value))
    elif re.search(r'SN\s*:', str_value, re.I) and re.search(r'PCB\s*:', str_value, re.I):
        query_format_sn_ppid(format_copy_SN_PCB(str_value))
    else:
        query_format_sn(format_copy_sn(str_value))
def query_format_sn_bga(sql_where):
    msg,columns,rows = module_oracle.fetch_format_sn_bga(sql_where)
    if msg == "OK":
        ui_table_tree(columns,rows)
    else:
        messagebox.showerror("失败", msg)
def query_format_sn_ppid(sql_where):
    msg,columns,rows = module_oracle.fetch_format_sn_ppid(sql_where)
    if msg == "OK":
        ui_table_tree(columns,rows)
    else:
        messagebox.showerror("失败", msg)
def query_format_sn(sql_where):
    msg,columns,rows = module_oracle.fetch_format_sn(sql_where)
    if msg == "OK":
        ui_table_tree(columns,rows)
    else:
        messagebox.showerror("失败", msg)
def format_copy_match(str_value):
    # 检测是否同时包含 SN 和 BGA 模式
    if re.search(r'SN\s*:', str_value, re.I) and re.search(r'BGA\s*:', str_value, re.I):
        return format_copy_SN_BGA(str_value)
    elif re.search(r'SN\s*:', str_value, re.I) and re.search(r'PCB\s*:', str_value, re.I):
        return format_copy_SN_PCB(str_value)
    else:
        return format_copy_sn(str_value)
def format_copy_sn(str_value):
    """
    将字符串按空格和换行分割，生成 SQL IN 子句。
    例如输入 "abc def ghi" 输出 "SERIAL_NUMBER IN ('abc','def','ghi')"
    """
    if not str_value:
        return ""
    # 按任意空白字符（空格、换行、制表符等）分割
    parts = re.split(r'\s+', str_value.strip())
    parts = [p for p in parts if p]  # 过滤空字符串

    if not parts:
        return ""
    # 去重并保留顺序
    unique_parts = list(dict.fromkeys(parts))
    # 生成 IN 子句
    values = "','".join(unique_parts)
    return f"SERIAL_NUMBER IN ('{values}')"
def format_copy_SN_PCB(str_value):
    """
    解析输入字符串中的 SN 和 PCB 值，生成 SQL 条件语句。
    支持格式：SN:xxx PCB:yyy 或 SN:xxx,PCB:yyy 等（以空格或逗号分隔）。
    示例输入：
        "SN:260675765830855 BGA:612352010U351410 SN:260675765830263 BGA:5CC705060U121402"
    输出：
        "STRSMTSN IN ('260675765830855','260675765830263') OR PCB_QRCODE IN ('612352010U351410','5CC705060U121402')"
    """
    if not str_value:
        return ""
    # 提取所有 SN 和 BGA 值（不区分大小写）
    sn_matches = re.findall(r'SN\s*:\s*([^\s,;]+)', str_value, re.IGNORECASE)
    pcb_matches = re.findall(r'PCB\s*:\s*([^\s,;]+)', str_value, re.IGNORECASE)
    # 去重并保留顺序（用 dict.fromkeys 保持顺序）
    sn_list = list(dict.fromkeys(sn_matches))
    pcb_list = list(dict.fromkeys(pcb_matches))
    conditions = []
    if sn_list:
        sn_values = "', '".join(sn_list)
        conditions.append(f"STRSMTSN IN ('{sn_values}')")
    if pcb_list:
        pcb_list = "', '".join(pcb_list)
        conditions.append(f"PCB_QRCODE IN ('{pcb_list}')")
    if not conditions:
        return ""
    return " OR ".join(conditions)
def format_copy_SN_BGA(str_value):
    """
    解析输入字符串中的 SN 和 BGA 值，生成 SQL 条件语句。
    支持格式：SN:xxx BGA:yyy 或 SN:xxx,BGA:yyy 等（以空格或逗号分隔）。
    示例输入：
        "SN:260675765830855 BGA:612352010U351410 SN:260675765830263 BGA:5CC705060U121402"
    输出：
        "SERIAL_NUMBER IN ('260675765830855','260675765830263') OR ITEM_PART_SN IN ('612352010U351410','5CC705060U121402')"
    """
    if not str_value:
        return ""
    # 提取所有 SN 和 BGA 值（不区分大小写）
    sn_matches = re.findall(r'SN\s*:\s*([^\s,;]+)', str_value, re.IGNORECASE)
    bga_matches = re.findall(r'BGA\s*:\s*([^\s,;]+)', str_value, re.IGNORECASE)
    # 去重并保留顺序（用 dict.fromkeys 保持顺序）
    sn_list = list(dict.fromkeys(sn_matches))
    bga_list = list(dict.fromkeys(bga_matches))
    conditions = []
    if sn_list:
        sn_values = "', '".join(sn_list)
        conditions.append(f"SERIAL_NUMBER IN ('{sn_values}')")
    if bga_list:
        bga_values = "', '".join(bga_list)
        conditions.append(f"ITEM_PART_SN IN ('{bga_values}')")
    if not conditions:
        return ""
    return " OR ".join(conditions)
def filter_by_column(col_name, value, tree, columns):
    """示例：根据列值过滤（实际应重新查询数据库）"""
    try:
        columns, rows = module_oracle.fetch_ECS_SN_REWORK_col_value(col_name,value)
    except Exception as e:
        messagebox.showerror("查询错误", str(e))
        return
def review_question(record_id,user,reply=None):
    """
    处理问题回复
    :param record_id: 记录ID（第一列值）
    :param user: 当前用户
    :param reply: 回复内容，若为 None 则弹出输入框让用户输入
    """
    if record_id is None:
        messagebox.showwarning("警告", "无法获取记录索引")
        return
    if reply is None:
        reply = simpledialog.askstring("输入回复", "请输入回复内容：", parent=root)
        if not reply:  # 用户取消或输入为空
            return
    if not messagebox.askyesno("确认", f"确定要将记录 [{record_id}] 标记为 [{reply}]  吗？"):
        return
    success, msg = module_oracle.update_question_status(record_id, reply, user)
    if success:
        messagebox.showinfo("成功", msg)
        query_issue()  # 刷新
    else:
        messagebox.showerror("错误", f"更新失败: {msg}")
def query_setting():
    global content_frame, status_label

    # 清空内容区域
    for widget in content_frame.winfo_children():
        widget.destroy()

    setting_frame = tk.Frame(content_frame)
    setting_frame.pack(pady=30, padx=30)

    config = module_save.load_config()
    misc_cfg = config['settings'].get('misc', {})
    enabled = misc_cfg.get('auto_refresh_enabled', False)
    interval = misc_cfg.get('auto_refresh_interval', 0)
    is_show = misc_cfg.get('show_confirmation_dialog', False)
    floor_B2 = misc_cfg.get('floor_B2', True)   # 默认选中
    floor_B3 = misc_cfg.get('floor_B3', True)
    floor_B4 = misc_cfg.get('floor_B4', True)

    row = 0

    # ---- 自动刷新 ----
    tk.Label(setting_frame, text="自动刷新:", font=("Arial", 10)).grid(row=row, column=0, padx=5, pady=8, sticky="e")
    enabled_var = tk.BooleanVar(value=enabled)
    chk_enable = tk.Checkbutton(setting_frame, variable=enabled_var)
    chk_enable.grid(row=row, column=1, padx=5, pady=8, sticky="w")
    row += 1

    # ---- 问题提醒 ----
    tk.Label(setting_frame, text="问题提醒:", font=("Arial", 10)).grid(row=row, column=0, padx=5, pady=8, sticky="e")
    show_var = tk.BooleanVar(value=is_show)
    chk_show = tk.Checkbutton(setting_frame, variable=show_var)
    chk_show.grid(row=row, column=1, padx=5, pady=8, sticky="w")
    row += 1

    # ---- 楼层筛选 ----
    tk.Label(setting_frame, text="楼层筛选:", font=("Arial", 10)).grid(row=row, column=0, padx=5, pady=8, sticky="ne")  # 顶对齐
    # 三个复选框横向排列
    floor_frame = tk.Frame(setting_frame)
    floor_frame.grid(row=row, column=1, padx=5, pady=8, sticky="w")
    var_B2 = tk.BooleanVar(value=floor_B2)
    var_B3 = tk.BooleanVar(value=floor_B3)
    var_B4 = tk.BooleanVar(value=floor_B4)
    cb_B2 = tk.Checkbutton(floor_frame, text="B2", variable=var_B2)
    cb_B3 = tk.Checkbutton(floor_frame, text="B3", variable=var_B3)
    cb_B4 = tk.Checkbutton(floor_frame, text="B4", variable=var_B4)
    cb_B2.pack(side=tk.LEFT, padx=5)
    cb_B3.pack(side=tk.LEFT, padx=5)
    cb_B4.pack(side=tk.LEFT, padx=5)
    row += 1

    # ---- 刷新间隔 ----
    tk.Label(setting_frame, text="刷新间隔(秒):", font=("Arial", 10)).grid(row=row, column=0, padx=5, pady=8, sticky="e")
    interval_var = tk.IntVar(value=interval if interval > 0 else 300)
    spin_interval = tk.Spinbox(setting_frame, from_=1, to=3600, textvariable=interval_var, width=10)
    spin_interval.grid(row=row, column=1, padx=5, pady=8, sticky="w")
    row += 1

    # ---- 按钮 ----
    def on_confirm():
        new_enabled = enabled_var.get()
        new_interval = interval_var.get()
        new_show = show_var.get()
        new_B2 = var_B2.get()
        new_B3 = var_B3.get()
        new_B4 = var_B4.get()
        if new_enabled and new_interval <= 0:
            messagebox.showwarning("警告", "刷新间隔必须大于0")
            return
        # 更新全局变量（若有）
        global auto_refresh_enabled, refresh_interval
        auto_refresh_enabled = new_enabled
        refresh_interval = new_interval
        # 应用到定时器
        if new_enabled and new_interval > 0:
            module_timer.set_interval(new_interval)
            module_timer.start()
        else:
            module_timer.stop()
        # 保存配置
        config['settings']['misc']['auto_refresh_enabled'] = new_enabled
        config['settings']['misc']['auto_refresh_interval'] = new_interval
        config['settings']['misc']['show_confirmation_dialog'] = new_show
        config['settings']['misc']['floor_B2'] = new_B2
        config['settings']['misc']['floor_B3'] = new_B3
        config['settings']['misc']['floor_B4'] = new_B4
        module_save.save_config(config)
        status_label.config(text=f"设置已保存: 自动刷新={'启用' if new_enabled else '禁用'}, 间隔={new_interval}秒")
        # 返回主界面或显示确认信息
        for widget in content_frame.winfo_children():
            widget.destroy()
        tk.Label(content_frame, text="设置已保存", font=("Arial", 14)).pack(pady=50)

    btn_frame = tk.Frame(setting_frame)
    btn_frame.grid(row=row, column=0, columnspan=2, pady=20)
    btn_confirm = tk.Button(btn_frame, text="保存", command=on_confirm, width=8)
    btn_confirm.pack(side=tk.LEFT, padx=10)

    status_label.config(text="查询设置界面 - 修改后点击确定")
# ---------- 登录相关----------
class LoginDialog:
    """登录对话框，支持记住密码"""
    def __init__(self, parent, title="登录"):
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("350x220")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # ---------- 让对话框相对于父窗口居中 ----------
        parent.update_idletasks()  # 确保父窗口尺寸已计算
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        dlg_w = 350
        dlg_h = 220
        x = parent_x + (parent_w - dlg_w) // 2
        y = parent_y + (parent_h - dlg_h) // 2
        self.dialog.geometry(f"+{x}+{y}")  # 仅移动位置，保持尺寸不变

        # ---------- 创建控件 ----------
        # 用户名
        tk.Label(self.dialog, text="用户名:").place(x=40, y=30)
        self.entry_username = tk.Entry(self.dialog)
        self.entry_username.place(x=110, y=30, width=180)

        # 密码
        tk.Label(self.dialog, text="密码:").place(x=40, y=70)
        self.entry_password = tk.Entry(self.dialog, show="*")
        self.entry_password.place(x=110, y=70, width=180)

        # 记住密码复选框
        self.remember_var = tk.BooleanVar()
        remember_cb = tk.Checkbutton(self.dialog, text="记住密码", variable=self.remember_var)
        remember_cb.place(x=110, y=110)

        # 登录按钮
        btn_login = tk.Button(self.dialog, text="登录", command=self.check_login, width=10)
        btn_login.place(x=130, y=150)

        # 绑定回车键
        self.dialog.bind('<Return>', lambda e: self.check_login())

        # 结果标志
        self.result = False
        self.user_info = None

        # 关闭窗口协议
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)

        # ---------- 加载保存的凭据 ----------
        self.load_saved_credentials()

        # 模态等待
        self.parent.wait_window(self.dialog)

    def load_saved_credentials(self):
        """从 saves.json 加载上次保存的用户名和记住密码状态"""
        config = module_save.load_config()
        last_emp = config['user'].get('last_user_emp', '')
        if last_emp:
            self.entry_username.insert(0, last_emp)

        if config['user'].get('remember_me', False):
            self.remember_var.set(True)
            saved_pwd = config['user'].get('last_user_pws', '')
            if saved_pwd:
                self.entry_password.insert(0, saved_pwd)
        else:
            self.remember_var.set(False)

    def check_login(self):
        """验证用户输入，成功后关闭对话框"""
        emp = self.entry_username.get().strip()
        pws = self.entry_password.get()
        remember = self.remember_var.get()

        if not emp:
            messagebox.showerror("错误", "请输入用户名", parent=self.dialog)
            return

        # 调用 module_login 的 login 函数
        success, info = module_login.login(emp, pws, remember)
        if success:
            self.result = True
            self.user_info = info
            self.dialog.destroy()
        else:
            messagebox.showerror("错误", f"登录失败：{info}", parent=self.dialog)
            self.entry_password.delete(0, tk.END)
            self.entry_username.focus()

    def on_close(self):
        """用户点击关闭按钮"""
        self.result = False
        self.dialog.destroy()
def re_login():
    global user_label, status_label, content_frame
    dlg = LoginDialog(root, title="登录")
    if dlg.result:
        # 更新界面
        user_label.config(text=f"当前用户: {module_login.current_user}")
        status_label.config(text="登录成功")
        for widget in content_frame.winfo_children():
            widget.destroy()
        welcome_label = tk.Label(content_frame, text=f"欢迎 {module_login.current_user}")
        welcome_label.pack(pady=20)
    else:
        pass
def update_ui_after_logout():
    """注销后更新界面（可选）"""
    global user_label, content_frame
    user_label.config(text="当前用户: 未登录")
    for widget in content_frame.winfo_children():
        widget.destroy()
    label = tk.Label(content_frame, text="已注销，请点击「登录」重新登录")
    label.pack(pady=20)
# -------- 重工流程相关 --------
def ui_routeR_dip_pack():
    def query_callback(dip, pack):
        result_msg, columns, rows = module_oracle.get_routeR_dip_pack(dip, pack)
        if result_msg == 'OK':
            if rows:
                global current_dip_route, current_pack_route
                current_dip_route = dip
                current_pack_route = pack
                ui_table_tree(columns, rows,route_menu)
            else:
                messagebox.showinfo("查询结果", "没有查询到数据")
        else:
            messagebox.showerror("查询失败", result_msg)

    _ui_input_two("查询DIP/PACK", query_callback,"DIP流程","PACK流程")
def route_menu(menu, tree, columns, row_id, col_index, col_name, values, cell_value, first_col_value):
    menu.add_command(label=f"复制 {col_name}", command=lambda: copy_to_clipboard(cell_value))
    if module_login.is_logined():
        menu.add_separator()
        if first_col_value:
            menu.add_command(label="查看流程", command=lambda: check_route(first_col_value))
        if current_dip_route and current_pack_route and first_col_value:
            menu.add_command(label="对比流程", command=lambda: contrast_route(current_dip_route, current_pack_route, first_col_value))
        else:
            menu.add_command(label="对比流程", state="disabled")
def contrast_route(dip,pack,rework):
    """
    对比两个流程（dip 和 pack）与 rework 流程的步骤
    左侧显示 dip + pack 的步骤合并列表，右侧显示 rework 步骤
    如果某流程无数据，则显示空表格
    """
    # 获取三个流程的数据（返回 (columns, rows)）
    _, rows_dip = module_oracle.fetch_route_steps(dip)
    _, rows_pack = module_oracle.fetch_route_steps(pack)
    _, rows_rework = module_oracle.fetch_route_steps(rework)

    # 合并左侧数据（dip + pack）
    rows_left = list(rows_dip) + list(rows_pack)

    # 创建对比窗口
    win = tk.Toplevel(root)
    win.title(f"流程对比: {dip}+{pack}  ↔  {rework}")
    win.geometry("800x500")
    win.transient(root)
    win.grab_set()

    # 使用 PanedWindow 左右分割
    paned = ttk.PanedWindow(win, orient=tk.HORIZONTAL)
    paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # ----- 左侧框架（dip + pack 合并）-----
    left_frame = tk.Frame(paned)
    paned.add(left_frame, weight=1)
    tk.Label(left_frame, text=f"流程: {dip} + {pack} (合并)", font=("Arial", 10, "bold")).pack(pady=5)
    l_scroll = ttk.Scrollbar(left_frame)
    l_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    left_tree = ttk.Treeview(left_frame, columns=["步骤", "是否必过"], show="headings",
                             yscrollcommand=l_scroll.set)
    left_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    l_scroll.config(command=left_tree.yview)
    left_tree.heading("步骤", text="步骤")
    left_tree.heading("是否必过", text="是否必过")
    left_tree.column("步骤", width=150, anchor="center")
    left_tree.column("是否必过", width=80, anchor="center")
    for row in rows_left:
        left_tree.insert("", tk.END, values=row)

    # ----- 右侧框架（rework）-----
    right_frame = tk.Frame(paned)
    paned.add(right_frame, weight=1)
    tk.Label(right_frame, text=f"流程: {rework}", font=("Arial", 10, "bold")).pack(pady=5)
    r_scroll = ttk.Scrollbar(right_frame)
    r_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    right_tree = ttk.Treeview(right_frame, columns=["步骤", "是否必过"], show="headings",
                              yscrollcommand=r_scroll.set)
    right_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    r_scroll.config(command=right_tree.yview)
    right_tree.heading("步骤", text="步骤")
    right_tree.heading("是否必过", text="是否必过")
    right_tree.column("步骤", width=150, anchor="center")
    right_tree.column("是否必过", width=80, anchor="center")
    for row in rows_rework:
        right_tree.insert("", tk.END, values=row)

    # 关闭按钮
    btn_close = tk.Button(win, text="关闭", command=win.destroy, width=10)
    btn_close.pack(pady=10)
def check_route(route_name):
    """查看流程详情（弹出新窗口）"""
    if not route_name:
        messagebox.showwarning("警告", "无效的流程标识")
        return

    # 查询步骤数据
    columns, rows = module_oracle.fetch_route_steps(route_name)
    if not columns or rows is None:
        messagebox.showerror("错误", "查询流程步骤失败")
        return

    if not rows:
        messagebox.showinfo("提示", "该流程没有步骤")
        return

    # 创建弹窗
    win = tk.Toplevel(root)
    win.title(f"流程步骤 - {route_name}")
    win.geometry("400x300")
    win.transient(root)
    win.grab_set()

    # 表格框架 + 滚动条
    frame = tk.Frame(win)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    v_scroll = ttk.Scrollbar(frame)
    v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    tree = ttk.Treeview(frame, columns=columns, show="headings",
                        yscrollcommand=v_scroll.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    v_scroll.config(command=tree.yview)

    # 设置列
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=120, anchor="center")

    # 插入数据
    for row in rows:
        tree.insert("", tk.END, values=row)

    # 关闭按钮
    btn_close = tk.Button(win, text="关闭", command=win.destroy)
    btn_close.pack(pady=5)
def ui_route_sn():
    """查询 SN 对应的流程列表，并让用户选择两个流程后执行查询。"""
    def on_sn_entered(sn):
        if not sn:
            messagebox.showwarning("提示", "请输入 SN")
            return
        result_msg, columns, rows = module_oracle.get_route_sn(sn)
        if result_msg == 'OK':
            if rows:
                # 调用通用选择器，传入查询回调
                ui_select_two_routes(columns, rows,on_selected=on_routes_selected,title="请选择恰好两个流程进行查询")
            else:
                messagebox.showinfo("查询结果", "没有查询到数据")
        else:
            messagebox.showerror("查询失败", result_msg)
    def on_routes_selected(dip, pack):
        # 当用户选择好两个流程后，执行查询
        global current_dip_route, current_pack_route
        result_msg, columns, rows = module_oracle.get_routeR_dip_pack(dip, pack)
        if result_msg == 'OK':
            if rows:
                current_dip_route = dip
                current_pack_route = pack
                ui_table_tree(columns, rows,route_menu)
            else:
                messagebox.showinfo("查询结果", "没有查询到数据")
        else:
            messagebox.showerror("查询失败", result_msg)
    # 使用通用单输入界面获取 SN
    _ui_input_one(title="查询 SN 流程",confirm_callback=on_sn_entered,label="SN:",btn_text="确定",warning_msg="请输入 SN 后再查询")
def ui_routeR_sn(columns, rows):
    """
    显示 SN 查询到的流程列表，并强制用户选择恰好两个路由。
    :param columns: 列名列表（如 ['ROUTE_ID', 'ROUTE_NAME']）
    :param rows: 数据行列表，每行为 (ROUTE_ID, ROUTE_NAME)
    """
    global content_frame, status_label, current_dip_route, current_pack_route

    # 清空内容区域
    for widget in content_frame.winfo_children():
        widget.destroy()

    if not rows:
        tk.Label(content_frame, text="没有查询到流程信息", font=("Arial", 12)).pack(pady=20)
        status_label.config(text="无流程信息")
        return

    # ---------- 居中容器 ----------
    center_frame = tk.Frame(content_frame)
    center_frame.place(relx=0.5, rely=0.5, anchor="center")

    # 标题
    tk.Label(center_frame, text="请选择恰好两个流程进行查询:", font=("Arial", 12, "bold")).pack(pady=10)

    # 流程列表容器
    list_frame = tk.Frame(center_frame)
    list_frame.pack(pady=10)

    # 存储每个流程的 (BooleanVar, route_id, route_name)
    route_vars = []

    for idx, row in enumerate(rows):
        route_id = row[0] if row else ""
        route_name = row[1] if len(row) > 1 else ""
        var = tk.BooleanVar(value=False)

        row_frame = tk.Frame(list_frame)
        row_frame.pack(anchor="w", pady=2)

        cb = tk.Checkbutton(row_frame, variable=var,
                            command=lambda v=var: on_check(v))
        cb.pack(side=tk.LEFT)

        lbl = tk.Label(row_frame, text=f"{route_id} - {route_name}")
        lbl.pack(side=tk.LEFT, padx=5)

        route_vars.append((var, route_id, route_name))

    def on_check(clicked_var):
        """限制选中数量不超过2个"""
        selected = sum(1 for v, _, _ in route_vars if v.get())
        if selected > 2:
            clicked_var.set(False)
            messagebox.showwarning("选择限制", "只能选择两个流程，不能超过两个")
            selected = sum(1 for v, _, _ in route_vars if v.get())
        status_label.config(text=f"已选择 {selected} 个流程（必须恰好选2个）")

    def on_confirm():
        global current_dip_route, current_pack_route
        selected_routes = [(r_id, r_name) for v, r_id, r_name in route_vars if v.get()]
        if len(selected_routes) != 2:
            messagebox.showinfo("提示", "必须恰好选择两个流程")
            return

        # 分配名称：D开头给dip，P开头给pack
        dip = None
        pack = None
        for r_id, r_name in selected_routes:
            if r_name.startswith('D'):
                dip = r_name
            elif r_name.startswith('P'):
                pack = r_name

        if dip is None or pack is None:
            messagebox.showerror("分配失败", "请选择一个D开头的流程和一个P开头的流程")
            return

        # 执行查询
        result_msg, columns, rows = module_oracle.get_routeR_dip_pack(dip, pack)
        if result_msg == 'OK':
            if rows:
                current_dip_route = dip
                current_pack_route = pack
                ui_routeR_dip_pack_tree(columns, rows)
            else:
                messagebox.showinfo("查询结果", "没有查询到数据")
        else:
            messagebox.showerror("查询失败", result_msg)

    # 确认按钮
    btn = tk.Button(center_frame, text="确认选择", command=on_confirm, width=12)
    btn.pack(pady=15)

    status_label.config(text="请选择恰好两个流程（D开头和P开头各一个）")
def ui_insert_routeR():
    def add_callback(dip, pack,router):
        result_msg = module_oracle.insert_routeR_DIP_PACK(dip, pack,router,module_login.current_user)
        if result_msg == 'OK':
            result_msg, columns, rows = module_oracle.get_routeR_dip_pack(dip, pack)
            if result_msg == 'OK':
                if rows:
                    global current_dip_route, current_pack_route
                    current_dip_route = dip
                    current_pack_route = pack
                    ui_table_tree(columns, rows)
                else:
                    messagebox.showinfo("查询结果", "没有查询到数据")
            else:
                messagebox.showerror("查询失败", result_msg)
        else:
            messagebox.showerror("查询失败", result_msg)
    _ui_input_three("添加DIP&PACK的重工流程", add_callback,"DIP流程:","PACK流程:","重工流程:")
def ui_insert_route_sn():
    """添加新流程时，先让用户选择两个流程作为组合。"""
    def on_selected(dip, pack):
        # 用户选择完后，继续让用户输入新路由名称和工号
        global current_dip_route, current_pack_route
        def on_router_entered(router_name):
            emp = module_login.current_user
            msg = module_oracle.insert_routeR_DIP_PACK(dip, pack, router_name, emp)
            if msg == 'OK':
                messagebox.showinfo("添加成功", msg)
                contrast_route(dip,pack,router_name)
            else:
                messagebox.showerror("失败", msg)
        # 使用单输入获取新路由名称
        _ui_input_one("输入新路由名称", on_router_entered, label="路由名称:", btn_text="添加")
        
    def on_sn_entered(sn):
        if not sn:
            messagebox.showwarning("提示", "请输入 SN")
            return
        result_msg, columns, rows = module_oracle.get_route_sn(sn)
        if result_msg == 'OK':
            if rows:
                # 调用通用选择器，传入查询回调
                ui_select_two_routes(columns, rows,on_selected,title="选择要组合的两个流程")
            else:
                messagebox.showinfo("查询结果", "没有查询到数据")
        else:
            messagebox.showerror("查询失败", result_msg)
    # 使用通用单输入界面获取 SN
    _ui_input_one(title="查询 SN 流程",confirm_callback=on_sn_entered,label="SN:",btn_text="确定",warning_msg="请输入 SN 后再查询")
def ui_copy_route():
    """复制流程到新流程"""
    def on_route_entered(route1,route2):
        if not route1 and not route2:
            messagebox.showwarning("提示", "请输入 流程")
            return
        result_msg = module_oracle.copy_route_new(route1,route2,module_login.current_user)
        if result_msg == 'OK':
            messagebox.showinfo("执行结果", f"复制{route1}到{route2}成功")
        else:
            messagebox.showerror("复制失败", result_msg)
    _ui_input_two(title="复制流程到新流程",confirm_callback=on_route_entered,label_1="现有流程:",label_2="新流程：",btn_text="确定",warning_msg="请输入 流程名 后再尝试添加")
def ui_find_route_by_process():
    """
    显示流程列表，按 STAGE_ID 分组，支持折叠，每行可选择状态（无/必有/必无）
    PROCESS_NAME 作为第一列（树形文本），PROCESS_ID 隐藏但用于保存
    """
    global content_frame, status_label
    # 清空内容区域
    for widget in content_frame.winfo_children():
        widget.destroy()
    # 获取数据
    msg, columns, rows = module_oracle.fetch_process()
    if msg != 'OK' or not rows:
        error_msg = msg if msg != 'OK' else "没有获取到流程数据"
        tk.Label(content_frame, text=error_msg, font=("Arial", 12), fg="red").pack(pady=20)
        status_label.config(text=error_msg)
        return
    # 获取各字段索引
    col_map = {col: idx for idx, col in enumerate(columns)}
    proc_id_idx = col_map.get('PROCESS_ID')
    proc_name_idx = col_map.get('PROCESS_NAME')
    stage_id_idx = col_map.get('STAGE_ID')
    proc_desc_idx = col_map.get('PROCESS_DESC')
    if any(v is None for v in [proc_id_idx, proc_name_idx, stage_id_idx, proc_desc_idx]):
        messagebox.showerror("错误", "缺少必要的列：PROCESS_ID, PROCESS_NAME, STAGE_ID, PROCESS_DESC")
        return
    # ---------- STAGE_ID 名称映射 ----------
    stage_names = {
        20001: "SMT 段",
        20002: "DIP 段",
        20003: "测试段",
        20004: "包装段",
    }

    # 按 STAGE_ID 分组
    groups = {}
    for row in rows:
        stage_id = row[stage_id_idx]
        groups.setdefault(stage_id, []).append(row)

    # 创建 Treeview 树形结构
    tree_frame = tk.Frame(content_frame)
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # 列顺序：PROCESS_ID, PROCESS_DESC, 状态 (PROCESS_NAME 作为 tree 的 text)
    cols_display = ('PROCESS_ID', 'PROCESS_DESC', '状态')
    tree = ttk.Treeview(tree_frame, columns=cols_display, show='tree headings')
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # 滚动条
    v_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
    v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    tree.configure(yscrollcommand=v_scroll.set)

    # 列标题和左对齐
    for col in cols_display:
        tree.heading(col, text=col)
        tree.column(col, width=120, anchor='w')   # 左对齐

    # 存储每个子项的状态和 PROCESS_ID 映射
    item_states = {}      # iid -> 状态字符串
    item_proc_id = {}     # iid -> PROCESS_ID

    # 插入分组和子项
    for stage_id, items in groups.items():
        # 自定义组显示名称
        display_name = stage_names.get(stage_id, f"STAGE_{stage_id}")
        parent = tree.insert('', 'end', text=f'{display_name} (ID:{stage_id})', open=True)
        for row in items:
            proc_id = row[proc_id_idx]
            proc_name = row[proc_name_idx]
            proc_desc = row[proc_desc_idx] if proc_desc_idx is not None else ''
            # 将 PROCESS_NAME 作为 tree 的 text，其他放入 columns
            child = tree.insert(parent, 'end', text=proc_name, values=(proc_id, proc_desc, '无'))
            item_states[child] = '无'
            item_proc_id[child] = proc_id

    # ---------- 右键菜单：设置状态 ----------
    def show_popup(event):
        selected = tree.identify_row(event.y)
        if not selected:
            return
        # 仅对子节点（非组）显示状态菜单
        if tree.parent(selected) == '':
            return
        menu = tk.Menu(root, tearoff=0)
        for state in ['无', '必有', '必无']:
            menu.add_command(label=f'设为 {state}',
                             command=lambda s=selected, st=state: set_state(s, st))
        menu.post(event.x_root, event.y_root)

    def set_state(iid, state):
        values = list(tree.item(iid, 'values'))
        values[2] = state  # 状态列在 values 中的索引为 2
        tree.item(iid, values=values)
        item_states[iid] = state
        # 更新状态栏，显示流程名称
        proc_name = tree.item(iid, 'text')
        status_label.config(text=f'已设置 {proc_name} 状态为 {state}')

    tree.bind('<Button-3>', show_popup)

    def on_summit():
        # 收集状态为“必有”和“必无”的流程名称
        must_have = []
        must_not = []
        for iid, state in item_states.items():
            if state == '必有':
                proc_name = tree.item(iid, 'text')  # 流程名称作为 tree 的 text
                must_have.append(proc_name)
            elif state == '必无':
                proc_name = tree.item(iid, 'text')
                must_not.append(proc_name)
        # 拼接字符串
        must_have_str = ','.join(must_have)
        must_not_str = ','.join(must_not)
        msg,columns,rows = module_oracle.fetch_route_process(must_have_str,must_not_str)
        if msg =="OK":
            if rows:
                ui_table_tree(columns, rows,route_menu)
            else:
                messagebox.showinfo("查询结果", "没有查询到数据")
        else:
            messagebox.showerror("查询失败", msg)
    btn_frame = tk.Frame(content_frame)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="确定", command=on_summit).pack(side=tk.LEFT, padx=10)
# --------- 清除卡号 ----------
def ui_clear_mac():
    """输入SN清除MAC卡号"""
    def on_sn_entered(sn):
        if not sn:
            messagebox.showwarning("提示", "请输入 SN")
            return
        result_msg, columns, rows = module_oracle.fetch_sn_mac(sn)
        if result_msg == 'OK':
            ui_table_tree(columns, rows,menu_mac)
        else:
            messagebox.showerror("查询失败", result_msg)
    def menu_mac(menu, tree, columns, row_id, col_index, col_name, values, cell_value, first_col_value):
        """自定义 MAC 表格右键菜单"""
        sn = values[columns.index('SERIAL_NUMBER')] if 'SERIAL_NUMBER' in columns else None
        mac = values[columns.index('MAC')] if 'MAC' in columns else None
        process = values[columns.index('WIP_PROCESS')] if 'MAC' in columns else None

        menu.add_command(label=f"复制 {col_name}", command=lambda: root.clipboard_append(cell_value))
        menu.add_command(label="查看当前值", command=lambda: show_cell_value(cell_value,col_name))

        if module_login.is_logined() and sn and mac and process=="F1Test":
            menu.add_separator()
            menu.add_command(label="删除 MAC",command=lambda s=sn, m=mac: delete_mac_action(s, m, tree))
        elif module_login.is_logined():
            menu.add_separator()
            menu.add_command(label="删除 MAC", state="disabled")

    def delete_mac_action(sn, mac, tree):
        """执行删除 MAC 操作"""
        if not messagebox.askyesno("确认删除", f"确定要删除 SN={sn}, MAC={mac} 吗？"):
            return
        msg = module_oracle.insert_ht_mac(sn,mac)
        if msg!="OK":
            messagebox.showerror("失败", msg)
            return
        msg = module_oracle.delete_sn_mac(sn, mac)
        if msg=="OK":
            on_sn_entered(sn)
            messagebox.showinfo("成功", msg)
        else:
            messagebox.showerror("失败", msg)
    _ui_input_one(title="查询卡号 : ",confirm_callback=on_sn_entered,label="SN:",btn_text="确定",warning_msg="请输入 SN 后再查询")
# -------- 服务器IP ----------
def load_server_ip(progress_callback=None):
    global server_ip
    server_ip = {}

    msg, cols, rows = module_oracle.fetch_server_gateway()
    if msg != 'OK' or not rows:
        update_status_safe("加载 IP 数据失败: " + msg)
        return

    col_map = {col: idx for idx, col in enumerate(cols)}
    for col in ['SERVER_ID', 'DRIVER_ID', 'GATEWAY_ID']:
        if col not in col_map:
            update_status_safe(f"缺少列: {col}")
            return

    total_ip_count = 0
    last_update_time = time.time()

    for row in rows:
        server_id = row[col_map['SERVER_ID']]
        driver_id = row[col_map['DRIVER_ID']]
        gateway_id = row[col_map['GATEWAY_ID']]
        gateway_key = f"{server_id}_{gateway_id}_{driver_id}"

        tres, ip_raw = module_oracle.fetch_gateway_ip(server_id, driver_id, gateway_id)
        if tres != 'OK' or not ip_raw:
            continue
        parts = ip_raw.split(';')
        ip_part = parts[1] if len(parts) > 1 else ''
        ip_list = [ip.strip() for ip in ip_part.split(',') if ip.strip()]
        if not ip_list:
            continue

        statuses = []
        for idx, ip in enumerate(ip_list, start=1):
            status_tres, _, status_rows = module_oracle.get_terminal_status(server_id, gateway_id, idx)
            if status_tres == 'OK' and status_rows:
                statuses.append(status_rows[0] if status_rows else None)
            else:
                statuses.append(None)

        for ip, status_row in zip(ip_list, statuses):
            segments = ip.split('.')
            subnet = '.'.join(segments[:3]) if len(segments) >= 3 else 'unknown'
            if subnet not in server_ip:
                server_ip[subnet] = {}
            if ip not in server_ip[subnet]:
                server_ip[subnet][ip] = []
            server_ip[subnet][ip].append((gateway_key, status_row))
            total_ip_count += 1

        # 每秒最多更新一次进度
        if progress_callback is not None:
            now = time.time()
            if now - last_update_time >= 1.0:
                progress_callback(total_ip_count)
                last_update_time = now

    # 最后再更新一次，确保最终数量显示
    if progress_callback is not None:
        progress_callback(total_ip_count)

    update_status_safe(f"IP 数据加载完成，共 {total_ip_count} 个 IP")
def exprot_server_ip():
    """
    后台加载全部 IP 数据，实时显示进度，加载完成后自动导出 CSV。
    """
    global server_ip

    status_label.config(text="正在加载 IP 数据...")
    root.update_idletasks()

    def load_and_export():
        # 加载数据（带进度回调）
        def update_progress(count):
            root.after(0, lambda: status_label.config(text=f"正在加载 IP 数据... 已加载 {count} 个 IP"))

        load_server_ip(progress_callback=update_progress)

        # 加载完成后，回到主线程执行导出
        root.after(0, _do_export)

    threading.Thread(target=load_and_export, daemon=True).start()
def _do_export():
    """实际执行导出的函数（在主线程中运行）"""
    try:
        desktop = os.path.expanduser("~/Desktop")
        filepath = os.path.join(desktop, "server_ip_export.csv")

        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(["网段", "IP", "网关Key(S_G_D)", "状态"])

            for subnet, ip_dict in server_ip.items():
                # 对每个网段内的 IP 进行数值排序
                valid_ips = []
                for ip in ip_dict.keys():
                    try:
                        parts = ip.split('.')
                        int_parts = [int(part) for part in parts]
                        valid_ips.append((ip, int_parts))
                    except ValueError:
                        pass
                sorted_ips = [ip for ip, _ in sorted(valid_ips, key=lambda x: x[1])]

                for ip in sorted_ips:
                    for gateway_key, status_row in ip_dict[ip]:
                        status = str(status_row) if status_row else "无状态"
                        writer.writerow([subnet, ip, gateway_key, status])

        status_label.config(text="导出完成")
        messagebox.showinfo("导出成功", f"数据已导出到：{filepath}")
    except Exception as e:
        status_label.config(text="导出失败")
        messagebox.showerror("导出失败", f"写入CSV文件失败：{e}")
def ui_tree_server():
    """
    三层树结构：服务器 (Server) → 网关 (Gateway) → IP
    展开网关时自动调用存储过程查询 IP。
    """
    global content_frame, status_label,server_ip

    # 清空内容区域
    for widget in content_frame.winfo_children():
        widget.destroy()

    # 获取数据
    msg, columns, rows = module_oracle.fetch_server_gateway()
    if msg != 'OK' or not rows:
        error_text = msg if msg != 'OK' else "没有查询到数据"
        tk.Label(content_frame, text=error_text, font=("Arial", 12), fg="red").pack(pady=20)
        status_label.config(text=error_text)
        return

    # 获取必要的列索引
    col_map = {col: idx for idx, col in enumerate(columns)}
    required_cols = [
        'SERVER_ID', 'SERVER_DESC_E', 'DRIVER_ID',
        'GATEWAY_ID', 'GATEWAY_DESC_E', 'GAYTEWAY_CONNECT_NUMBER'
    ]
    for col in required_cols:
        if col not in col_map:
            messagebox.showerror("错误", f"缺少列: {col}")
            return

    # 按 SERVER_ID 分组，计算总连接数
    groups = {}
    server_total_conn = {}
    for row in rows:
        server_id = row[col_map['SERVER_ID']]
        groups.setdefault(server_id, []).append(row)
        conn_num = row[col_map['GAYTEWAY_CONNECT_NUMBER']] or 0
        server_total_conn[server_id] = server_total_conn.get(server_id, 0) + conn_num

    # 创建 Treeview
    tree = ttk.Treeview(content_frame, show='tree')
    tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # 存储网关参数 {iid: (server_id, driver_id, gateway_id)}
    gateway_params = {}

    # ----- 插入服务器和网关节点 -----
    for server_id, items in groups.items():
        server_desc = items[0][col_map['SERVER_DESC_E']]
        total_conn = server_total_conn.get(server_id, 0)
        server_text = f"{server_desc} (总连接数: {total_conn})"
        server_iid = tree.insert('', 'end', text=server_text, open=False)

        for row in items:
            gateway_desc = row[col_map['GATEWAY_DESC_E']]
            connect_num = row[col_map['GAYTEWAY_CONNECT_NUMBER']] or 0
            driver_id = row[col_map['DRIVER_ID']]
            gateway_id = row[col_map['GATEWAY_ID']]
            gateway_text = f"{gateway_desc} (连接数: {connect_num})"
            gateway_iid = tree.insert(server_iid, 'end', text=gateway_text, open=False)
            tree.insert(gateway_iid, 'end', text='加载中...', open=False)
            gateway_params[gateway_iid] = (server_id, driver_id, gateway_id)

    # ----- 展开网关时查询 IP -----
    def on_tree_open(event):
        item = tree.focus()
        if not item or item not in gateway_params:
            return
        children = tree.get_children(item)
        if children and tree.item(children[0], 'text') != '加载中...':
            return
        for child in children:
            tree.delete(child)

        server_id, driver_id, gateway_id = gateway_params[item]
        tres, ip_raw = module_oracle.fetch_gateway_ip(server_id, driver_id, gateway_id)
        if tres == 'OK' and ip_raw:
            try:
                parts = ip_raw.split(';')
                ip_part = parts[1] if len(parts) > 1 else ''
                ip_list = [ip.strip() for ip in ip_part.split(',') if ip.strip()]
                if ip_list:
                    for idx, ip in enumerate(ip_list, start=1):
                        _, _, status_rows = module_oracle.get_terminal_status(server_id, gateway_id, idx)
                        tree.insert(item, 'end', text=f"{idx}. {ip} {status_rows}", open=False)
                else:
                    tree.insert(item, 'end', text="IP: (无有效IP)", open=False)
            except Exception:
                tree.insert(item, 'end', text=f"IP 解析失败: {ip_raw[:50]}", open=False)
        elif tres == 'OK':
            tree.insert(item, 'end', text="IP: (空)", open=False)
        else:
            tree.insert(item, 'end', text=f"查询失败: {tres}", open=False)
    tree.bind('<<TreeviewOpen>>', on_tree_open)
# ---------- 查询 -----------
def query_sn_ppid():
    def query_callback(sn, pcb):
        result_msg, columns, rows = module_oracle.fetch_sn_ppid(sn, pcb)
        if result_msg == 'OK':
            if rows:
                ui_table_tree(columns, rows,ppid_menu)
            else:
                messagebox.showinfo("查询结果", "没有查询到数据")
        else:
            messagebox.showerror("查询失败", result_msg)
    def ppid_menu(menu, tree, columns, row_id, col_index, col_name, values, cell_value, first_col_value):
        sn = values[columns.index('STRSMTSN')] if 'STRSMTSN' in columns else None
        ppid = values[columns.index('PCB_QRCODE')] if 'PCB_QRCODE' in columns else None 

        menu.add_command(label=f"复制 {col_name}", command=lambda: copy_to_clipboard(cell_value))
        if module_login.is_logined():
            menu.add_separator()
            menu.add_command(label="删除这一条记录", command=lambda: delete_sn_ppid(sn,ppid))
            if col_name == "STRSMTSN":
                menu.add_command(label="修改 STRSMTSN",command=lambda: prompt_update_sn(sn, ppid, field='sn'))
            if col_name == "PCB_QRCODE":
                menu.add_command(label="修改 PCB_QRCODE",command=lambda: prompt_update_sn(sn, ppid, field='ppid'))
    def delete_sn_ppid(sn,ppid):
        if not messagebox.askyesno("确认删除", f"确定要删除 SN={sn}, PCB二维码={ppid}的记录吗？"):
            return
        msg = module_oracle.delete_sn_ppid(sn, ppid)
        if msg == "OK":
            messagebox.showinfo("成功", "删除成功")
            query_callback(sn, ppid)
        else:
            messagebox.showerror("错误", f"删除失败: {msg}")
    def prompt_update_sn(sn, ppid, field):
        """弹出输入框获取新值并执行更新"""
        if field == 'sn':
            new_val = simpledialog.askstring("修改 STRSMTSN", "请输入新的 STRSMTSN:", parent=root)
            if new_val is None:  # 用户取消
                return
            new_val = new_val.strip()
            if not new_val:
                messagebox.showwarning("警告", "新 STRSMTSN 不能为空")
                return
            if not messagebox.askyesno("确认修改", f"确定将 STRSMTSN 从 {sn} 修改为 {new_val} 吗？"):
                return
            msg = module_oracle.update_ppid_sn(sn, ppid, new_sn=new_val)
            if msg == "OK":
                messagebox.showinfo("成功", "更新成功")
                query_callback(new_val,ppid)
            else:
                messagebox.showerror("错误", f"更新失败: {msg}")
        else:  # ppid
            new_val = simpledialog.askstring("修改 PCB_QRCODE", "请输入新的 PCB_QRCODE:", parent=root)
            if new_val is None:
                return
            new_val = new_val.strip()
            if not new_val:
                messagebox.showwarning("警告", "新 PCB_QRCODE 不能为空")
                return
            if not messagebox.askyesno("确认修改", f"确定将 PCB_QRCODE 从 {ppid} 修改为 {new_val} 吗？"):
                return
            msg = module_oracle.update_ppid_pcb(sn, ppid, new_ppid=new_val)
            if msg == "OK":
                messagebox.showinfo("成功", "更新成功")
                query_callback(sn,new_val)
            else:
                messagebox.showerror("错误", f"更新失败: {msg}")
    _ui_input_two("查询 SN & PCB",query_callback,"SN :","PCB :")
def query_sn_keyparts():
    def query_callback(sn):
        result_msg, columns, rows = module_oracle.fetch_sn_keyparts(sn)
        if result_msg == 'OK':
            if rows:
                ui_table_tree(columns, rows,keyarts_menu)
            else:
                messagebox.showinfo("查询结果", "没有查询到数据")
        else:
            messagebox.showerror("查询失败", result_msg)
    def keyarts_menu(menu, tree, columns, row_id, col_index, col_name, values, cell_value, first_col_value):
        sn = values[columns.index('SERIAL_NUMBER')] if 'SERIAL_NUMBER' in columns else None
        part = values[columns.index('ITEM_PART_SN')] if 'ITEM_PART_SN' in columns else None 
        time = values[columns.index('UPDATE_TIME')] if 'UPDATE_TIME' in columns else None 

        menu.add_command(label=f"复制 {col_name}", command=lambda: copy_to_clipboard(cell_value))
        if module_login.is_logined():
            menu.add_separator()
            menu.add_command(label="删除这一条记录", command=lambda: delete_sn_keypart(sn,part,time))
            menu.add_command(label="删除全部记录", command=lambda: delete_all_keyarts(sn))
    def delete_sn_keypart(sn, part, time):
        if not messagebox.askyesno("确认删除", f"确定要删除 SN={sn}, 料件SN={part}, 时间={time} 的记录吗？"):
            return
        msg = module_oracle.insert_ht_sn_keypart(sn, part, time)
        if msg != "OK":
            messagebox.showerror("错误", f"插入历史表失败: {msg}")
            return
        msg = module_oracle.delete_sn_keypart(sn, part, time)
        if msg == "OK":
            messagebox.showinfo("成功", "删除成功")
            query_callback(sn)
        else:
            messagebox.showerror("错误", f"删除失败: {msg}")
    def delete_all_keyarts(sn):
        if not messagebox.askyesno("确认删除", f"确定要删除 SN={sn} 的所有记录吗？"):
            return
        msg = module_oracle.insert_ht_sn_keyparts(sn)
        if msg != "OK":
            messagebox.showerror("错误", f"插入历史表失败: {msg}")
            return
        msg = module_oracle.delete_sn_keyparts(sn)
        if msg == "OK":
            messagebox.showinfo("成功", "删除成功")
            query_callback(sn)
        else:
            messagebox.showerror("错误", f"删除失败: {msg}")
    _ui_input_one("查询 SN & KEYPARTS",query_callback,"SN :")
def qurey_keyparts_carton():
    list_sn = []
    cartonc = None
    def query_callback(carton):
        nonlocal list_sn,cartonc
        cartonc = carton
        result_msg, columns, rows = module_oracle.fetch_carton_keyparts(carton)
        if result_msg == 'OK':
            if rows:
                try:
                    sn_index = columns.index("SERIAL_NUMBER")
                    list_sn = [row[sn_index] for row in rows]
                    list_sn = list(dict.fromkeys(list_sn))
                except ValueError:
                    list_sn = []
                ui_table_tree(columns, rows,keyarts_menu)
            else:
                messagebox.showinfo("查询结果", "没有查询到数据")
        else:
            messagebox.showerror("查询失败", result_msg)
    def keyarts_menu(menu, tree, columns, row_id, col_index, col_name, values, cell_value, first_col_value):
        wo = values[columns.index('WORK_ORDER')] if 'WORK_ORDER' in columns else None
        process = values[columns.index('PROCESS_NAME')] if 'PROCESS_NAME' in columns else None 
        menu.add_command(label=f"复制 {col_name}", command=lambda: copy_to_clipboard(cell_value))
        if module_login.is_logined():
            menu.add_separator()
            menu.add_command(label=f"删除{wo}工单下{process}站位的记录", command=lambda: delete_keyparts_wo_process(wo,process,list_sn))
    def delete_keyparts_wo_process(wo,process,list_sn):
        if not messagebox.askyesno("确认删除", f"确定要删除工单{wo}下的{process}站位的记录吗？"):
            return
        msg = module_oracle.insert_ht_keyarts_wo_process(wo,process,list_sn)
        if msg != "OK":
            messagebox.showerror("错误", f"插入历史表失败: {msg}")
            return
        msg = module_oracle.delete_keyparts_wo_process(wo,process,list_sn)
        if msg == "OK":
            messagebox.showinfo("成功", "删除成功")
            query_callback(cartonc)
        else:
            messagebox.showerror("错误", f"删除失败: {msg}")
    _ui_input_one("查询 箱号下SN的料件 ",query_callback,"箱号 :")
def qurey_keyparts_rework():
    list_sn = []
    rework = None
    groups = {}
    def query_callback(rewk):
        nonlocal list_sn,rework,groups
        rework = rewk
        result_msg, columns, rows = module_oracle.fetch_keyparts_rework(rewk)
        if result_msg == 'OK':
            if rows:
                try:
                    sn_idx = columns.index("SERIAL_NUMBER")
                    wo_idx = columns.index("WORK_ORDER")
                    process_idx = columns.index("PROCESS_NAME")
                except ValueError:
                    messagebox.showerror("错误", "缺少必要的列")
                    return
                # 构建分组: key=(wo, process), value=list of sn
                groups = {}
                all_sn = []
                for row in rows:
                    sn = row[sn_idx]
                    wo = row[wo_idx]
                    process = row[process_idx]
                    all_sn.append(sn)
                    key = (wo, process)
                    groups.setdefault(key, []).append(sn)

                # 去重
                list_sn = list(dict.fromkeys(all_sn))
                for key in groups:
                    groups[key] = list(dict.fromkeys(groups[key]))
                # 构建显示数据：每行 (WORK_ORDER, PROCESS_NAME, 合并的SN字符串)
                display_rows = []
                for (wo, process), sn_list in groups.items():
                    sns_str = ', '.join(sn_list)
                    display_rows.append((wo, process, sns_str))
                display_columns = ['WORK_ORDER', 'PROCESS_NAME', 'SERIAL_NUMBER']
                ui_table_tree(display_columns, display_rows, keyarts_menu)
            else:
                messagebox.showinfo("查询结果", "没有查询到数据")
        else:
            messagebox.showerror("查询失败", result_msg)
    def keyarts_menu(menu, tree, columns, row_id, col_index, col_name, values, cell_value, first_col_value):
        wo = values[columns.index('WORK_ORDER')] if 'WORK_ORDER' in columns else None
        process = values[columns.index('PROCESS_NAME')] if 'PROCESS_NAME' in columns else None 
        menu.add_command(label=f"复制 {col_name}", command=lambda: copy_to_clipboard(cell_value))
        if module_login.is_logined():
            menu.add_separator()
            menu.add_command(label=f"删除{wo}工单下{process}站位的记录", command=lambda: delete_keyparts_wo_process(wo,process,list_sn))
    def delete_keyparts_wo_process(wo,process,list_sn):
        if not messagebox.askyesno("确认删除", f"确定要删除工单{wo}下的{process}站位的记录吗？"):
            return
        msg = module_oracle.insert_ht_keyarts_wo_process(wo,process,list_sn)
        if msg != "OK":
            messagebox.showerror("错误", f"插入历史表失败: {msg}")
            return
        msg = module_oracle.delete_keyparts_wo_process(wo,process,list_sn)
        if msg == "OK":
            messagebox.showinfo("成功", "删除成功")
            query_callback(rework)
        else:
            messagebox.showerror("错误", f"删除失败: {msg}")
    _ui_input_one("查询 重工编号下的SN的料件 ",query_callback,"重工编号 :")
def qurey_work_order():
    def query_callback(work):
        result_msg, columns, rows = module_oracle.fetch_work_order(work)
        if result_msg == 'OK':
            if rows:
                ui_table_tree(columns, rows,order_menu)
            else:
                messagebox.showinfo("查询结果", "没有查询到数据")
        else:
            messagebox.showerror("查询失败", result_msg)
    def order_menu(menu, tree, columns, row_id, col_index, col_name, values, cell_value, first_col_value):
        wo = values[columns.index('WORK_ORDER')] if 'WORK_ORDER' in columns else None

        menu.add_command(label=f"复制 {col_name}", command=lambda: copy_to_clipboard(cell_value))
        if module_login.is_logined() and wo:
            menu.add_separator()
            # 创建状态子菜单
            status_menu = tk.Menu(menu, tearoff=0)
            menu.add_cascade(label="修改工单状态", menu=status_menu)
            status_map = {
                0: "initial",
                1: "prepare",
                2: "release",
                3: "work in process",
                4: "hold",
                5: "cancel",
                6: "complete"
            }
            for status_code, status_desc in status_map.items():
                status_menu.add_command(
                    label=f"{status_code} - {status_desc}",
                    command=lambda s=status_code: update_workorder_status(wo, s)
                )
    def update_workorder_status(wo,status):
        if not messagebox.askyesno("确认修改", f"确定要修改工单{wo}的状态为{status}吗？"):
            return
        msg = module_oracle.update_woder_status(wo,status)
        if msg == "OK":
            messagebox.showinfo("成功", "修改成功")
            query_callback(wo)
        else:
            messagebox.showerror("错误", f"修改失败: {msg}")
    _ui_input_one("查询工单状态 ",query_callback,"工单 :")
# ---------- 主函数 -----------
def main():
    global root, content_frame, status_label, user_label

    root = tk.Tk()
    root.title("VarlikeTools")
    root.geometry("960x540")
    icon_path = resource_path("favicon.ico")
    root.iconbitmap(icon_path)
    
    # 加载窗口配置
    config = module_save.load_config()
    win_cfg = config['settings']['window']
    root.geometry(f"{win_cfg['width']}x{win_cfg['height']}+{win_cfg['x']}+{win_cfg['y']}")
    if win_cfg['maximized']:
        root.state('zoomed')

    # 尝试自动登录
    auto_user = module_login.init_login_from_config()
    if auto_user:
        # 自动登录成功
        initial_welcome = f"欢迎回来，{auto_user}"
        user_display = auto_user
    else:
        initial_welcome = "欢迎使用 VarlikeTools\n请点击菜单栏「用户->登录」"
        user_display = "未登录"

    # 菜单栏
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    # 查询
    question_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="问题处理", menu=question_menu)
    question_menu.add_command(label="查询问题", command=query_issue)
    question_menu.add_command(label="查询设置", command=query_setting)
    # 用户
    menu_user = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="用户", menu=menu_user)
    menu_user.add_command(label="登录", command=re_login)
    menu_user.add_command(label="注销", command=lambda: (module_login.logout(), update_ui_after_logout()))
    # 重工流程
    route_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="重工流程", menu=route_menu)
    route_menu.add_command(label="---查询---", state="disabled")
    route_menu.add_command(label="DIP$PACK", command=ui_routeR_dip_pack)
    route_menu.add_command(label="SN", command=ui_route_sn)
    route_menu.add_command(label="Process",command=ui_find_route_by_process)
    route_menu.add_command(label="---添加---", state="disabled")
    route_menu.add_command(label="DIP$PACK", command=ui_insert_routeR)
    route_menu.add_command(label="SN", command=ui_insert_route_sn)
    route_menu.add_command(label="复制流程", command=ui_copy_route)
    #清除卡号
    menubar.add_command(label="清除卡号", command=ui_clear_mac)
    #服务器IP
    server_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="服务器IP", menu=server_menu)
    server_menu.add_command(label="查看IP列表", command=ui_tree_server)
    server_menu.add_command(label="导出全部IP", command=exprot_server_ip)
    #查询
    query_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="查询", menu=query_menu)
    query_menu.add_command(label="查询SN&PCB", command=query_sn_ppid)
    query_menu.add_command(label="查询SN&KEYPARTS", command=query_sn_keyparts)
    query_menu.add_command(label="查询箱号下的料件", command=qurey_keyparts_carton)
    query_menu.add_command(label="查询重工号下的料件", command=qurey_keyparts_rework)
    query_menu.add_command(label="查询工单状态", command=qurey_work_order)
    # 内容区域
    content_frame = tk.Frame(root)
    content_frame.pack(fill=tk.BOTH, expand=True)
    welcome_label = tk.Label(content_frame, text=initial_welcome)
    welcome_label.pack(pady=20)
    # 底部
    bottom_frame = tk.Frame(root)
    bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
    status_label = tk.Label(bottom_frame, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
    status_label.pack(side=tk.TOP, fill=tk.X)
    user_label = tk.Label(bottom_frame, text=f"当前用户: {user_display}", bd=1, relief=tk.SUNKEN, anchor=tk.W)
    user_label.pack(side=tk.TOP, fill=tk.X)
    # 初始化定时器，传入 root 和刷新函数（query_issue）
    module_timer.init_timer(root, lambda: query_issue(notify=True))
    # 加载配置
    config = module_save.load_config()
    refresh_interval = config['settings']['misc'].get('auto_refresh_interval', 0)
    auto_refresh_enabled = config['settings']['misc'].get('auto_refresh_enabled', False)
    # 如果启用，启动定时器
    if auto_refresh_enabled and refresh_interval > 0:
        module_timer.set_interval(refresh_interval)
        module_timer.start()
    else:
        # 确保停止
        module_timer.stop()
    # 窗口关闭保存配置
    def on_closing():
        module_timer.stop()
        config = module_save.load_config()
        if root.state() != 'zoomed':
            config['settings']['window']['width'] = root.winfo_width()
            config['settings']['window']['height'] = root.winfo_height()
            config['settings']['window']['x'] = root.winfo_x()
            config['settings']['window']['y'] = root.winfo_y()
        config['settings']['window']['maximized'] = (root.state() == 'zoomed')
        module_save.save_config(config)
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
if __name__ == "__main__":
    main()