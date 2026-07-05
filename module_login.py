import module_oracle
import module_save

current_user = None

def login_check_emp(emp,pws):
    res = module_oracle.LOGIN_EMP_CHECK(emp,pws)
    return res

def init_login_from_config():
    """
    在程序启动时调用，从配置文件中读取保存的凭据，尝试自动登录。
    返回当前登录用户（成功登录的用户信息）或 None。
    """
    global current_user
    config = module_save.load_config()
    if config['user'].get('remember_me', False):
        emp = config['user'].get('last_user_emp', '')
        pws = config['user'].get('last_user_pws', '')
        if emp and pws:
            try:
                msg = login_check_emp(emp, pws)  # 假设该函数在本模块或从别处导入
                if msg == "OK":
                    current_user = emp  # 例如员工姓名
                    # 可选：在状态栏显示自动登录成功
                    return current_user
                else:
                    # 凭证失效，清除保存的密码（可选）
                    config['user']['remember_me'] = False
                    config['user']['last_user_pws'] = ''
                    module_save.save_config(config)
            except Exception as e:
                print(f"自动登录失败: {e}")
    current_user = None
    return None

def login(emp, pws, remember):
    """
    手动登录函数，供登录对话框调用。
    成功时返回 (True, 用户信息)，并更新 current_user 和配置文件。
    失败时返回 (False, 错误信息)。
    """
    global current_user
    msg = login_check_emp(emp, pws)
    if msg != "OK":
        return False, msg
    # 登录成功
    current_user = emp
    # 保存配置
    config = module_save.load_config()
    config['user']['last_user_emp'] = emp
    if remember:
        config['user']['last_user_pws'] = pws
        config['user']['remember_me'] = True
    else:
        config['user']['last_user_pws'] = ''
        config['user']['remember_me'] = False
    module_save.save_config(config)
    return True, msg

def logout():
    """注销当前用户"""
    global current_user
    current_user = None
     # 保存配置
    config = module_save.load_config()
    config['user']['last_user_emp'] = ""
    config['user']['last_user_pws'] = ""
    config['user']['remember_me'] = False
    module_save.save_config(config)

def is_logined():
    if current_user != None:
        return True
    else:
        return False