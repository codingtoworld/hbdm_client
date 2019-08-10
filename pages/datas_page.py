#! /usr/bin/env python
#  -*- coding: utf-8 -*-
import threading
import sys, os
from api.wss_hbdm import TradeDetail
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


class DatasPage:

    def __init__(self, winMain, symbol=None):
        """
        This class configures and populates the toplevel window.
           top is the toplevel containing window.
        """
        self.winMain = winMain
        self.symbol = symbol
        self.wssApi = None
        self.period = '1min'
        self.root = tk.Tk()
        # root.withdraw()
        self.root.title("%s - 交易数据统计" % symbol)
        self.root.attributes("-topmost", True)
        self.root.configure(background="#d9d9d9")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close_page)
        screenheight = self.root.winfo_screenheight()
        screenwidth = self.root.winfo_screenwidth()
        wwidth = 380
        wheight = 220
        _left = int(screenwidth/2 - wwidth/2)
        _top = int(screenheight/2 - wwidth/2)
        self.root.geometry("%sx%s+%s+%s" % (wwidth, wheight, _left, _top))
        self.datas_1min = []
        self.datas_5min = []
        self.datas_15min = []

        frameTop = tk.Frame(self.root, height=40)
        frameTop.pack(side=tk.TOP, expand=tk.NO, fill=tk.X)
        self.btn_1min = tk.Button(frameTop, width=10, text="1分钟")
        self.btn_1min.pack(side=tk.RIGHT)
        self.btn_1min.bind("<ButtonPress-1>", self.btnClick)
        self.btn_5min = tk.Button(frameTop, width=10, text="5分钟")
        self.btn_5min.pack(side=tk.RIGHT)
        self.btn_5min.bind("<ButtonPress-1>", self.btnClick)
        self.btn_15min = tk.Button(frameTop, width=10, text="15分钟")
        self.btn_15min.pack(side=tk.RIGHT)
        self.btn_15min.bind("<ButtonPress-1>", self.btnClick)

        self.selPeriod = tk.StringVar()
        self.selPeriod.set("1分钟")
        self.Label1 = tk.Label(frameTop, textvariable=self.selPeriod, width=10, height=2)
        self.Label1.pack(side=tk.LEFT, expand=tk.NO)
        self.Label1.configure(font="-family {Arial} -size 12")

        frameMain = tk.Frame(self.root)
        frameMain.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self.tvData = ttk.Treeview(frameMain, columns=("买卖比", "中单比", "大单比"))  # 表格

        vsb = ttk.Scrollbar(frameMain, orient="vertical", command=self.tvData.yview)
        vsb.pack(side=tk.RIGHT, fill='y')

        self.tvData.heading('#0', text='统计周期')
        self.tvData.heading('#1', text='买卖比')
        self.tvData.heading('#2', text='中单比')
        self.tvData.heading('#3', text='大单比')
        self.tvData.column('#0', width=180)
        self.tvData.column('#1', width=60)
        self.tvData.column('#2', width=60)
        self.tvData.column('#3', width=60)
        self.tvData.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.tvData.configure(yscroll=vsb.set)

        thread = threading.Thread(target=self.init_datas, name="wssThread")
        thread.setDaemon(True)
        thread.start()

        self.root.mainloop()

    def on_close_page(self):
        self.wssApi.close_wss()
        self.datas_1min.clear()
        self.datas_5min.clear()
        self.datas_15min.clear()
        self.root.destroy()
        self.winMain.is_show_dp = False

    def init_datas(self):
        self.wssApi = TradeDetail(self.symbol)
        self.wssApi.process_message(self.callback)

    def callback(self, msg):
        msg['data'][1] = '-' if msg['data'][1] == 999 else msg['data'][1]
        msg['data'][2] = '-' if msg['data'][2] == 999 else msg['data'][2]
        msg['data'][3] = '-' if msg['data'][3] == 999 else msg['data'][3]
        if msg['period'] == '1min':
            self.datas_1min.append(msg['data'])
            self.update_view(msg['data'], '1min')
        if msg['period'] == '5min':
            self.datas_5min.append(msg['data'])
            self.update_view(msg['data'], '5min')
        if msg['period'] == '15min':
            self.datas_15min.append(msg['data'])
            self.update_view(msg['data'], '15min')

    def update_view(self, datas, period='1min'):
        if self.period == period:
            self.tvData.insert('', 'end', text=datas[0], values=(datas[1], datas[2], datas[3],))

    def btnClick(self, event):
        caption = event.widget.cget('text')
        self.tvData.delete(*self.tvData.get_children())
        self.selPeriod.set(caption)
        if caption == '1分钟':
            self.period = '1min'
            for row in self.datas_1min:
                self.tvData.insert('', 'end', text=row[0], values=(row[1], row[2], row[3],))
        elif caption == '5分钟':
            self.period = '5min'
            for row in self.datas_5min:
                self.tvData.insert('', 'end', text=row[0], values=(row[1], row[2], row[3],))
        elif caption == '15分钟':
            self.period = '15min'
            for row in self.datas_15min:
                self.tvData.insert('', 'end', text=row[0], values=(row[1], row[2], row[3],))

