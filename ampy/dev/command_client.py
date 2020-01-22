import json
import socket
import struct
from typing import Any

from ampy.dev_upy.settings import UINT_FMT, TCP_MAX_SIZE, UINT_SIZE, COMMANDS_PORT


def main(host: str, cmd: str, *args: Any) -> dict:
    """
    Run a command with name :param:`cmd` on the board @ :param:`host` with :param:`args`.

    Returns a socket file, for streaming the output of command.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, COMMANDS_PORT))
    sock.send(pack(json.dumps({"cmd": cmd, "args": args}).encode()))
    try:
        return json.loads(sock.recv(TCP_MAX_SIZE))
    finally:
        sock.close()


_max_payload_size = TCP_MAX_SIZE - UINT_SIZE


def pack(data: bytes) -> bytes:
    if len(data) > _max_payload_size:
        raise ValueError("Payload is too large!")
    return struct.pack(UINT_FMT, len(data)) + data
