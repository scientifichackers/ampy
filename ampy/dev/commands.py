import io
from typing import ContextManager

from . import command_client


def exec_func(host: str, code: str) -> ContextManager[io.BytesIO]:
    return command_client.main(host, "exec_func", code)


def open_term(host: str, mode: str = "rw") -> ContextManager[io.BytesIO]:
    return command_client.main(host, "open_term", mode)
