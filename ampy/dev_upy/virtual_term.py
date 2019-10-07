import io
import os
import socket

from .settings import TERMINAL_PORT

_socks = {}


def add(host: str, port: int):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    sock.connect((host, port))
    sock.bind((host, TERMINAL_PORT))
    _socks[sock] = sock.makefile()


def main():
    os.dupterm(VitrualTermIO())


class VitrualTermIO(io.IOBase):
    _index = 0

    def readinto(self, buf):
        for f in _socks.values():
            return f.readinto(buf)

    def write(self, buf):
        tot = 0
        count = 0
        for f in _socks.values():
            count += 1
            tot += f.write(buf)
        return tot // count
