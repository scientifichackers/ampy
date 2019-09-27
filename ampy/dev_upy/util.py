import errno


def bind_to_random_port(sock, addr):
    for port in range(65535, 0, -1):
        try:
            sock.bind((addr, port))
        except OSError as e:
            if e.args[0] != errno.EADDRINUSE:
                raise
        else:
            return addr


def recvall(sock, *, chunksize=256):
    data = b""
    while True:
        chunk = sock.recvfrom(chunksize)
        if not chunk:
            break
        data += chunk
    return data
