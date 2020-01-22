import socket
import sys

import machine

from . import config
from .remote_term import RemoteTerm
from .repl_man import ReplMan


def exec_func(host: str, main_fn: str, fn_args: tuple, fn_kwargs: dict):
    # code called inside exec() can't modify variables, but can mutate them.
    # So just use a dict to store the output of the main() function.
    result = {"value": None}

    code = main_fn + "\nresult['value'] = main(host, *fn_args, **fn_kwargs)"
    locals = {
        "result": result,
        "host": host,
        "fn_args": fn_args,
        "fn_kwargs": fn_kwargs,
    }

    exec(code, locals)
    return result["value"]


def send_ctrl_c(_):
    RemoteTerm.get_instance().send_ctrl_c()


def update_config(_, conf: dict) -> dict:
    config.conf = conf
    config.store()
    return config.conf


def reset(_, hard: bool = False):
    if hard:
        sys.exit()
    else:
        machine.reset()


def exec_code(host: str, src: str, port: int):
    repl = ReplMan.get_instance()

    if port is None:
        conn = None
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        addr = (host, port)
        sock.connect(addr)
        conn = addr, sock

    repl.mode = repl.get_exec_code_mode(src, conn)
