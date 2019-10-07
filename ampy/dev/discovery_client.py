import socket

from ampy.dev_upy.settings import DISCOVERY_PORT, BCAST_HOST, UDP_MAX_SIZE


def main() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(b"hello", (BCAST_HOST, DISCOVERY_PORT))
    _, addr = sock.recvfrom(UDP_MAX_SIZE)
    return addr[0]


if __name__ == "__main__":
    main()
