import errno
import json

import network
from machine import Timer

from .settings import CONFIG_FILE

conf = {}


def load():
    global conf
    try:
        with open(CONFIG_FILE, 'r') as f:
            conf = json.load(f)
    except OSError as e:
        if e.args[0] != errno.ENOENT:
            raise


def store():
    with open(CONFIG_FILE, 'w') as f:
        json.dump(conf, f)


def get_sta_if():
    sta_if = network.WLAN(network.STA_IF)
    sta_ssid = conf.get('sta_ssid')
    sta_password = conf.get('sta_password')

    if sta_ssid is None:
        sta_if.active(False)
    else:
        sta_if.active(True)
        sta_if.connect(sta_ssid, sta_password)

    return sta_if


def get_ap_if():
    ap_if = network.WLAN(network.AP_IF)
    disable = conf.get('disable_ap', False)
    ap_ssid = conf.get('ap_ssid')
    ap_pass = conf.get('ap_password')

    if disable:
        ap_if.active(False)
    else:
        if ap_ssid is not None:
            if ap_pass is None:
                ap_if.config(essid=ap_ssid, authmode=network.AUTH_OPEN)
            else:
                ap_if.config(
                    essid=ap_ssid, authmode=network.AUTH_WPA_WPA2_PSK, password=ap_pass
                )

        ap_if.active(True)

    return ap_if


def get_timer() -> Timer:
    return Timer(conf.get('timer_id', 0))
