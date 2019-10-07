from textwrap import indent

from . import command_client


def run_code(addr: str, code: str) -> dict:
    code = f"def main(_):\n" + indent(code, " ")
    return command_client.main(addr, "exec_func", code)
