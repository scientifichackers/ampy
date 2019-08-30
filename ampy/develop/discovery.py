import socket

from machine import Timer

from .consts import *


def run():
    Timer(1).init(period=DISCOVERY_WAIT_MS, callback=_create_callback())


def _create_callback():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((LOCAL_HOST, DISCOVERY_PORT))
    sock.settimeout(0)

    def callback(_):
        print("discovery request:", sock.recv(1024).decode())

    return callback
