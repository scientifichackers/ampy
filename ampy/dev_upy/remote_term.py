"""
Allows remote control of the inbuilt virtual teminal.
"""
import errno
import io
import os
import socket

from . import settings

KYB_INT = const(3)


def main():
    rt = RemoteTerm.get_instance()
    os.dupterm(rt)

    notify = os.dupterm_notify

    def poll(_):
        notify(0)

    return poll


class RemoteTerm(io.IOBase):
    _instance = None

    @classmethod
    def get_instance(cls) -> 'RemoteTerm':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        # setup a socket for receiving input from the world
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((settings.LOCAL_HOST, settings.TERMINAL_PORT))
        sock.setblocking(False)
        self.rx_file = sock.makefile()

        # These two flags work in tandem to emulate a keyboard interrupt.
        # The private flag, allows sending the 'KYB_INT' char to the virtual terminal.
        # The public flag allows 'repl_man.py',
        # to differentiate between fake and real events.
        self._fake_ctrl_c_flag = False
        self.fake_ctrl_c_flag = False

        # {address = (host, port) : tx socket file}
        self.tx_files = {}

    def send_ctrl_c(self):
        """
        Send a fake KeyboardInterrupt to local terminal.
        """
        self._fake_ctrl_c_flag = True
        os.dupterm_notify(0)

    def readinto(self, buf):
        """
        Receive data from clients into the local terminal buffer.
        """
        if self._fake_ctrl_c_flag:
            self._fake_ctrl_c_flag = False
            self.fake_ctrl_c_flag = True
            buf[0] = KYB_INT
            return 1

        try:
            n = self.rx_file.readinto(buf)
        except OSError as e:
            if e.args[0] != errno.ETIMEDOUT:
                raise
        else:
            return n

    def write(self, buf):
        """
        Send data from local terminal buffer to all clients.
        """
        if not self.tx_files:
            return len(buf)

        total = 0
        count = 0
        for addr, f in list(self.tx_files.items()):
            count += 1
            try:
                total += f.write(buf)
            except OSError as e:
                if e.args[0] == errno.EBADF:
                    del self.tx_files[addr]
                else:
                    raise

        return total // count
