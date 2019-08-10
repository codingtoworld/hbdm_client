#! /usr/bin/env python
#  -*- coding: utf-8 -*-
import sys, os
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
from pages.hbdm_main import MainPage
from config import DEFAULT_USER


class LoginPage:
    win_main = None

    def __init__(self, top=None, win_main=None):
        """
        This class configures and populates the toplevel window.
           top is the toplevel containing window.
        """
        top.title("账户登录")
        top.iconbitmap('favicon.ico')
        top.attributes("-topmost", True)
        top.configure(background="#d9d9d9")
        screenheight = top.winfo_screenheight()
        screenwidth = top.winfo_screenwidth()
        wwidth = 360
        wheight = 220
        _left = int(screenwidth/2 - wwidth/2)
        _top = int(screenheight/2 - wwidth /2)
        top.geometry("%sx%s+%s+%s" % (wwidth, wheight, _left, _top))
        self.top_level = top
        self.win_main = win_main

        self.Label1 = tk.Label(top)
        self.Label1.place(relx=0.0, rely=0.0, height=80, relwidth=1)
        photo_location = os.path.join(os.path.abspath(os.path.dirname(__file__)), "user.png")
        self._img0 = tk.PhotoImage(file=photo_location)
        self.Label1.configure(image=self._img0)
        self.Label1.configure(relief="groove")

        self.TLabel1 = ttk.Label(top)
        self.TLabel1.place(relx=0.1, y=100, height=24, width=49)
        self.TLabel1.configure(background="#d9d9d9", foreground="#000000", font="TkDefaultFont",
                               relief="flat", text='账户：')

        self.TEntryUser = ttk.Entry(top)
        self.TEntryUser.place(relx=0.2, y=100, height=24, relwidth=0.6)
        self.TEntryUser.configure(cursor="ibeam")
        self.TEntryUser.insert(tk.END, DEFAULT_USER)	    # 'config 中配置默认账户'

        self.TLabelPass = ttk.Label(top)
        self.TLabelPass.place(relx=0.1, y=130, height=24, width=49)
        self.TLabelPass.configure(background="#d9d9d9", foreground="#000000", font="TkDefaultFont",
                                  relief="flat", text='密码：')

        self.TEntryPass = ttk.Entry(top)
        self.TEntryPass.place(relx=0.2, y=130, height=24, relwidth=0.6)
        self.TEntryPass.configure(cursor="ibeam")
        self.TEntryPass.bind("<Return>", self.user_login)

        self.Button1 = tk.Button(top)
        self.Button1.configure(background="#25b979", foreground="#ffffff", activeforeground="#000000")
        self.Button1.place(relx=0.6, y=170, height=33, relwidth=0.2)
        self.Button1.bind('<Button-1>', self.user_login)
        self.Button1.configure(pady="0", text='登  录')

        self.Message = ttk.Label(top)
        self.Message.place(relx=0.2, y=170, height=33, relwidth=0.4)
        self.Message.configure(background="#d9d9d9", foreground="#ff0000")

    def user_login(self, event):
        _uname = self.TEntryUser.get()
        _upass = self.TEntryPass.get()
        _r = self.win_main.http_post_request('%s/signin' % self.win_main.baseUrl,
                                             params={'username': _uname, 'authcode': _upass})
        if _r['code'] == 200:
            self.win_main.main_page = MainPage(self.top_level, self.win_main)

        else:
            self.Message.configure(text='登录失败')
