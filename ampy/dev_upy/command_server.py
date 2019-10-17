import errno
import json
import socket
import struct

from . import virtual_term
from . import commands
from .settings import (
    MAX_TCP_CONNECTIONS,
    TCP_MAX_SIZE,
    UINT_FMT,
    UINT_SIZE,
    COMMANDS_PORT,
    LOCAL_HOST,
)


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((LOCAL_HOST, COMMANDS_PORT))
    sock.listen(MAX_TCP_CONNECTIONS)
    sock.setblocking(False)

    def poll(_):
        try:
            client = sock.accept()
        except OSError as e:
            if e.args[0] != errno.EAGAIN:
                raise
        else:
            handle_client(*client)

    return poll


_data_mv = memoryview(bytearray(TCP_MAX_SIZE))


def handle_client(sock, addr):
    print("recv conn:", sock, addr)
    success_result = json.dumps({"status": "success"}).encode()

    try:
        sock.setblocking(True)
        f = sock.makefile()
        try:
            # read the first UINT_SIZE to determine the size of payload
            size_buf = f.read(UINT_SIZE)
            size = struct.unpack(UINT_FMT, size_buf)[0]

            # don't accept payload that's too large
            if size > len(_data_mv):
                return

            # read the payload into the memoryview, and json-decode it
            f.readinto(_data_mv, size)
            req = json.loads(_data_mv[:size])
            print("recv req:", addr, req)

            # dynamic dispatch, for calling a function defined in the "commands" module
            func = getattr(commands, req["cmd"])

            virtual_term.write_clients[addr] = f
            try:
                result = func(addr[0], *req["args"])
            finally:
                del virtual_term.write_clients[addr]
            print("req result:", result)

            if result is None:
                result = success_result
            else:
                result = json.dumps(result).encode()
            f.write(result)
        finally:
            f.close()
    finally:
        sock.close()
