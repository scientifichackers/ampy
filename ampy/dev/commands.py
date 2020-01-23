import socket
from typing import Tuple, Optional

from ampy.dev_upy import settings
from . import command_client


def exec_func(host: str, main_fn: str, *fn_args, **fn_kwargs) -> dict:
    return command_client.send_recv(host, "exec_func", main_fn, fn_args, fn_kwargs)


def send_ctrl_c(host: str) -> dict:
    return command_client.send_recv(host, "send_ctrl_c")


def get_config(host: str, config: dict) -> dict:
    return command_client.send_recv(host, 'get_config', config)


def update_config(host: str, config: dict) -> dict:
    return command_client.send_recv(host, 'update_config', config)


def reset(host: str, hard: bool = False):
    command_client.send(host, 'reset', hard)


def exec_code(
    host: str, src: str, *, silent: bool = False
) -> Tuple[dict, Optional[socket.socket]]:
    port = None

    if not silent:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((settings.LOCAL_HOST, 0))
        sock.listen()
        port = sock.getsockname()[1]

    response = command_client.send_recv(host, "exec_code", src, port)
    if silent:
        return response, None
    else:
        return response, sock.accept()[0]
