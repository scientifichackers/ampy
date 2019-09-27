import errno
import json
import socket

from .settings import LOCAL_HOST, DISCOVERY_PORT


def create_discovery_receiver(code_receiver_port):
    # create a nonblocking UDP socket, and bind it to LOCAL_HOST:DISCOVERY_PORT
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((LOCAL_HOST, DISCOVERY_PORT))
    sock.settimeout(0)

    # create the response for a discovery
    reponse = json.dumps(dict(code_receiever_port=code_receiver_port)).encode()
    print(reponse)

    buffer = bytearray(65535)

    def poll(_):
        try:
            addr = sock.recvfrom_into(buffer, 65535)
        except OSError as e:
            if e.args[0] != errno.ETIMEDOUT:
                raise
        else:
            print("discovery recv:", buffer)
            sock.sendto(reponse, addr)

    return poll
