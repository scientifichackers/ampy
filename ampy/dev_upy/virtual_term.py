import io
import os
import socket

from .settings import TERMINAL_PORT

read_clients = {}
write_clients = {}

read_socks = read_clients.values()
write_socks = write_clients.values()


class VitrualTermIO(io.IOBase):
    def readinto(self, buf):
        for f in read_socks:
            return f.readinto(buf)

    def write(self, buf):
        tot = 0
        count = 0
        for f in write_socks:
            count += 1
            tot += f.write(buf)
        if not count:
            return 0
        return tot // count


vio = VitrualTermIO()


def main():
    os.dupterm(vio)


def add_client(addr: tuple, mode: str):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    f = sock.makefile()

    if "r" in mode:
        sock.bind((addr[0], TERMINAL_PORT))
        read_clients[addr] = f

    if "w" in mode:
        sock.connect(addr)
        write_clients[addr] = f
