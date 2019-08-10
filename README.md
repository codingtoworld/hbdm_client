# 火币合约交易客户端

## 文件列表
```markdown
│  config.py
│  favicon.ico
│  hbdm.py
│  mpg123.exe
│  README.md
│  requirements.txt
│  walf.mp3
│
├─api
│  │  utils.py
│  │  wss_hbdm.py
│  │  __init__.py
│
├─logs
└──pages
    │  chart.png
    │  datas_page.py
    │  hbdm_login.py
    │  hbdm_main.py
    │  user.png
    │  __init__.py

```

## 重要文件说明

* config.py 配置文件，需要配置服务器（必须）和默认登录账户（选配）
* favicon.ico 窗口图标文件
* hbdm.py 客户端入口文件，通过调用该文件，启动程序
* mpg123.exe 配合 下面的walf.mp3,在止损位置发出狼嚎，代表狼来了（自己可以定义喜欢的音乐）
* requirements.txt 需要安装的包
* api/utils.py 通用函数
* api/wss_hbdm.py 用于统计交易数据买卖单比例
* logs 目录存储当日操作次数，可以定义当日做多操作次数（一天的行情有限，日内操作越多，赚钱的概率越低）
* pages/chart.png 主窗口程序右侧的开仓标准化图（SOP）
* pages/datas_page.py 数据统计窗口
* pages/hbdm_login.py 登录窗口
* pages/hbdm_main.py 交易主窗口
* pages/user.png 登录窗口界面图标


## 如何使用

1、 需要先部署安装服务器端程序，参见服务器部分介绍和说明
> 参考 [服务器端项目](https://github.com/codingtoworld/hbdm_client)

2、 安装Python环境，建议使用Python3.6以上环境，可以参考以下视频：

[码上看世界](https://www.youtube.com/watch?v=M2uoep0i8AQ) 观看Windows部分。

3、安装requirements 要求的包
```
pip install -r requirements.txt
```

4、下载本源代码到目标目录，然后可以制作一个快捷方式：
> 例如项目下载到d:\hbdm_client，Python安装在c:\python，则快捷方式为：
>  C:\Python\pythonw.exe D:\hbdm_client\hbdm.py
> 注意使用pythonw.exe 而不是 python.exe，否则将会出现黑色console窗口

5、配置参数，打开config.py
```markdownWe
SERVER_URL = 'https://XXX'        # 配置行情交易服务器的URL
SERVER_WSS = 'wss://XXX/wss'      # 配置行情交易服务器的b Socket server
DEFAULT_USER = ''                 # 配置默认登录的账户，对应服务器上的账户
MAX_PROCESS_COUNTS = 8            # 当日最大执行操作次数
```

6、运行该快捷方式启动，直接双击运行即可

登录窗口：

![image](https://raw.githubusercontent.com/codingtoworld/hbdm_client/master/login_form.png)

主窗口：

![image](https://raw.githubusercontent.com/codingtoworld/hbdm_client/master/main_form.png)
