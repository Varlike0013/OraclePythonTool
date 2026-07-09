import os
import oracledb
import sys
import module_save

# 获取程序运行时的根目录
# 如果是 PyInstaller 打包后的 exe，用 sys._MEIPASS；否则用当前文件所在目录
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS          # PyInstaller 临时解压目录
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

# 拼接 Instant Client 子目录（文件夹名字要和下面一致）
instant_client_dir = os.path.join(base_path, "instantclient_19_31")

# 设置 NLS_LANG 解决 ORA-12705
os.environ['NLS_LANG'] = 'AMERICAN_AMERICA.AL32UTF8'  # 或 'SIMPLIFIED CHINESE_CHINA.ZHS16GBK'
# 初始化 Oracle Client
oracledb.init_oracle_client(lib_dir=instant_client_dir)
#oracledb.init_oracle_client(lib_dir=r"D:\\instantclient-basic-nt-19.31.0.0.0dbru\\instantclient_19_31")

username = "SAJET"
password = "tech"
dsn = "10.240.144.17:1521/SAJET"

def fetch_rework_records(): #查询问题今天还未解决的问题
    """
    从 SAJET.ECS_SN_REWORK 表中获取当天 CREATEDATE 非空且 DUALTIME 为空的记录，
    按 CREATEDATE 降序排列。
    
    参数:
        username (str): 数据库用户名
        password (str): 数据库密码
        dsn (str): 数据库连接字符串 (例如 "host:port/service_name")
    
    返回:
        list: 包含所有查询结果的列表，每个元素是一个元组（行数据）
    """
    # 读取楼层筛选设置（默认为 True 表示全选）
    config = module_save.load_config()
    misc = config.get('settings', {}).get('misc', {})
    floor_B2 = misc.get('floor_B2', True)
    floor_B3 = misc.get('floor_B3', True)
    floor_B4 = misc.get('floor_B4', True)

    #  构建楼层条件
    floor_conditions = []
    if floor_B2:
        floor_conditions.append("R.PDLINE_NAME LIKE 'B2%'")
    if floor_B3:
        floor_conditions.append("R.PDLINE_NAME LIKE 'B3%'")
    if floor_B4:
        floor_conditions.append("R.PDLINE_NAME LIKE 'B4%'")
    floor_clause = ""
    if floor_conditions:
        floor_clause = " AND (" + " OR ".join(floor_conditions) + ")"
    sql = f"""
        SELECT * 
        FROM SAJET.ECS_SN_REWORK R
        WHERE R.CREATEDATE IS NOT NULL 
          AND R.DUALTIME IS NULL
          AND R.CREATEDATE >= TRUNC(SYSDATE)          -- 今天零点
          AND R.CREATEDATE < TRUNC(SYSDATE) + 1       -- 明天零点（不包含）
          {floor_clause}
        ORDER BY R.CREATEDATE DESC
    """
    # 执行查询
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                return columns, rows
    except oracledb.Error as e:
        raise RuntimeError(f"数据库查询失败: {e}")
def fetch_ECS_SN_REWORK_col_value (col_name, value, count=20):
    """
    从 SAJET.ECS_SN_REWORK 表中查询指定列等于指定值的记录，
    按 CREATEDATE 降序排列，返回最近的 count 条。

    参数:
        col_name (str): 要筛选的列名（必须属于表内合法列）
        value (str/int): 要匹配的值
        count (int): 返回的记录条数，默认为20

    返回:
        tuple: (columns, rows)
            columns: 列名列表
            rows: 查询结果行列表，每行为元组
    """
    sql = f"""
        SELECT * FROM (
            SELECT * 
            FROM SAJET.ECS_SN_REWORK 
            WHERE {col_name} = :value
            ORDER BY CREATEDATE DESC
        ) WHERE ROWNUM <= :count
    """
    with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, {'value': value, 'count': count})
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return columns, rows
def LOGIN_EMP_CHECK(emp, pws):
    """
    验证员工登录
    :param EMP: 员工号
    :param PWS: 密码
    :return: (status_code, message)
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                # 调用存储过程，使用输出参数接收结果
                result_var = cursor.var(oracledb.DB_TYPE_VARCHAR)  # 输出变量
                cursor.callproc("SAJET.SJ_CHK_EMP_PWD", [emp, pws, result_var])
                result = result_var.getvalue()
                return result
    except oracledb.Error as e:
        error_msg = f"数据库错误: {e}"
        return error_msg
    except Exception as e:
        return str(e)
def update_question_status(record_id, reply, emp_no):
    """
    更新SAJET.ECS_SN_REWORK表的状态
    :param record_id: 记录索引 (NUMBERINDEX)
    :param reply: 状态值 (REWORK_NO)
    :param user: 当前用户工号 (EMP_NO)
    :return: message
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                sql = """
                    UPDATE SAJET.ECS_SN_REWORK R
                    SET R.EMP_SFIS = (SELECT E.EMP_NAME FROM SAJET.SYS_EMP E WHERE E.EMP_NO = :emp_no),
                        R.DUALTIME = SYSDATE,
                        R.REWORK_NO = :reply
                    WHERE R.NUMBERINDEX = :record_id
                """
                cursor.execute(sql, emp_no=emp_no, reply=reply, record_id=record_id)
                conn.commit()
                if cursor.rowcount == 0:
                    return "未找到对应的记录，更新失败"
                return "OK"
    except oracledb.Error as e:
        return f"数据库错误: {e}"
    except Exception as e:
        return f"错误: {e}"
def get_routeR_dip_pack(dip,pack):
    """
    调用 SAJET.SJ_GET_R_ROUTE 存储过程
    :param dip: 输入参数 dip
    :param pack: 输入参数 pack
    :return: (result_msg, columns, rows)
             result_msg: 存储过程返回的状态字符串
             columns: 列名列表
             rows: 数据行列表
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                # 创建输出变量
                result_var = cursor.var(oracledb.DB_TYPE_VARCHAR)
                cur_var = cursor.var(oracledb.DB_TYPE_CURSOR)
                # 调用存储过程
                cursor.callproc("SAJET.SJ_GET_R_ROUTE", [dip, pack, result_var, cur_var])
                result_msg = result_var.getvalue()
                # 获取游标并读取数据
                out_cursor = cur_var.getvalue()
                if out_cursor:
                    columns = [col[0] for col in out_cursor.description]
                    rows = out_cursor.fetchall()
                else:
                    columns = []
                    rows = []
                return result_msg, columns, rows
    except oracledb.Error as e:
        return f"数据库错误: {e}", None, None
    except Exception as e:
        return f"异常: {e}", None, None
def insert_routeR_DIP_PACK(dip,pack,router,emp_no):
    """
    调用存储过程 SAJET.SJ_INSERT_R_ROUTE 插入新的 DIP/PACK 流程组合。
    :param dip:      DIP 流程名称
    :param pack:     PACK 流程名称
    :param router:   新路由名称（RouteNameNew）
    :param emp_no:   操作员工号（EMP_NO_IN）
    :return: ( message: str)
             message: 'OK',或者ERROR存储过程返回的状态信息或异常描述
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                result_var = cursor.var(oracledb.DB_TYPE_VARCHAR)
                cursor.callproc("SAJET.SJ_INSERT_R_ROUTE",
                                [dip, pack, router, emp_no, result_var])
                result_msg = result_var.getvalue()
                conn.commit()
                return result_msg
    except oracledb.Error as e:
        return f"数据库错误: {e}"
    except Exception as e:
        return f"异常: {e}"
def fetch_route_steps(route_name):
    """
    根据流程名称获取该流程的所有步骤（进程名、是否必选）
    :param route_name:
    :return: (columns, rows) 成功；如果失败或没数据，返回 (None, None) 或 ([], [])
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                # SQL：根据流程名称查询步骤，显示进程名称和是否必选，按步骤顺序排序
                sql = """
                    SELECT U.PROCESS_NAME, D.NECESSARY
                    FROM SAJET.SYS_ROUTE_DETAIL D
                    INNER JOIN SAJET.SYS_ROUTE R
                        ON D.ROUTE_ID = R.ROUTE_ID
                    INNER JOIN SAJET.SYS_PROCESS U
                        ON D.NEXT_PROCESS_ID = U.PROCESS_ID
                    WHERE R.ROUTE_NAME = :route_name AND SEQ = STEP
                    ORDER BY D.SEQ ASC
                """
                cursor.execute(sql, route_name=route_name)
                rows = cursor.fetchall()
                columns = ["进程", "是否必过"]   # 显示列名
                return columns, rows
    except oracledb.Error as e:
        return [], []
    except Exception as e:
        return [], []
def check_route_exi(route_name):
    """
    根据流程名称获取该流程的所有步骤（进程名、是否必选）
    :param route_name: 流程名称
    :return: success
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                sql = """
                    SELECT *
                    FROM SAJET.SYS_ROUTE R
                    WHERE R.ROUTE_NAME = :route_name 
                """
                cursor.execute(sql, route_name=route_name)
                rows = cursor.fetchall()
                columns = ["进程", "是否必过"]   # 显示列名
                return columns, rows
    except oracledb.Error as e:
        return [], []
    except Exception as e:
        return [], []
def get_route_sn(sn):
    """根据序列号获取其对应的流程ID和名称"""
    if not sn:
        return ['ROUTE_ID', 'ROUTE_NAME'], []
    sql = """
        SELECT ROUTE_ID, ROUTE_NAME
        FROM SAJET.SYS_ROUTE
        WHERE ROUTE_ID IN (
            SELECT ROUTE_ID
            FROM SAJET.G_SN_TRAVEL
            WHERE SERIAL_NUMBER = :sn
            GROUP BY ROUTE_ID
        )
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, sn=sn)
                rows = cursor.fetchall()
                columns = ['ROUTE_ID', 'ROUTE_NAME']
                return 'OK',columns, rows
    except oracledb.Error as e:
        return f"数据库错误: {e}", None, None
    except Exception as e:
        return f"异常: {e}", None, None
def fetch_sn_mac(sn):
    """
    根据序列号 SN 查询对应的 MAC、工单、状态、时间等信息。
    :param sn: 序列号字符串
    :return: (result,columns, rows)，result(OK/ERROR),columns 为列名列表，rows 为数据行列表。
             若查询失败或无数据，返回 (error,[], [])。
    """
    if not sn:
        return "SN 不能为空",[], []
    sql = """
        SELECT M.WORK_ORDER,
            M.SERIAL_NUMBER,
            M.MAC,
            NVL(P.PROCESS_NAME, 'None') AS CURRENT_PROCESS,
            NVL(R.PROCESS_NAME, 'None') AS WIP_PROCESS,
            M.UPDATE_USERID,
            M.UPDATE_TIME,
            M.UUID,
            M.CUSTOMER_SN
        FROM SAJET.G_WO_MAC M
        LEFT JOIN SAJET.G_SN_STATUS S ON S.SERIAL_NUMBER = M.SERIAL_NUMBER
        LEFT JOIN SAJET.SYS_PROCESS P ON P.PROCESS_ID = S.PROCESS_ID
        LEFT JOIN SAJET.SYS_PROCESS R ON R.PROCESS_ID = S.WIP_PROCESS
        WHERE M.SERIAL_NUMBER IN (:sn)
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, sn=sn)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if rows else []
                return "OK",columns, rows
    except oracledb.Error as e:
        return f"数据库错误: {e}",[], []
    except Exception as e:
        return f"异常: {e}",[], []
def delete_sn_mac(sn, mac):
    """
    删除 SAJET.G_WO_MAC 表中指定 SN 和 MAC 的记录。
    :param sn:  序列号
    :param mac: MAC地址
    :return: ( message: str)
            message: 操作结果描述
    """
    if not sn or not mac:
        return False, "SN 和 MAC 不能为空"
    sql = """
        DELETE FROM SAJET.G_WO_MAC
        WHERE SERIAL_NUMBER = :sn OR MAC = :mac
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, sn=sn, mac=mac)
                rowcount = cursor.rowcount  # 受影响的行数
                conn.commit()
                if rowcount > 0:
                    return "OK"
                else:
                    return f"未找到匹配的记录 (SN: {sn}, MAC: {mac})"
    except oracledb.Error as e:
        return f"数据库错误: {e}"
    except Exception as e:
        return f"异常: {e}"
def fetch_process():
    """
    查询 SAJET.SYS_PROCESS 表中指定的启用流程。
    返回 (msg,columns, rows)，其中msg,为信息 columns 为列名列表，rows 为数据行列表。
    若查询失败，返回 ([], [])。
    """
    # 固定的流程名称列表
    process_list = [
        'AOI', 'BAOI', 'BSPI', 'BSVI', 'PCB_INPUT', 'SMT_INPUT', 'SPI', 'SVI',
        'S_AOI', 'BottomVI', 'CHANGE_SN', 'CHECK_BAT', 'CHECK_CPU', 'CHECK_FAN',
        'DAOI', 'DICT', 'DInput', 'DOA_VI', 'FQC-CHK', 'HEATSINK', 'MDA', 'PLATE',
        'TopVI', 'CHK_LABEL1', 'Cutboard', 'F1Test', 'F2Test', 'F3Test', 'F4Test',
        'GLUE_SVI', 'Power On Test', 'CHECKSN', 'CHECK_BOX', 'CHKPART', 'CHKSSN',
        'CHK_MAC', 'CHK_PART', 'CQC', 'ColorCheck', 'OQC', 'OQC_F1', 'PACKING',
        'PBottomVI', 'PK_AOI', 'PK_VBATT', 'PTopVI', 'Packing1', 'PrintLabel',
        'QC_CHK', 'SOCPT0PVl'
    ]

    # 构建 SQL 和绑定变量
    # 使用动态占位符，例如 :p0, :p1, ...
    placeholders = ','.join([f':p{i}' for i in range(len(process_list))])
    sql = f"""
        SELECT *
        FROM SAJET.SYS_PROCESS P
        WHERE P.ENABLED = 'Y'
          AND P.PROCESS_NAME IN ({placeholders})
        ORDER BY P.STAGE_ID, P.PROCESS_NAME
    """
    # 绑定参数以字典形式提供
    bind_vars = {f'p{i}': name for i, name in enumerate(process_list)}

    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, bind_vars)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if rows else []
                return "OK",columns, rows
    except oracledb.Error as e:
        return f"数据库错误: {e}",[], []
    except Exception as e:
        return f"异常: {e}",[], []
def fetch_route_process(must_have_str, must_not_str):
    """
    调用存储过程 SAJET.FIND_ROUTE_PROCESS，根据必过/必不过流程列表查找满足条件的路由。
    :param must_have_str: 必过流程名称，逗号分隔，如 'F1Test,PBottomVI,PTopVI,PACKING,OQC'
    :param must_not_str:  必不过流程名称，逗号分隔，如 'F2Test,F4Test'
    :return: (msg, columns, rows)  msg 为 'OK' 或错误信息，columns 为 ['ROUTE_NAME']，rows 为路由名称列表
    """
    if not must_have_str and not must_not_str:
        return "必须提供至少一个流程列表", [], []
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                res_var = cursor.var(oracledb.DB_TYPE_VARCHAR)
                cur_var = cursor.var(oracledb.DB_TYPE_CURSOR)
                cursor.callproc("SAJET.FIND_ROUTE_PROCESS", [must_have_str, must_not_str, res_var, cur_var])
                msg = res_var.getvalue()
                out_cursor = cur_var.getvalue()
                rows = []
                if out_cursor:
                    for row in out_cursor:
                        rows.append(row[0])
                else:
                    rows = []
                if msg != 'OK':
                    return msg, [], []
                columns = ['ROUTE_NAME']
                return "OK", columns, rows
    except oracledb.Error as e:
        return f"数据库错误: {e}", [], []
    except Exception as e:
        return f"异常: {e}", [], []
def copy_route_new(old_route,new_route,emp,is_overwrite=False):
    """
    调用存储过程 SAJET.SJ_COPY_ROUTE 复制流程。
    :param old_route: 原流程名称
    :param new_route: 新流程名称
    :param emp:       操作员工号
    :param is_overwrite: 是否覆盖已存在的流程，True 时传 'Y'，False 传 'N'
    :return: (message: str)
    """
    if not old_route or not new_route or not emp:
        return False, "参数不完整：原流程、新流程、工号均不能为空"

    overwrite_flag = 'Y' if is_overwrite else 'N'

    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                result_var = cursor.var(oracledb.DB_TYPE_VARCHAR)
                cursor.callproc("SAJET.SJ_COPY_ROUTE", [old_route, new_route, emp, overwrite_flag, result_var])
                result_msg = result_var.getvalue()
                return result_msg
    except oracledb.Error as e:
        return f"数据库错误: {e}"
    except Exception as e:
        return f"异常: {e}"
def insert_ht_mac(sn, mac):
    """
    将 SAJET.G_WO_MAC 中指定 SN 和 MAC 的记录插入到 SAJET.G_HT_WO_MAC（历史表）中。
    :param sn:  序列号
    :param mac: MAC地址
    :return: (message: str)
    """
    if not sn or not mac:
        return False, "SN 和 MAC 不能为空"
    sql = """
        INSERT INTO SAJET.G_HT_WO_MAC
        SELECT * FROM SAJET.G_WO_MAC W
        WHERE W.SERIAL_NUMBER = :sn OR W.MAC = :mac
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, sn=sn, mac=mac)
                rowcount = cursor.rowcount
                conn.commit()
                if rowcount > 0:
                    return "OK"
                else:
                    return "未找到匹配的记录，插入失败"
    except oracledb.Error as e:
        return f"数据库错误: {e}"
    except Exception as e:
        return f"异常: {e}"
def fetch_server_gateway():
    """
    查询启用的服务器和网关信息（关联 TGS_SERVER_BASE 和 TGS_GATEWAY_BASE）。
    返回 (msg, columns, rows)
    """
    sql = """
        SELECT *
        FROM SAJET.TGS_SERVER_BASE S
        INNER JOIN SAJET.TGS_GATEWAY_BASE G ON G.SERVER_ID = S.SERVER_ID
        WHERE S.ENABLED = 'Y' AND G.ENABLED = 'Y'
        ORDER BY S.SERVER_DESC_E
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if rows else []
                return "OK", columns, rows
    except oracledb.Error as e:
        return f"数据库错误: {e}", [], []
    except Exception as e:
        return f"异常: {e}", [], []
def fetch_gateway_ip(server, driver, gateway):
    """
    调用存储过程 SAJET.GET_GATEWAY_IP，获取网关 IP 信息。
    :param server:  服务器 ID（NUMBER）
    :param driver:  驱动 ID（NUMBER）
    :param gateway: ID（NUMBER）
    :return: (tres, ip)
             tres: 存储过程返回的状态字符串，'OK' 表示成功
             ip:   IP 地址字符串，若失败则为 None
    """
    if server is None or driver is None or not gateway:
        return "参数不完整：server, driver, gateway 均不能为空", None

    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                tres_var = cursor.var(oracledb.DB_TYPE_VARCHAR)
                ip_var = cursor.var(oracledb.DB_TYPE_VARCHAR)
                cursor.callproc("SAJET.GET_GATEWAY_IP", [server, gateway,driver ,tres_var, ip_var])
                tres = tres_var.getvalue()
                ip = ip_var.getvalue()
                return tres, ip
    except oracledb.Error as e:
        return f"数据库错误: {e}", None
    except Exception as e:
        return f"异常: {e}", None
def get_terminal_status(server, gateway, index):
    """
    调用存储过程 SAJET.SJ_GET_TERMINAL_STATUS，获取终端状态信息。
    :param server:  服务器 ID (NUMBER)
    :param gateway: 网关 ID (NUMBER)
    :param index:  索引 ID (NUMBER)
    :return: (tres, columns, rows)
             tres: 存储过程返回的状态字符串（如 'OK'）
             columns: 游标结果集的列名列表
             rows: 数据行列表（元组列表）
    """
    try:
        server = int(server)
        index = int(index)
        gateway = int(gateway)
    except (TypeError, ValueError):
        return "参数类型错误：server, index, gateway 必须为数字", [], []

    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                tres_var = cursor.var(oracledb.DB_TYPE_VARCHAR)
                cur_var = cursor.var(oracledb.DB_TYPE_CURSOR)
                # 存储过程参数顺序：SERVER, GATEWAY, DRIVER, TRES, p_cursor
                cursor.callproc("SAJET.SJ_GET_TERMINAL_STATUS", [server, gateway, index, tres_var, cur_var])
                tres = tres_var.getvalue()
                out_cursor = cur_var.getvalue()
                if out_cursor:
                    columns = [col[0] for col in out_cursor.description]
                    rows = out_cursor.fetchall()
                else:
                    columns = []
                    rows = []
                return tres, columns, rows
    except oracledb.Error as e:
        return f"数据库错误: {e}", [], []
    except Exception as e:
        return f"异常: {e}", [], []
def fetch_format_sn_ppid(sql_where):
    """
    根据给定的 WHERE 条件查询 ECS_PPID_PCB_CODE 表。
    :param sql_where: 条件字符串，如 "STRSMTSN IN ('123') OR PCB_QRCODE IN ('ABC')"
    :return: (msg, columns, rows)
    """
    if not sql_where:
        return "查询条件不能为空", [], []

    sql = f"SELECT * FROM SAJET.ECS_PPID_PCB_CODE WHERE {sql_where}"

    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if rows else []
                return "OK", columns, rows
    except oracledb.Error as e:
        return f"数据库错误: {e}", [], []
    except Exception as e:
        return f"异常: {e}", [], []
def fetch_sn_ppid(sn, pcb):
    """
    根据给定的 sn, pcb 条件查询 ECS_PPID_PCB_CODE 表。
    :param sn, pcb: 条件字符串，如 "STRSMTSN = :sn OR PCB_QRCODE =:pcb"
    :return: (msg, columns, rows)
    """
    if not sn and not pcb:
        return "查询条件不能为空", [], []

    sql = f"SELECT * FROM SAJET.ECS_PPID_PCB_CODE WHERE STRSMTSN = :sn OR PCB_QRCODE = :pcb"

    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql,sn=sn,pcb=pcb)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if rows else []
                return "OK", columns, rows
    except oracledb.Error as e:
        return f"数据库错误: {e}", [], []
    except Exception as e:
        return f"异常: {e}", [], []
def fetch_format_sn_bga(sql_where):
    """
    根据给定的 WHERE 条件查询 G_SN_KEYPARTS 表。
    :param sql_where: 条件字符串，如 "SERIAL_NUMBER IN ('123') OR ITEM_PART_SN IN ('ABC')"
    :return: (msg, columns, rows)
    """
    if not sql_where:
        return "查询条件不能为空", [], []

    sql = f"SELECT * FROM SAJET.G_SN_KEYPARTS WHERE {sql_where}"

    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if rows else []
                return "OK", columns, rows
    except oracledb.Error as e:
        return f"数据库错误: {e}", [], []
    except Exception as e:
        return f"异常: {e}", [], []
def fetch_format_sn(sql_where):
    """
    根据给定的 WHERE 条件查询 G_SN_STATUS 表。
    :param sql_where: 条件字符串，如 "SERIAL_NUMBER IN ('123')"
    :return: (msg, columns, rows)
    """
    if not sql_where:
        return "查询条件不能为空", [], []

    sql = f"SELECT * FROM SAJET.G_SN_STATUS WHERE {sql_where}"

    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if rows else []
                return "OK", columns, rows
    except oracledb.Error as e:
        return f"数据库错误: {e}", [], []
    except Exception as e:
        return f"异常: {e}", [], []
def fetch_sn_keyparts(sn):
    """
    根据给定的 SN 条件查询 G_SN_KEYPARTS 表。
    :param SN: SERIAL_NUMBER
    :return: (msg, columns, rows)
    """
    if not sn:
        return "SN 不能为空", [], []
    sql = """
        SELECT K.WORK_ORDER,
               K.SERIAL_NUMBER,
               P.PROCESS_NAME,
               PA.PART_NO,
               PA.PART_TYPE,
               K.ITEM_PART_SN,
               K.ITEM_GROUP,
               K.VERSION,
               E.EMP_NAME,
               K.UPDATE_TIME
        FROM SAJET.G_SN_KEYPARTS K
        LEFT JOIN SAJET.SYS_PROCESS P ON P.PROCESS_ID = K.PROCESS_ID
        LEFT JOIN SAJET.SYS_PART PA ON PA.PART_ID = K.ITEM_PART_ID
        LEFT JOIN SAJET.SYS_EMP E ON E.EMP_ID = K.UPDATE_USERID
        WHERE K.SERIAL_NUMBER = :sn
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, sn=sn)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if rows else []
                return "OK", columns, rows
    except oracledb.Error as e:
        return f"数据库错误: {e}", [], []
    except Exception as e:
        return f"异常: {e}", [], []
def insert_ht_sn_keypart(sn, part, time):
    """
    将 G_SN_KEYPARTS 中指定 SN、料件SN和更新时间匹配的记录插入到历史表 G_HT_SN_KEYPARTS。
    :param sn:   序列号
    :param part: 料件SN (ITEM_PART_SN)
    :param time: 更新时间 (UPDATE_TIME)
    :return: ( message: str)
    """
    if not sn or not part or not time:
        return False, "SN、料件SN和更新时间不能为空"

    sql = """
        INSERT INTO SAJET.G_HT_SN_KEYPARTS
        SELECT * FROM SAJET.G_SN_KEYPARTS K
        WHERE K.SERIAL_NUMBER = :sn
          AND K.ITEM_PART_SN = :part
          AND K.UPDATE_TIME = TO_DATE(:time, 'YYYY-MM-DD HH24:MI:SS')
    """

    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, sn=sn, part=part, time=time)
                rowcount = cursor.rowcount
                conn.commit()
                if rowcount > 0:
                    return "OK"
                else:
                    return "未找到匹配的记录，插入失败"
    except oracledb.Error as e:
        return f"数据库错误: {e}"
    except Exception as e:
        return f"异常: {e}"
def delete_sn_keypart(sn, part, time):
    """
    删除 G_SN_KEYPARTS 中匹配 SN、料件SN和时间戳的记录。
    :param sn:   序列号
    :param part: 料件SN (ITEM_PART_SN)
    :param time: 更新时间 (UPDATE_TIME)
    :return: 'OK' 成功，否则返回错误信息字符串
    """
    if not sn or not part or not time:
        return "SN、料件SN和更新时间不能为空"

    sql = """
        DELETE FROM SAJET.G_SN_KEYPARTS K
        WHERE K.SERIAL_NUMBER = :sn
          AND K.ITEM_PART_SN = :part
          AND K.UPDATE_TIME = TO_DATE(:time, 'YYYY-MM-DD HH24:MI:SS')
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, sn=sn, part=part, time=time)
                rowcount = cursor.rowcount
                conn.commit()
                if rowcount > 0:
                    return "OK"
                else:
                    return "未找到匹配的记录，删除失败"
    except oracledb.Error as e:
        return f"数据库错误: {e}"
    except Exception as e:
        return f"异常: {e}"
def insert_ht_sn_keyparts(sn):
    """
    将 G_SN_KEYPARTS 中指定 SN、料件SN和更新时间匹配的记录插入到历史表 G_HT_SN_KEYPARTS。
    :param sn:   序列号
    :return: ( message: str)
    """
    if not sn:
        return False, "SN 不能为空"

    sql = """
        INSERT INTO SAJET.G_HT_SN_KEYPARTS
        SELECT * FROM SAJET.G_SN_KEYPARTS K
        WHERE K.SERIAL_NUMBER = :sn
    """

    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, sn=sn)
                rowcount = cursor.rowcount
                conn.commit()
                if rowcount > 0:
                    return "OK"
                else:
                    return "未找到匹配的记录，插入失败"
    except oracledb.Error as e:
        return f"数据库错误: {e}"
    except Exception as e:
        return f"异常: {e}"
def delete_sn_keyparts(sn):
    """
    删除 G_SN_KEYPARTS 中匹配 SN、料件SN和时间戳的记录。
    :param sn:   序列号
    :return: 'OK' 成功，否则返回错误信息字符串
    """
    if not sn:
        return "SN 不能为空"

    sql = """
        DELETE FROM SAJET.G_SN_KEYPARTS K
        WHERE K.SERIAL_NUMBER = :sn
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, sn=sn)
                rowcount = cursor.rowcount
                conn.commit()
                if rowcount > 0:
                    return "OK"
                else:
                    return "未找到匹配的记录，删除失败"
    except oracledb.Error as e:
        return f"数据库错误: {e}"
    except Exception as e:
        return f"异常: {e}"
def delete_sn_ppid(sn, ppid):
    """
    删除 ECS_PPID_PCB_CODE 表中匹配 STRSMTSN 和 PCB_QRCODE 的记录。
    :param sn:   序列号 (STRSMTSN)
    :param ppid: PCB 二维码 (PCB_QRCODE)
    :return: 'OK' 成功，否则返回错误信息字符串
    """
    if not sn or not ppid:
        return "SN 和 PPID 不能为空"

    sql = """
        DELETE FROM SAJET.ECS_PPID_PCB_CODE P
        WHERE P.STRSMTSN = :sn
          AND P.PCB_QRCODE = :ppid
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, sn=sn, ppid=ppid)
                rowcount = cursor.rowcount
                conn.commit()
                if rowcount > 0:
                    return "OK"
                else:
                    return "未找到匹配的记录，删除失败"
    except oracledb.Error as e:
        return f"数据库错误: {e}"
    except Exception as e:
        return f"异常: {e}"
def fetch_carton_keyparts(carton):
    """
    根据箱号查询所有关联 SN 的关键部件信息。
    :param carton: 箱号
    :return: (msg, columns, rows)
             msg: 'OK' 或错误信息
             columns: 列名列表
             rows: 数据行列表
    """
    if not carton:
        return "箱号不能为空", [], []

    sql = """
        SELECT K.WORK_ORDER,
               K.SERIAL_NUMBER,
               P.PROCESS_NAME,
               PA.PART_NO,
               PA.PART_TYPE,
               K.ITEM_PART_SN,
               K.ITEM_GROUP,
               K.VERSION,
               E.EMP_NAME,
               K.UPDATE_TIME
        FROM SAJET.G_SN_KEYPARTS K
        LEFT JOIN SAJET.SYS_PROCESS P ON P.PROCESS_ID = K.PROCESS_ID
        LEFT JOIN SAJET.SYS_PART PA ON PA.PART_ID = K.ITEM_PART_ID
        LEFT JOIN SAJET.SYS_EMP E ON E.EMP_ID = K.UPDATE_USERID
        WHERE K.SERIAL_NUMBER IN (SELECT S.SERIAL_NUMBER FROM SAJET.G_SN_STATUS S WHERE S.CARTON_NO = :carton)
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, carton=carton)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if rows else []
                return "OK", columns, rows
    except oracledb.Error as e:
        return f"数据库错误: {e}", [], []
    except Exception as e:
        return f"异常: {e}", [], []
def delete_keyparts_wo_process(wo, process, list_sn):
    """
    删除指定工单、站位下所有 SN 的记录。
    :param wo:       工单号
    :param process:  站位名称（PROCESS_NAME）
    :param list_sn:  SN 列表
    :return: 'OK' 成功，否则返回错误信息字符串
    """
    if not wo or not process or not list_sn:
        return "参数不完整：工单、站位、SN列表均不能为空"
   
    if not list_sn:
        return "SN列表为空"
    placeholders = ','.join([f':sn{i}' for i in range(len(list_sn))])
    sql = f"""
        DELETE FROM SAJET.G_SN_KEYPARTS K
        WHERE K.PROCESS_ID = (SELECT PROCESS_ID FROM SAJET.SYS_PROCESS WHERE PROCESS_NAME = :process)
          AND K.WORK_ORDER = :wo
          AND K.SERIAL_NUMBER IN ({placeholders})
    """
    bind_vars = {'process': process, 'wo': wo}
    for i, sn in enumerate(list_sn):
        bind_vars[f'sn{i}'] = sn
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, bind_vars)
                rowcount = cursor.rowcount
                conn.commit()
                if rowcount > 0:
                    return "OK"
                else:
                    return "未找到匹配的记录"
    except oracledb.Error as e:
        return f"数据库错误: {e}"
    except Exception as e:
        return f"异常: {e}"
def insert_ht_keyarts_wo_process(wo, process, list_sn):
    """
    将指定工单、站位和 SN 列表对应的记录插入到历史表 G_HT_SN_KEYPARTS。
    :param wo:       工单号
    :param process:  站位名称（PROCESS_NAME）
    :param list_sn:  SN 列表
    :return: 'OK' 成功，否则返回错误信息字符串
    """
    if not wo or not process or not list_sn:
        return "参数不完整：工单、站位、SN列表均不能为空"

    if not list_sn:
        return "SN列表为空"
    
    placeholders = ','.join([f':sn{i}' for i in range(len(list_sn))])
    sql = f"""
        INSERT INTO SAJET.G_HT_SN_KEYPARTS
        SELECT K.*
        FROM SAJET.G_SN_KEYPARTS K
        WHERE K.PROCESS_ID = (SELECT PROCESS_ID FROM SAJET.SYS_PROCESS WHERE PROCESS_NAME = :process)
          AND K.WORK_ORDER = :wo
          AND K.SERIAL_NUMBER IN ({placeholders})
    """
    bind_vars = {'process': process, 'wo': wo}
    for i, sn in enumerate(list_sn):
        bind_vars[f'sn{i}'] = sn

    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, bind_vars)
                rowcount = cursor.rowcount
                conn.commit()
                if rowcount > 0:
                    return "OK"
                else:
                    return "未找到匹配的记录，备份失败"
    except oracledb.Error as e:
        return f"数据库错误: {e}"
    except Exception as e:
        return f"异常: {e}"
def fetch_keyparts_rework(rewk):
    """
    根据重工号查询所有关联 SN 的关键部件信息。
    :param rewk: 重工号
    :return: (msg, columns, rows)
             msg: 'OK' 或错误信息
             columns: 列名列表
             rows: 数据行列表
    """
    if not rewk:
        return "重工号不能为空", [], []

    sql = """
         SELECT K.WORK_ORDER,
               K.SERIAL_NUMBER,
               P.PROCESS_NAME,
               PA.PART_NO,
               PA.PART_TYPE,
               K.ITEM_PART_SN,
               K.ITEM_GROUP,
               K.VERSION,
               E.EMP_NAME,
               K.UPDATE_TIME
        FROM SAJET.G_SN_KEYPARTS K
        LEFT JOIN SAJET.SYS_PROCESS P ON P.PROCESS_ID = K.PROCESS_ID
        LEFT JOIN SAJET.SYS_PART PA ON PA.PART_ID = K.ITEM_PART_ID
        LEFT JOIN SAJET.SYS_EMP E ON E.EMP_ID = K.UPDATE_USERID
        WHERE K.SERIAL_NUMBER IN (SELECT S.SERIAL_NUMBER FROM SAJET.G_SN_STATUS S WHERE S.REWORK_NO = :rewk)
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, rewk=rewk)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if rows else []
                return "OK", columns, rows
    except oracledb.Error as e:
        return f"数据库错误: {e}", [], []
    except Exception as e:
        return f"异常: {e}", [], []
def update_ppid_sn(sn, ppid, new_sn):
    """
    更新 ECS_PPID_PCB_CODE 表中的 STRSMTSN 字段。
    :param sn:      原 STRSMTSN
    :param ppid:    原 PCB_QRCODE
    :param new_sn:  新 STRSMTSN
    :return: 'OK' 或错误信息
    """
    if not sn or not ppid or not new_sn:
        return "原 SN、PPID 和新 SN 均不能为空"

    sql = """
        UPDATE SAJET.ECS_PPID_PCB_CODE P
        SET P.STRSMTSN = :new_sn
        WHERE P.STRSMTSN = :sn AND P.PCB_QRCODE = :ppid
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, new_sn=new_sn, sn=sn, ppid=ppid)
                rowcount = cursor.rowcount
                conn.commit()
                if rowcount > 0:
                    return "OK"
                else:
                    return "未找到匹配的记录，更新失败"
    except oracledb.Error as e:
        return f"数据库错误: {e}"
    except Exception as e:
        return f"异常: {e}"
def update_ppid_pcb(sn, ppid, new_ppid):
    """
    更新 ECS_PPID_PCB_CODE 表中的 PCB_QRCODE 字段。
    :param sn:       原 STRSMTSN
    :param ppid:     原 PCB_QRCODE
    :param new_ppid: 新 PCB_QRCODE
    :return: 'OK' 或错误信息
    """
    if not sn or not ppid or not new_ppid:
        return "原 SN、PPID 和新 PPID 均不能为空"

    sql = """
        UPDATE SAJET.ECS_PPID_PCB_CODE P
        SET P.PCB_QRCODE = :new_ppid
        WHERE P.STRSMTSN = :sn AND P.PCB_QRCODE = :ppid
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, new_ppid=new_ppid, sn=sn, ppid=ppid)
                rowcount = cursor.rowcount
                conn.commit()
                if rowcount > 0:
                    return "OK"
                else:
                    return "未找到匹配的记录，更新失败"
    except oracledb.Error as e:
        return f"数据库错误: {e}"
    except Exception as e:
        return f"异常: {e}"
def fetch_work_order(work):
    """
    根据工单号查询工单详细信息。
    :param work: 工单号
    :return: (msg, columns, rows)
    WO_STATUS -> 0:initial,1:prepare,2:release,3:work in process,4:hold,5:cancel,6:complete
    """
    if not work:
        return "工单号不能为空", [], []

    sql = """
        SELECT W.WORK_ORDER,
            P.PART_NO,
            W.WO_RULE,
            W.VERSION,
            W.WO_STATUS,
            CASE 
                WHEN W.WO_STATUS = 0 THEN 'initial'
                WHEN W.WO_STATUS = 1 THEN 'prepare'
                WHEN W.WO_STATUS = 2 THEN 'release'
                WHEN W.WO_STATUS = 3 THEN 'work in process'
                WHEN W.WO_STATUS = 4 THEN 'hold'
                WHEN W.WO_STATUS = 5 THEN 'cancel'
                WHEN W.WO_STATUS = 6 THEN 'complete'
                ELSE 'unknown'
            END AS WO_STATUS_DESC,
            W.TARGET_QTY,
            W.INPUT_QTY,
            W.OUTPUT_QTY,
            R.ROUTE_NAME,
            PE.PROCESS_NAME AS START_PROCESS,
            PA.PROCESS_NAME AS END_PROCESSS
        FROM SAJET.G_WO_BASE W
        LEFT JOIN SAJET.SYS_PART P ON P.PART_ID = W.MODEL_ID
        LEFT JOIN SAJET.SYS_ROUTE R ON R.ROUTE_ID = W.ROUTE_ID
        LEFT JOIN SAJET.SYS_PROCESS PE ON PE.PROCESS_ID = W.START_PROCESS_ID
        LEFT JOIN SAJET.SYS_PROCESS PA ON PA.PROCESS_ID = W.END_PROCESS_ID
        WHERE W.WORK_ORDER = :work
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, work=work)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if rows else []
                return "OK", columns, rows
    except oracledb.Error as e:
        return f"数据库错误: {e}", [], []
    except Exception as e:
        return f"异常: {e}", [], []
def update_woder_status(wo, status):
    """
    更新工单的状态。
    :param wo:     工单号
    :param status: 新状态（数字，0-6）
    :return: 'OK' 或错误信息
    """
    if not wo:
        return "工单号不能为空"
    if status is None or not isinstance(status, int):
        return "状态值必须为整数"

    sql = """
        UPDATE SAJET.G_WO_BASE W
        SET W.WO_STATUS = :status
        WHERE W.WORK_ORDER = :wo
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, status=status, wo=wo)
                rowcount = cursor.rowcount
                conn.commit()
                if rowcount > 0:
                    return "OK"
                else:
                    return "未找到工单，更新失败"
    except oracledb.Error as e:
        return f"数据库错误: {e}"
    except Exception as e:
        return f"异常: {e}"
def fetch_smt_reelup(line, site, sn, time=3):
    """
    查询 SMT 飞达上料信息（远程表）。
    :param line: 线别 (STRLINEID)
    :param site: 站点 (STRSITE)
    :param sn:   飞达 SN (STRREELUPSN)
    :param time: 时间范围（天数），默认 3 天，查询 LOADRELLDATE >= TRUNC(SYSDATE)-time
    :return: (msg, columns, rows)
             msg: 'OK' 或错误信息
             columns: 列名列表
             rows: 数据行列表
    """
    if ((not line or not site) and not sn):
        return "请至少输入线别+站点组合，或输入SN", [], []

    # 时间参数验证
    try:
        time = int(time)
        if time < 0:
            return "时间范围不能为负数", [], []
    except (TypeError, ValueError):
        return "时间参数必须为整数", [], []

    sql = """
        SELECT *
        FROM TBL_SMT_REELUPINFO@smt T
        WHERE (T.STRLINEID = :line AND T.STRSITE = :site AND T.LOADRELLDATE >= TRUNC(SYSDATE) - :time)
           OR T.STRREELUPSN = :sn
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, line=line, site=site, sn=sn, time=time)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if rows else []
                return "OK", columns, rows
    except oracledb.Error as e:
        return f"数据库错误: {e}", [], []
    except Exception as e:
        return f"异常: {e}", [], []
def delete_smt_reelup(index, sn):
    """
    根据 NUMINDEX 删除 TBL_SMT_REELUPINFO@smt 中的记录。
    删除前检查该 SN 对应的记录总数，必须 >= 2 才允许删除（确保至少留有一条）。
    :param index: 记录主键索引 (NUMINDEX)
    :param sn:    料盘 SN (STRREELUPSN)
    :return: 'OK' 或错误信息字符串
    """
    if index is None:
        return "索引不能为空"
    if not sn:
        return "SN 不能为空"

    try:
        index = int(index)
    except (TypeError, ValueError):
        return "索引必须为数字"

    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                # 1. 查询该 SN 的记录总数
                count_sql = "SELECT COUNT(*) FROM TBL_SMT_REELUPINFO@smt WHERE STRREELUPSN = :sn"
                cursor.execute(count_sql, sn=sn)
                count = cursor.fetchone()[0]
                if count < 2:
                    return f"该料盘SN({sn})记录数不足，当前 {count} 条，至少需要2条才能删除"

                # 2. 执行删除
                del_sql = "DELETE FROM TBL_SMT_REELUPINFO@smt T WHERE T.NUMINDEX = :index"
                cursor.execute(del_sql, index=index)
                rowcount = cursor.rowcount
                conn.commit()
                if rowcount > 0:
                    return "OK"
                else:
                    return f"未找到 NUMINDEX={index} 的记录，删除失败"
    except oracledb.Error as e:
        return f"数据库错误: {e}"
    except Exception as e:
        return f"异常: {e}"
def fetch_lenovo_carton(carton):
    """
    查询联想装箱信息。若 carton 为空则查询全部，否则按箱号过滤。
    :param carton: 箱号
    :return: (msg, columns, rows)
             msg: 'OK' 或错误信息
             columns: 列名列表
             rows: 数据行列表
    """
    sql_base = """
        SELECT L.CARTON_NO,
               P.PART_NO,
               E.PDLINE_NAME,
               L.CLOSE_FLAG,
               L.CARTON_QTY,
               L.CREATE_TIME,
               L.TERMINAL_ID,
               L.OPTION_NUM1,
               T.TERMINAL_NAME
        FROM SAJET.G_PACK_CARTON_LENOVO L
        LEFT JOIN SAJET.SYS_PART P ON P.PART_ID = L.MODEL_ID
        LEFT JOIN SAJET.SYS_PDLINE E ON E.PDLINE_ID = L.PDLINE_ID
        LEFT JOIN SAJET.SYS_TERMINAL T ON T.TERMINAL_ID = L.TERMINAL_ID
    """

    if carton:
        sql = sql_base + " WHERE L.CARTON_NO = :carton"
        bind_vars = {'carton': carton}
    else:
        sql = sql_base
        bind_vars = {}

    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, bind_vars)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if rows else []
                return "OK", columns, rows
    except oracledb.Error as e:
        return f"数据库错误: {e}", [], []
    except Exception as e:
        return f"异常: {e}", [], []
def fetch_lenovo_carton_sn(carton):
    """
    查询联想箱号对应的 SN 列表。若 carton 为空则返回错误。
    :param carton: 箱号
    :return: (msg, columns, rows)
             msg: 'OK' 或错误信息
             columns: 列名列表
             rows: 数据行列表
    """
    if not carton:
        return "箱号不能为空", [], []

    sql = "SELECT * FROM SAJET.LENOVO_CARTON_SN WHERE CARTON_NO = :carton"
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, carton=carton)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if rows else []
                return "OK", columns, rows
    except oracledb.Error as e:
        return f"数据库错误: {e}", [], []
    except Exception as e:
        return f"异常: {e}", [], []
def update_lenovo_status(carton, status):
    """
    更新联想装箱表的 CLOSE_FLAG 状态。
    :param carton: 箱号
    :param status: 状态值（CLOSE_FLAG）
    :return: 'OK' 或错误信息字符串
    """
    if not carton:
        return "箱号不能为空"
    if status is None:
        return "状态不能为空"

    sql = """
        UPDATE SAJET.G_PACK_CARTON_LENOVO L
        SET L.CLOSE_FLAG = :status
        WHERE L.CARTON_NO = :carton
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, status=status, carton=carton)
                rowcount = cursor.rowcount
                conn.commit()
                if rowcount > 0:
                    return "OK"
                else:
                    return f"未找到箱号 {carton}，更新失败"
    except oracledb.Error as e:
        return f"数据库错误: {e}"
    except Exception as e:
        return f"异常: {e}"
def delete_lenovo_carton_sn(carton):
    """
    先删除联想箱号对应的所有 SN 记录，成功后更新主表 OPTION_NUM1 为 0。
    :param carton: 箱号
    :return: 'OK' 或错误信息字符串
    """
    if not carton:
        return "箱号不能为空"

    delete_sql = "DELETE FROM SAJET.LENOVO_CARTON_SN WHERE CARTON_NO = :carton"
    update_sql = """
        UPDATE SAJET.G_PACK_CARTON_LENOVO
        SET OPTION_NUM1 = 0
        WHERE CARTON_NO = :carton
    """

    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(delete_sql, carton=carton)
                cursor.execute(update_sql, carton=carton)
                conn.commit()
                return "OK"
    except oracledb.Error as e:
        return f"数据库错误: {e}"
    except Exception as e:
        return f"异常: {e}"
def update_erp_asus():
    """
    执行存储过程 SAJET.erp_to_sfis_asus（无参数）。
    :return: 'OK' 或错误信息字符串
    """
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.callproc("SAJET.erp_to_sfis_asus")
                conn.commit()
                return "OK"
    except oracledb.Error as e:
        return f"数据库错误: {e}"
    except Exception as e:
        return f"异常: {e}"
def insert_user_action(user_no, user_action, target=None, status=None, ip_address=None):
    """
    调用存储过程 SAJET.INSERT_VARLIKE_ACTION_LOG 插入用户操作日志。
    :param user_no:     工号（EMP_NO）
    :param user_action: 操作类型
    :param target:      操作目标（可选）
    :param status:      执行结果（可选）
    :param ip_address:  客户端IP（可选）
    :return: 'OK' 或错误信息字符串
    """
    if not user_no or not user_action:
        return "工号和操作类型不能为空"

    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                tres_var = cursor.var(oracledb.DB_TYPE_VARCHAR)
                cursor.callproc(
                    "SAJET.INSERT_VARLIKE_ACTION_LOG",
                    [user_no, user_action, target, status, ip_address, tres_var]
                )
                conn.commit()
                result = tres_var.getvalue()
                return result
    except oracledb.Error as e:
        return f"数据库错误: {e}"
    except Exception as e:
        return f"异常: {e}"
def fetch_erp_material(wo):
    """
    根据工单号查询 ERP 物料信息。
    :param wo: 工单号
    :return: (msg, columns, rows)
             msg: 'OK' 或错误信息
             columns: 列名列表
             rows: 数据行列表
    """
    if not wo:
        return "输入不能为空", [], []

    sql = "SELECT * FROM SAJET.ERP_WO_MATERIAL WHERE WORK_ORDER = :wo"
    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, wo=wo)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if rows else []
                return "OK", columns, rows
    except oracledb.Error as e:
        return f"数据库错误: {e}", [], []
    except Exception as e:
        return f"异常: {e}", [], []
def insert_erp_material(wo_part, ecs_part, decs, kpart):
    """
    调用存储过程 SAJET.INSERT_WO_MATERIA 插入 ERP 物料信息。
    :param wo_part:  工单号或料号（用于校验）
    :param ecs_part: ECS 料号
    :param decs:     ECS 描述
    :param kpart:    关键件号
    :return: 'OK' 或错误信息字符串
    """
    if not wo_part or not decs or not kpart:
        return "参数不完整：工单/料号、描述、关键件号均不能为空"

    try:
        with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
            with conn.cursor() as cursor:
                result_var = cursor.var(oracledb.DB_TYPE_VARCHAR)
                cursor.callproc(
                    "SAJET.INSERT_WO_MATERIA",
                    [wo_part, ecs_part, decs, kpart, result_var]
                )
                conn.commit()
                result = result_var.getvalue()
                return result
    except oracledb.Error as e:
        return f"数据库错误: {e}"
    except Exception as e:
        return f"异常: {e}"