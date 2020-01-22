import errno
import json
import socket
import struct

from . import commands
from . import settings


def main():
    # bind a non-blocking TCP socket to LOCAL_HOST:DISCOVERY_PORT
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((settings.LOCAL_HOST, settings.COMMANDS_PORT))
    sock.listen(settings.MAX_TCP_CONNECTIONS)
    sock.setblocking(False)

    mem = memoryview(bytearray(settings.TCP_MAX_SIZE))

    def poll(_):
        try:
            client = sock.accept()
        except OSError as e:
            if e.args[0] != errno.EAGAIN:
                raise
        else:
            handle_client(*client)

    def handle_client(conn, addr):
        f = conn.makefile()
        try:
            conn.setblocking(True)
            # read the first 'UINT_SIZE' bytes to determine the size of payload
            size_buf = f.read(settings.UINT_SIZE)
            size = struct.unpack(settings.UINT_FMT, size_buf)[0]

            # don't accept a payload that's too large
            if size > len(mem):
                return

            # read the payload into the memoryview, and json-decode it
            f.readinto(mem, size)
            req = json.loads(mem[:size])
            print("[ampy] recv:", addr, req)

            # use dynamic dispatch,
            # for calling the function whose name is available in the request
            cmd = getattr(commands, req["cmd"])

            reply = {"status": "success"}
            try:
                # call the command, with the hostname,
                # and positional arguments provided in the request
                reply["result"] = cmd(addr[0], *req["args"])
            except Exception as e:
                reply["status"] = "failed"
                reply["result"] = repr(e)

            f.write(json.dumps(reply).encode())
            print("[ampy] sent:", addr, reply)
        finally:
            conn.close()
            f.close()

    return poll
