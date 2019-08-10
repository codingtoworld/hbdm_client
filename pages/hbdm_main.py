#! /usr/bin/env python
#  -*- coding: utf-8 -*-

import time
import websocket
import ssl
import json
import subprocess
import threading
from functools import partial
try:
    import Tkinter as tk
    from Tkinter import messagebox
except ImportError:
    import tkinter as tk
    from tkinter import messagebox

try:
    import ttk
    py3 = False
except ImportError:
    import tkinter.ttk as ttk
    py3 = True
from api.utils import *
from pages.datas_page import DatasPage


# 自定义float类型输入Entry
class FloatEntry(tk.Entry):
    def __init__(self, master, value="", **kw):
        tk.Entry.__init__(self, master, kw)
        self.__value = value
        self.variable = tk.StringVar()
        self.variable.set(value)
        self.variable.trace("w", self.__callback)
        self.config(textvariable=self.variable)

    def __callback(self, *dummy):
        value = self.variable.get()
        newvalue = self.validate(value)
        if newvalue is None:
            self.variable.set(self.__value)
        elif newvalue != value:
            self.__value = newvalue
            self.variable.set(self.__value)
        else:
            self.__value = value

    def validate(self, value):
        try:
            if value:
                v = float(value)
            return value
        except ValueError:
            return None


class MainPage:
    trade_types = [
        ("当前成交价", "TP"),
        ("第一档卖价", "S1"),
        ("第一档买价", "B1"),
        ("对手价成交", "OP"),
        ("蜡烛图高价", "HP"),
        ("蜡烛图低价", "LP"),
        ("蜡烛图开价", "ON"),
        ("蜡烛图收价", "OF"),
    ]
    server_time = 0
    datasPage = None
    tradeTimes = 8  # 每天最多进行的交易次数 防止黑天鹅 交易要有节制

    def __init__(self, top=None, win_main=None):

        top.title("火币合约 API交易")
        top.configure(background="#d9d9d9")

        top.iconbitmap('favicon.ico')
        top.attributes("-topmost", True)

        screenheight = top.winfo_screenheight()
        wwidth = 430
        wheight = 390
        _top = screenheight - wheight - 36
        top.geometry("%sx%s+0+%s" % (wwidth, wheight, _top))

        self.top_level = top
        self.win_main = win_main

        self.varSymbol = tk.StringVar()
        self.varSymbol.set("承认无知，只算概率！")

        self.volume = 0
        self.symbols = None

        self.warning_counter = 0
        # ------------------------- 1
        self.Label1 = tk.Label(top, textvariable=self.varSymbol, height=2)
        self.Label1.pack(side=tk.TOP, expand=tk.NO, fill=tk.X)
        self.Label1.configure(background="#6f6f6f", font="-family {Arial} -size 12",
                              foreground="#ffffff", relief="groove")

        mainFrame = tk.Frame(top)
        mainFrame.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH)

        self.statusTxt = tk.StringVar()
        self.TLabel1 = tk.Label(top, textvariable=self.statusTxt, height=1, anchor="w")
        self.TLabel1.pack(side=tk.BOTTOM, expand=tk.NO, fill=tk.X)
        self.TLabel1.configure(background="#d9d9d9", foreground="#0000ff", font="TkDefaultFont", relief="ridge")

        self.FrameL = tk.Frame(mainFrame, width=12)
        self.FrameL.pack(side=tk.LEFT, expand=tk.NO, anchor='w', fill=tk.Y)
        self.FrameL.configure(relief='groove', borderwidth="2", background="#d9d9d9")

        self.FrameR = tk.Frame(mainFrame)
        self.FrameR.pack(side=tk.LEFT, expand=tk.YES, anchor='w', fill=tk.BOTH)
        self.FrameR.configure(relief='groove', borderwidth="2", background="#d9d9d9")

        # ----- FrameL 2

        self.Label2 = tk.Label(self.FrameL, height=1)
        self.Label2.pack(side=tk.TOP, expand=tk.NO, fill=tk.X)
        self.Label2.configure(background="#d9d9d9", foreground="#000000", relief="groove", text='交易品种')

        self.period = tk.StringVar()
        self.Combobox = ttk.Combobox(self.FrameL, width=12, textvariable=self.period)
        self.Combobox['values'] = ("CW", "NW", "CQ")  # 设置下拉列表的值
        self.Combobox.current(2)
        self.Combobox.pack(side=tk.TOP)

        self.boxSymbols = tk.Listbox(self.FrameL, width=12, height=6, exportselection=False, borderwidth="0")
        self.boxSymbols.pack(side=tk.TOP, anchor='nw', expand=tk.YES, fill=tk.BOTH)
        self.boxSymbols.configure(background="white", font="-family {Microsoft YaHei UI} -size 10",
                                  foreground="#0000ff")
        self.boxSymbols.bind("<ButtonRelease-1>", self.listbox_click)

        self.check_open_stat = tk.IntVar()
        self.check_auto_close = tk.Checkbutton(self.FrameL, variable=self.check_open_stat, padx=0,
                                               background="#d9d9d9", anchor='w',
                                               text='打开数据统计').pack(anchor='sw', side=tk.BOTTOM)
        # 设置支撑压力位
        self.qtPriceFrame = tk.Frame(self.FrameL, borderwidth="4", background="#87D37C")
        self.qtPriceFrame.pack(side=tk.BOTTOM, expand=tk.NO, anchor='sw', fill=tk.X)
        self.qtPriceFrame.configure()

        self.edtYL = FloatEntry(self.qtPriceFrame, width=2)
        self.edtYL.bind("<Return>", self.YLZCClick)
        self.edtYL.pack(side=tk.TOP, expand=tk.NO, anchor='nw', fill=tk.X)

        self.btnYLZC = tk.Button(self.qtPriceFrame, width=6, borderwidth="0", command=partial(self.YLZCClick, None))
        self.btnYLZC.configure(background="#25b979", foreground="#ffffff", activeforeground="#000000")
        self.btnYLZC.configure(font="-family {Microsoft YaHei UI} -size 10", pady="0", text='设置压力支撑')
        self.btnYLZC.pack(side=tk.TOP, expand=tk.NO, anchor='sw', fill=tk.X)

        self.edtZC = FloatEntry(self.qtPriceFrame, width=2)
        self.edtZC.bind("<Return>", self.YLZCClick)
        self.edtZC.pack(side=tk.BOTTOM, expand=tk.NO, anchor='sw', fill=tk.X)

        # ------ FrameR 2
        self.varTradeInfo = tk.StringVar()
        self.varMonitor = tk.StringVar()
        self.lbrMonitor = tk.Label(self.FrameR, height=1, anchor='e', textvariable=self.varMonitor)
        self.lbrMonitor.pack(side=tk.TOP, expand=tk.NO, fill=tk.X)
        self.lbrMonitor.configure(relief="groove",
                                  font="-family {Microsoft YaHei UI} -size 10", background="#ffffff",
                                  foreground="#ff0000")

        self.FrameRM = tk.Frame(self.FrameR)
        self.FrameRM.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH)
        self.FrameRM.configure(relief='groove', borderwidth="2", background="#ffffff")

        # ----- FrameRM 2
        self.FrameCL = tk.Frame(self.FrameRM)
        self.FrameCL.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH)
        self.FrameCL.configure(borderwidth="0", background="#d9d9d9")

        self.FrameCL_L = tk.Frame(self.FrameCL, width=16)
        self.FrameCL_L.pack(side=tk.LEFT, expand=tk.NO, fill=tk.Y, anchor='w')
        self.FrameCL_L.configure(borderwidth="0", background="#d9d9d9")

        self.ttv = tk.IntVar()
        for _id, _name in enumerate(self.trade_types):

            tk.Radiobutton(self.FrameCL_L,
                           text=_name, pady=0, padx=10, background="#d9d9d9", anchor='w',
                           variable=self.ttv, command=self.get_trade_type,
                           value=_id).pack(anchor='nw')
        self.ttv.set(2)

        slFrame = tk.Frame(self.FrameCL_L, width=10, background="#ffff00", height=10)
        slFrame.pack(fill=tk.X, expand=tk.NO, side=tk.BOTTOM)

        self.check_val = tk.IntVar()
        self.check_auto_close = tk.Checkbutton(slFrame, variable=self.check_val, pady=0, anchor='w',
                                               text='自动平仓', background="#ffff00",
                                               command=partial(self.set_auto_close, None))
        self.check_auto_close.pack(anchor='sw', side=tk.RIGHT)

        self.edtStopLost = FloatEntry(slFrame, width=10)
        self.edtStopLost.pack(side=tk.LEFT, expand=tk.NO, anchor='sw', fill=tk.X, padx=4, pady=4)
        self.edtStopLost.bind("<Return>", self.set_auto_close)

        self.ChartLabel = tk.Label(self.FrameCL)
        self.ChartLabel.pack(side=tk.LEFT, expand=tk.YES, fill=tk.BOTH, anchor='w')
        photo_location = os.path.join(os.path.abspath(os.path.dirname(__file__)), "chart.png")
        _img0 = tk.PhotoImage(file=photo_location)
        self.ChartLabel.configure(borderwidth="2", image=_img0, relief="groove", background="#ffffff")
        self.ChartLabel.image = _img0

        self.lblWarning = tk.Label(self.FrameRM, pady=0, padx=10)
        self.lblWarning.pack(fill=tk.X, side=tk.BOTTOM)
        self.lblWarning.configure(background="#ffffff", foreground="#ff0000",
                                  font="-family {Microsoft YaHei UI} -size 10",
                                  relief="groove", text='在开仓点果断开仓，在止损点果断止损')

        # ---- FrameRB 2
        self.FrameRB = tk.Frame(self.FrameR, height=40)
        self.FrameRB.pack(side=tk.TOP, expand=tk.NO, fill=tk.X)
        self.FrameRB.configure(relief='groove', borderwidth="2", background="#d9d9d9")

        self.btnLeft = tk.Button(self.FrameRB, width=6)
        self.btnLeft.configure(background="#25b979", foreground="#ffffff", activeforeground="#000000")
        self.btnLeft.configure(font="-family {Microsoft YaHei UI} -size 11", pady="0", text='开仓')
        self.btnLeft.bind("<ButtonPress-1>", self.TradeBtnClick)
        self.btnLeft.pack(side=tk.LEFT)

        self.btnRight = tk.Button(self.FrameRB, width=6)    # command=self.TradeBtnClick)
        self.btnRight.configure(background="#d75f5f", foreground="#ffffff", activeforeground="#000000")
        self.btnRight.configure(font="-family {Microsoft YaHei UI} -size 11", pady="0", text='平仓')
        self.btnRight.bind("<ButtonPress-1>", self.TradeBtnClick)
        self.btnRight.pack(side=tk.RIGHT)

        self.lbTrade = tk.Label(self.FrameRB, textvariable=self.varTradeInfo, anchor="center")
        self.lbTrade.configure(background="#d9d9d9", foreground="#000000", font="TkDefaultFont")
        self.lbTrade.pack(anchor='center', expand=tk.YES, fill=tk.BOTH)
        self.lbTrade.bind('<Double-Button-1>', self.set_stop_price)

        # ------- init event
        self.load_symbols()
        self.load_timer()

        thread = threading.Thread(target=self.start_wss, name="wssThread")
        thread.setDaemon(True)
        thread.start()

    def set_stop_price(self, event=None):
        result = messagebox.askokcancel("强行平仓", "确认将当前持有合约强行平仓吗?")
        if result:  # 设置止盈止损单
            symbol = self.boxSymbols.get(self.boxSymbols.curselection())  # self.varSymbol.get()
            if symbol == '':
                return False
            caption = self.btnRight.cget('text')
            direction, offset = '', ''
            if caption == '空单平仓':
                direction = 'buy'
                offset = 'close'
            if caption == '多单平仓':
                direction = 'sell'
                offset = 'close'
            params = {'direction': direction,
                      'symbol': symbol,
                      'offset': offset,
                      'period': self.Combobox.get(),
                      'order_price_type': 9,    # 强行平仓，针对瀑布行情
                      }

            _r = self.win_main.http_get_request('%s/trade' % self.win_main.baseUrl, params)

            if isinstance(_r, dict) and _r['status'] == 'ok':
                self.varTradeInfo.set('%s成功！ ' % caption)
            elif isinstance(_r, dict):
                self.statusTxt.set('%s失败: %s' % (caption, _r['err_msg']))
            else:
                self.statusTxt.set('操作失败！请检测是否登陆账户！')
                return False

    def start_wss(self):
        def on_message(ws, message):
            msg = json.loads(message)
            if msg['type'] == 'taker':
                if (msg['data'][1] > 2) and (msg['data'][2] > msg['data'][1]):
                    self.varMonitor.set('大单买入：%s' % msg['symbol'])
            if msg['type'] == 'quant':
                self.varMonitor.set('%s买入策略：%s' % (msg['symbol'], msg['name']))
                messagebox.showinfo("买入策略", self.varMonitor.get())

        def on_error(ws, error):
            pass

        def on_close(ws):
            pass

        def on_open(ws):
            pass

        websocket.enableTrace(True)
        wss = websocket.WebSocketApp(self.win_main.baseWss,
                                     on_message=on_message,
                                     on_error=on_error,
                                     on_close=on_close,
                                     on_open=on_open
                                     )
        while True:
            try:
                wss.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
            except:
                print('wss error!')

    def get_trade_type(self):
        return self.ttv.get()

    def load_symbols(self):
        self.symbols = self.win_main.http_get_request('%s/symbols' % self.win_main.baseUrl)
        if len(self.symbols) > 0 and {'symbol': 'BTC'} in self.symbols:
            for symbol in self.symbols:
                self.boxSymbols.insert(tk.END, symbol['symbol'])
            self.statusTxt.set('加载完毕')
            th = threading.Thread(target=self.keep_alive)
            th.setDaemon(True)
            th.start()

    def load_timer(self):
        def timer_thead(offset=0):
            while True:
                if self.server_time > 0:
                    now = time.time()*1000
                    offset = int(self.server_time - now) if offset == 0 else offset
                    ts = int((now + offset)/1000)
                    ts_mod15 = 900 - (ts % 900)
                    ts_mod5 = 300 - (ts % 300)
                    ts_mod1 = 60 - (ts % 60)
                    self.varSymbol.set("倒计时：[ %d 秒 ] [ %d 秒 ] [ %d 秒 ]" % (ts_mod15, ts_mod5, ts_mod1))
                else:
                    offset = 0
                time.sleep(1)

        th = threading.Thread(target=timer_thead)
        th.setDaemon(True)
        th.start()

    def set_auto_close(self, event):
        auto_close = str(self.check_val.get())
        stop_price = self.edtStopLost.variable.get()
        try:
            stop_price = float(stop_price)
        except ValueError:
            stop_price = 0
        _symbol = self.boxSymbols.get(self.boxSymbols.curselection())
        _period = self.Combobox.get()
        if _symbol == '':
            return False
        params = {'auto_close': auto_close, 'stop_price': stop_price, 'symbol': _symbol, 'period': _period}
        _r = self.win_main.http_get_request('%s/setlost' % self.win_main.baseUrl, params=params)

    def keep_alive(self):
        while True:
            _r = self.win_main.http_get_request('%s/logchk' % self.win_main.baseUrl)
            if _r is False:
                self.statusTxt.set('心跳检测失败！')
                continue
            if _r['code'] == 200:
                tm = time.strftime("%H:%M", time.localtime(int(time.time())))
                self.statusTxt.set('%s已登录，服务器时间：%s' % (_r['user'], tm))
                self.varMonitor.set("")

                show_warning = False
                is_rase = True
                if 'rates' in _r:   # 出现盈亏信息
                    yk = ''
                    for rate in _r['rates']:
                        yk = yk + "%s利润: [ %.2f%% ] [ %.2f%% ] [ %.2f%% ]" % \
                             (rate['symbol'], rate['max_profit'], rate['profit_rate'], rate['net_profit'])
                        if rate['warning']:
                            show_warning = True
                        if rate['profit_rate'] < 0:
                            is_rase = False
                    self.varMonitor.set(yk)
                if show_warning:
                    if self.warning_counter % 20 == 0:  # 100秒提醒一次
                        # messagebox.showwarning("止损报警", "当前收益率已经跌破预设值，请请注意止损！")
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        subprocess.Popen(['mpg123.exe', '-q', 'walf.mp3'],
                                         stderr=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         startupinfo=startupinfo).wait()
                    self.warning_counter += 1
                else:
                    self.warning_counter = 0

                if is_rase:
                    self.lbrMonitor.configure(foreground="#25b979")
                else:
                    self.lbrMonitor.configure(foreground="#d75f5f")
            else:
                self.statusTxt.set('心跳检测失败！')
            time.sleep(2)

    def listbox_click(self, event):
        w = event.widget
        # w.curselection()
        sel = w.curselection()
        if len(sel) == 1:
            index = int(sel[0])
            _symbol = w.get(index)
            self.varSymbol.set(_symbol)
            _period = self.Combobox.get()
            # 获取最新报价
            _p = self.win_main.http_get_request('%s/contract?symbol=%s&period=%s' %
                                                (self.win_main.baseUrl, _symbol, _period)
                                                )
            if isinstance(_p, dict) and _p['code'] == 200:
                _str = '多单' if _p['data']['direction'] == 'buy' else '空单'
                self.volume = _p['data']['volume']

                self.btnLeft.pack_forget()
                self.btnRight.pack_forget()
                self.btnRight.pack(side=tk.RIGHT)
                if _p['data']['available'] > 0:  # 尚未委托
                    self.varTradeInfo.set(_str + " %d 手" % self.volume)
                    self.btnRight.configure(text=_str+'平仓')
                else:
                    self.varTradeInfo.set('委托'+_str + " %d 手" % self.volume)
                    self.btnRight.configure(text='重平'+_str)
                # 初始化 合约周期列表
                ct_types = {
                    "this_week": "CW",
                    "next_week": "NW",
                    "quarter": "CQ"
                }
                self.server_time = _p['ts']
                contract_type = ct_types[_p['data']['contract_type']]
                self.Combobox.set(contract_type)

                # 获取压力支撑位置
                self.edtYL.variable.set(_p['top'] if 'top' in _p else '')
                self.edtZC.variable.set(_p['down'] if 'down' in _p else '')

                # 获取是否系统止损和止损价格
                self.check_val.set(1 if ('auto_close' in _p) and _p['auto_close'] == 1 else 0)
                self.edtStopLost.variable.set(_p['stop_price'] if ('stop_price' in _p) and _p['stop_price'] > 0 else '')
            elif isinstance(_p, dict) and _p['code'] == 201:     # 不持有，显示开多，开空信息
                self.server_time = _p['ts']
                self.volume = 0
                self.btnLeft.pack(side=tk.LEFT)
                self.btnLeft.configure(text='多单开仓')
                self.btnRight.configure(text='空单开仓')
                info = "[%.2f%%] 空仓 [%.2f%%]" % (_p['premium_buy'], _p['premium_sell'])
                self.varTradeInfo.set(info)
                # 获取压力支撑位置
                self.edtYL.variable.set(_p['top'] if 'top' in _p else '')
                self.edtZC.variable.set(_p['down'] if 'down' in _p else '')

                # 获取是否系统止损和止损价格
                self.check_val.set(1 if ('auto_close' in _p) and _p['auto_close'] == 1 else 0)
                self.edtStopLost.variable.set(_p['stop_price'] if ('stop_price' in _p) and _p['stop_price'] > 0 else '')
            elif isinstance(_p, dict):
                self.varTradeInfo.set(_p['msg'])
            self.lbTrade.pack_forget()
            self.lbTrade.pack(anchor='center', expand=tk.YES, fill=tk.BOTH)

            # 调用买卖数据统计页面
            open_stat = self.check_open_stat.get()
            if not self.win_main.is_show_dp and open_stat:
                self.win_main.is_show_dp = True
                DatasPage(self.win_main, "%s_%s" % (_symbol, _period))

    def TradeBtnClick(self, event):
        # 每天操作不超过4次，也就是开仓不能操作2次
        tts = get_trade_times()
        tts += 1
        set_trade_times(tts)
        if tts > self.tradeTimes:
            self.statusTxt.set('今天已经操作好多次啦！请您好好休息！')
            return False
        _symbol = self.boxSymbols.get(self.boxSymbols.curselection())
        if _symbol == '':
            return False
        caption = event.widget.cget('text')
        _bg = event.widget.cget('background')
        if _bg == '#363636':
            return False
        event.widget.configure(state=tk.DISABLED, background='#363636')
        direction, offset = '', ''
        order_price_type = self.ttv.get()
        if caption == '多单开仓':
            direction = 'buy'
            offset = 'open'
        if caption == '多单平仓':
            direction = 'sell'
            offset = 'close'
        if caption == '空单开仓':
            direction = 'sell'
            offset = 'open'
        if caption == '空单平仓':
            direction = 'buy'
            offset = 'close'
        if caption == '重平多单':
            direction = 'sell'
            offset = 'close'
            # 取消当前委托单
            _c = self.win_main.http_get_request('%s/cancel' % self.win_main.baseUrl, {'symbol': _symbol})
            time.sleep(1)
            order_price_type = 9
        if caption == '重平空单':
            direction = 'buy'
            offset = 'close'
            # 取消当前委托单
            _c = self.win_main.http_get_request('%s/cancel' % self.win_main.baseUrl, {'symbol': _symbol})
            time.sleep(1)
            order_price_type = 9

        params = {'direction': direction,
                  'symbol': _symbol,
                  'offset': offset,
                  'period': self.Combobox.get(),
                  'order_price_type': order_price_type,
                  }

        _r = self.win_main.http_get_request('%s/trade' % self.win_main.baseUrl, params)
        # {u'status': u'error', u'err_msg': u'Invalid amount, please modify and order again.',
        # u'ts': 1555629730784, u'err_code': 1040}
        # {u'status': u'error', u'err_msg': u'Abnormal service. Please try again later.',
        # u'ts': 1555629955001, u'err_code': 1067}
        # {u'status': u'ok', u'data': {u'order_id': 39, u'client_order_id': 1555629485}, u'ts': 1555635427627}
        if _r is False:
            self.statusTxt.set('操作失败！请检测是否登陆账户！')
            return False
        if _r['status'] == 'ok':
            self.varTradeInfo.set('%s成功！ ' % caption)
        else:
            self.statusTxt.set('%s失败: %s' % (caption, _r['err_msg']))
        event.widget.configure(state=tk.NORMAL, background=_bg)

    def YLZCClick(self, event):
        _top = self.edtYL.variable.get()
        _down = self.edtZC.variable.get()
        _symbol = self.boxSymbols.get(self.boxSymbols.curselection())
        _period = self.Combobox.get()
        if _symbol == '':
            return False
        _r = self.win_main.http_post_request('%s/topdown' % self.win_main.baseUrl,
                                             params={'top': _top, 'down': _down, 'symbol': _symbol, 'period': _period})
        if _r is False:
            self.statusTxt.set('操作失败！请检测是否登陆账户！')
            return False
        if _r['status'] == 'ok':
            self.statusTxt.set('设置成功！ ')
        else:
            self.statusTxt.set('设置失败: %s' % _r['err_msg'])
