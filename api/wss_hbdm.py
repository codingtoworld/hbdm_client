#!/usr/bin/env python
# -*- coding: utf-8 -*-

import websocket
import ssl
import gzip
import json
import time


class TradeDetail:

    def __init__(self, symbol):
        self.symbol = symbol
        self.datas = {}
        self.WSC = websocket.WebSocket(sslopt={"cert_reqs": ssl.CERT_NONE})
        self.wscUri = 'wss://www.hbdm.com/ws'
        self.trade_detail_req = '{"req": "market.%s.trade.detail", "id": "python_hbdm"}' % symbol
        self.msg_id = 0
        self.datas = {}
        self.kt_timer = 0
        self.qt_big = 1000  # 成交1000位大单，2000为超大单
        self.init_socket()

    def close_wss(self):
        if self.WSC.connected:
            self.WSC.close()

    def init_socket(self):
        self.WSC.connect(self.wscUri)
        self.WSC.send(self.trade_detail_req)

    def process_message(self, callback):
        while True:
            compress_data = self.WSC.recv()
            result = gzip.decompress(compress_data).decode('utf-8')
            if result[:7] == '{"ping"':
                ts = result[8:21]
                pong = '{"pong":' + ts + '}'
                self.WSC.send(pong)
                self.WSC.send(self.trade_detail_req)
            else:
                try:
                    data = json.loads(result)['data']
                    for row in data:
                        """
                        {"amount":"20","ts":1557113126145,"id":46273427100000,"price":"4.701","direction":"buy"}
                        """
                        if row['id'] > self.msg_id:
                            self.msg_id = row['id']
                            self.taker_message(row, callback)
                            # print("direction:%s amount:%s" % (row['direction'], row['amount']))
                except Exception:
                    pass

    def taker_message(self, msg, callback):
        kt = int(msg['ts'] / 1000)
        kt = kt - (kt % 60)
        k = str(kt)
        if not (k in self.datas.keys()):
            self.datas[k] = {
                'b0': 0, 'b1': 0, 'b2': 0,
                's0': 0, 's1': 0, 's2': 0
            }
        quantity = float(msg['amount'])

        if msg['direction'] == 'buy':  # true 为主卖
            self.datas[k]['b0'] += quantity
        else:
            self.datas[k]['s0'] += quantity

        if quantity >= self.qt_big:
            if msg['direction'] == 'buy':  # buy
                self.datas[k]['b1'] += quantity
            else:  # sell
                self.datas[k]['s1'] += quantity

        if quantity >= self.qt_big * 2:
            if msg['direction'] == 'buy':  # buy
                self.datas[k]['b2'] += quantity
            else:  # sell
                self.datas[k]['s2'] += quantity

        dkeys = self.datas.keys()
        if self.kt_timer < kt:  # 下一个时间周期,显示前面的处理结果
            self.kt_timer = kt  # 全局变量，避免进程冲突

            k60, pk = str(kt - 60), (kt - 60)
            if k60 in dkeys:
                mmb0 = 999 if self.datas[k60]['s0'] == 0 else \
                    float(self.datas[k60]['b0'] / self.datas[k60]['s0'])
                mmb1 = 999 if self.datas[k60]['s1'] == 0 else \
                    float(self.datas[k60]['b1'] / self.datas[k60]['s1'])
                mmb2 = 999 if self.datas[k60]['s2'] == 0 else \
                    float(self.datas[k60]['b2'] / self.datas[k60]['s2'])
                _ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(pk))
                msg = {
                    'symbol': self.symbol,
                    'type': 'taker',
                    'period': '1min',
                    'data': [_ts, round(mmb0, 2), round(mmb1, 2), round(mmb2, 2)]
                }
                # self.WSC.send(json.dumps(msg))
                callback(msg)

            # 输出上一个5分钟周期K线统计 从 kt - 300 到 kt - 60
            if kt % 300 == 0:
                bt = kt - 300
                b0, b1, b2, s0, s1, s2 = 0, 0, 0, 0, 0, 0
                while bt <= (kt - 60):
                    k300 = str(bt)
                    if k300 in dkeys:
                        b0 += self.datas[k300]['b0']
                        b1 += self.datas[k300]['b1']
                        b2 += self.datas[k300]['b2']
                        s0 += self.datas[k300]['s0']
                        s1 += self.datas[k300]['s1']
                        s2 += self.datas[k300]['s2']
                    bt += 60
                mmb0 = 999 if s0 == 0 else float(b0 / s0)
                mmb1 = 999 if s1 == 0 else float(b1 / s1)
                mmb2 = 999 if s2 == 0 else float(b2 / s2)
                _ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(kt - 300))
                msg = {
                    'symbol': self.symbol,
                    'type': 'taker',
                    'period': '5min',
                    'data': [_ts, round(mmb0, 2), round(mmb1, 2), round(mmb2, 2)]
                }
                # self.WSC.send(json.dumps(msg))
                callback(msg)

                # 输出上一个15分钟K线周期统计 从 kt - 900 到 kt - 60
                if kt % 900 == 0:
                    bt = kt - 900
                    b0, b1, b2, s0, s1, s2 = 0, 0, 0, 0, 0, 0
                    while bt <= (kt - 60):
                        k900 = str(bt)
                        if k900 in dkeys:
                            b0 += self.datas[k900]['b0']
                            b1 += self.datas[k900]['b1']
                            b2 += self.datas[k900]['b2']
                            s0 += self.datas[k900]['s0']
                            s1 += self.datas[k900]['s1']
                            s2 += self.datas[k900]['s2']
                            del self.datas[k900]  # 删除已经统计完的数据
                        bt += 60
                    mmb0 = 999 if s0 == 0 else float(b0 / s0)
                    mmb1 = 999 if s1 == 0 else float(b1 / s1)
                    mmb2 = 999 if s2 == 0 else float(b2 / s2)
                    _ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(kt - 900))
                    msg = {
                        'symbol': self.symbol,
                        'type': 'taker',
                        'period': '15min',
                        'data': [_ts, round(mmb0, 2), round(mmb1, 2), round(mmb2, 2)]
                    }
                    # self.WSC.send(json.dumps(msg))
                    callback(msg)

