#! /usr/bin/env python
#  -*- coding: utf-8 -*-
try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

try:
    import ttk
    py3 = False
except ImportError:
    import tkinter.ttk as ttk
    py3 = True

try:    # py3
    from urllib.parse import urlparse, urlencode, quote, unquote
except ImportError:     # py2
    from urlparse import urlparse
    from urllib import urlencode, quote, unquote
import requests
from pages.hbdm_login import LoginPage
import urllib3
from config import *


class WinMain:

    root = tk.Tk()
    top_level = tk.Toplevel(root)
    login_page = None
    main_page = None
    is_show_dp = False

    httpClient = None

    def __init__(self):
        self.root.withdraw()
        self.login_page = LoginPage(self.top_level, self)
        self.top_level.protocol("WM_DELETE_WINDOW", self.on_close_page)
        self.baseUrl = SERVER_URL
        self.baseWss = SERVER_WSS
        self.httpClient = requests.session()
        # self.top_level.destroy()

    def on_close_page(self):
        self.top_level.destroy()
        self.root.destroy()

    def start(self):
        self.root.mainloop()

    def http_get_request(self, url, params=None, add_to_headers=None):
        headers = {
            "Accept": "application/json",
            'Accept-Language': 'zh-cn',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 7_1_2 like Mac OS X) > AppleWebKit/537.51.2' +
                          ' (KHTML, like Gecko) Mobile/11D257 > MicroMessenger/6.0.1 NetType/WIFI',
        }
        if add_to_headers:
            headers.update(add_to_headers)
        if params is not None:
            postdata = urlencode(params)
            url = url + "&" + postdata if url.find('?') >= 0 else url + "?" + postdata

        try:
            response = self.httpClient.get(url, headers=headers, timeout=30, verify=False)
            if response.status_code == 200:
                return response.json()
            else:
                print("%s\r\n%s" % (url, response.content))
                return False
        except BaseException as e:
            print("httpGet failed, detail is:%s" % str(e))
            return False

    def http_post_request(self, url, params=None, add_to_headers=None):
        headers = {
            "Accept": "application/json",
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 7_1_2 like Mac OS X) > AppleWebKit/537.51.2 '
                          '(KHTML, like Gecko) Mobile/11D257 > MicroMessenger/6.0.1 NetType/WIFI'
        }
        if add_to_headers:
            headers.update(add_to_headers)
        postdata = None
        if params is not None:
            postdata = urlencode(params)    # json.dumps(params)
        # print(postdata)
        try:
            response = self.httpClient.post(url, data=postdata, headers=headers, timeout=30, verify=False)
            if response.status_code == 200:
                return response.json()
            else:
                print("%s\r\n%s" % (url, response.content))
                return False
        except BaseException as e:
            print("httpPost failed, detail is: %s" % str(e))
            return


if __name__ == '__main__':
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    wm = WinMain()
    wm.start()
