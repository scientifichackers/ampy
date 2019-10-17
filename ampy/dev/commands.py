import io
from typing import ContextManager

from . import command_client


def exec_func(host: str, main_fn: str, *fn_args, **fn_kwargs) -> ContextManager[io.BytesIO]:
    return command_client.main(host, "exec_func", main_fn, fn_args, fn_kwargs)


def open_term(host: str, mode: str = "rw") -> ContextManager[io.BytesIO]:
    return command_client.main(host, "open_term", mode)


# def download_user_code(host: str, code: str) -> ContextManager[io.BytesIO]:
