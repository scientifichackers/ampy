import io
import json
import socket
import struct
from contextlib import contextmanager
from typing import Any, ContextManager

from ampy.dev_upy.settings import UINT_FMT, TCP_MAX_SIZE, UINT_SIZE, COMMANDS_PORT


@contextmanager  # type: ignore
def main(host: str, cmd: str, *args: Any) -> ContextManager[io.BytesIO]:
    """
    Run a command with name :param:`cmd` on the board @ :param:`host` with :param:`args`.


    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, COMMANDS_PORT))
    sock.send(pack(json.dumps({"cmd": cmd, "args": args}).encode()))

    f = sock.makefile(mode="rb")
    try:
        yield f
    finally:
        f.close()
        sock.close()


_max_payload_size = TCP_MAX_SIZE - UINT_SIZE


def pack(data: bytes) -> bytes:
    if len(data) > _max_payload_size:
        raise ValueError("Payload is too large!")
    return struct.pack(UINT_FMT, len(data)) + data


# if __name__ == "__main__":
# # addr = discovery_client.main()
# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# sock.bind(("0.0.0.0", 2456))
#
# stdout = sys.stdout.buffer
#
# stdin = sys.stdin.buffer
# orig_fl = fcntl.fcntl(stdin, fcntl.F_GETFL)
# fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)
# # print(main(addr, "open_term", 2456))
#
# buf = memoryview(bytearray(65535))
# addrs = set()
#
# def on_sock():
#     n, addr = sock.recvfrom_into(buf, len(buf))
#     addrs.add(addr)
#     stdout.write(buf[:n])
#     stdout.flush()
#
# def on_stdin():
#     b = stdin.read()
#     for addr in addrs:
#         sock.sendto(b, addr)
#
# dispatch = {sock: on_sock, stdin: on_stdin}
#
# while True:
#     for f in select.select([sock, stdin], [], [])[0]:
#         dispatch[f]()

# print(sock.recvfrom(1024))\textbf{}
# main(("192.168.43.144", 65533))
