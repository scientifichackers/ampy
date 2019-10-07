import struct

from .settings import UINT_FMT, UINT_SIZE


def tcp_sock_read(sock, buf):
    f = sock.makefile()

    # read the first few bytes,
    # that contain the size of the actual payload,
    # packed via UINT_FMT.
    size = struct.unpack(UINT_FMT, f.read(UINT_SIZE))[0]

    # refuse to accept oversized payload
    if size > len(buf):
        return

    # read the payload into memory
    f.readinto(buf, size)

    # process received data
    return buf[:size]
