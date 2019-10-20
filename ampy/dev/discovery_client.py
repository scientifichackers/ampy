import socket
from time import sleep, time
from typing import Generator

from ampy.dev_upy.settings import DISCOVERY_PORT, BCAST_HOST, UDP_MAX_SIZE


def main(timeout: float = 5, bcast_hz: float = 50) -> Generator[str, None, None]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setblocking(False)

    found = set()
    interval = 1 / bcast_hz
    start = time()
    deadline = start + timeout

    while time() <= deadline:
        sock.sendto(b"hello", (BCAST_HOST, DISCOVERY_PORT))
        sleep(interval)
        try:
            response = sock.recvfrom(UDP_MAX_SIZE)
        except BlockingIOError:
            continue
        host = response[1][0]
        if host in found:
            continue
        found.add(host)
        yield host

    if not found:
        end = time()
        raise TimeoutError(f"No board found on local network after {end - start:.3f}s.")
