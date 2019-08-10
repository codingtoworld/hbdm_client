# -*- coding: utf-8 -*-

import json
import time
import os


def load_json(json_file):
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    log_path = os.path.join(base_path, 'logs')
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    try:
        with open(os.path.join(log_path, json_file)) as f:
            _json = json.loads(f.read())
    except (IOError, ValueError):
        _json = {}
    return _json


def save_json(_json, json_file):
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    log_path = os.path.join(base_path, 'logs')
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    try:
        with open(os.path.join(log_path, json_file), 'w') as f:
            f.write(json.dumps(_json))
    except (IOError, TypeError):
        pass


def get_trade_times():
    """
    获取当天的交易次数
    :return:
    """
    tlj = load_json('trade_log.json')
    curr_date = time.strftime("%Y%m%d", time.localtime())
    if curr_date in tlj:
        return tlj[curr_date]
    else:
        return 0


def set_trade_times(times):
    tlj = load_json('trade_log.json')
    curr_date = time.strftime("%Y%m%d", time.localtime())
    tlj[curr_date] = times
    save_json(tlj, 'trade_log.json')
