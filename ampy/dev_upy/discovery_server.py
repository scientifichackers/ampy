import errno
import json
import socket

from .settings import LOCAL_HOST, DISCOVERY_PORT, UDP_MAX_SIZE


def main():
    # create a nonblocking UDP socket, and bind it to LOCAL_HOST:DISCOVERY_PORT
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LOCAL_HOST, DISCOVERY_PORT))
    sock.setblocking(False)

    # create the response for a discovery
    payload = json.dumps({"status": "sucess"}).encode()
    print(payload)

    def poll(_):
        try:
            data, addr = sock.recvfrom(UDP_MAX_SIZE)
        except OSError as e:
            if e.args[0] != errno.ETIMEDOUT:
                raise
        else:
            print("discovery recv:", data)
            sock.sendto(payload, addr)

    return poll
