# OraclePythonTool
#查看python是否是32位，不对配置环境变量
输入： python -c "import platform; print(platform.architecture())"
输出('32bit', 'WindowsPE')
#环境变量
C:\Users\leihuang.ECS\AppData\Local\Programs\Python\Python313-32
C:\Users\leihuang.ECS\AppData\Local\Programs\Python\Python313-32\Scripts
#py基础库依赖安装
pip install oracledb
pip install cryptography --only-binary :all:
##封装指令 varlike.spec或者spec无法进行封装 第一次封装许执行下述指令，会生成一个spec用于后续封装
pyinstaller -w -D --add-data "./instantclient_19_31;instantclient_19_31" --icon=favicon.ico .\varlike.py
##spec 封装
pyinstaller .\varlike.spec