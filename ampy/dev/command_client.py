import json
import socket
import struct
from contextlib import contextmanager
import typing as T

from ampy.dev_upy.settings import UINT_FMT, TCP_MAX_SIZE, UINT_SIZE, COMMANDS_PORT

MAX_PAYLOAD_SIZE = TCP_MAX_SIZE - UINT_SIZE


def send_recv(host: str, cmd: str, *args: T.Any) -> dict:
    with send(host, cmd, *args) as sock:
        return recv(sock)


@contextmanager
def send(host: str, cmd: str, *args: T.Any) -> T.ContextManager[socket.socket]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, COMMANDS_PORT))
        data = {"cmd": cmd, "args": args}
        payload = pack(json.dumps(data).encode())
        sock.send(payload)
        yield sock
    finally:
        sock.close()


def recv(sock: socket.socket) -> dict:
    return json.loads(sock.recv(TCP_MAX_SIZE))


def pack(data: bytes) -> bytes:
    if len(data) > MAX_PAYLOAD_SIZE:
        raise ValueError("Payload is too large!")
    return struct.pack(UINT_FMT, len(data)) + data
