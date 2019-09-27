import errno
import json
import socket

from .settings import LOCAL_HOST, MAX_TCP_CONNECTIONS
from .util import recvall, bind_to_random_port


def create_code_receiever():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = bind_to_random_port(sock, LOCAL_HOST)
    sock.listen(MAX_TCP_CONNECTIONS)
    sock.settimeout(0)

    def poll(_):
        try:
            conn, addr = sock.accept()
        except OSError as e:
            if e.args[0] != errno.EAGAIN:
                raise
        else:
            req = json.loads(recvall(conn))
            print("code recv:", req)

    return port, poll
