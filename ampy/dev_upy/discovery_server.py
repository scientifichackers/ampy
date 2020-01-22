import errno
import json
import socket

from . import settings


def main():
    # bind a non-blocking UDP socket to LOCAL_HOST:DISCOVERY_PORT
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((settings.LOCAL_HOST, settings.DISCOVERY_PORT))
    sock.setblocking(False)

    # create the response for a discovery
    payload = json.dumps({"status": "sucess"}).encode()

    # cache
    recvfrom = sock.recvfrom
    sendto = sock.sendto
    n = settings.UDP_MAX_SIZE

    def poll(_):
        try:
            data, addr = recvfrom(n)
        except OSError as e:
            if e.args[0] not in (errno.ETIMEDOUT, errno.EAGAIN):
                raise
        else:
            print("[ampy] discovery req:", addr, data)
            sendto(payload, addr)

    return poll
