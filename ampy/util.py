import os
from distutils.spawn import find_executable

from ampy import pyboard
from ampy.colors import *


def find(name: str) -> str:
    path = find_executable(name)
    if path is None:
        raise FileNotFoundError(
            f"{name!r} could not be found in PATH. Please make sure it is installed correctly."
        )
    return path


def _picocom(board: pyboard.Pyboard, program_path: str):
    os.execv(program_path, [program_path, board.device, "-b", str(board.baudrate)])


def _screen(board: pyboard.Pyboard, program_path: str):
    os.execv(program_path, [program_path, board.device, str(board.baudrate)])


def _telnet(board: pyboard.Pyboard, program_path: str):
    os.execv(program_path, [program_path, board.device])


_program_dispatch = {
    "telnet": _telnet,
    "picocom": _picocom,
    "screen": _screen,
}


def invoke_repl(board: pyboard.Pyboard, program_name: str, program_path: str):
    print(bold(f"Launching uPy REPL using {green(program_name)}..."))
    return _program_dispatch[program_name](board, program_path)


def windows_full_port_name(portname):
    # Helper function to generate proper Windows COM port paths.  Apparently
    # Windows requires COM ports above 9 to have a special path, where ports below
    # 9 are just referred to by COM1, COM2, etc. (wacky!)  See this post for
    # more info and where this code came from:
    # http://eli.thegreenplace.net/2009/07/31/listing-all-serial-ports-on-windows-with-python/
    m = re.match("^COM(\d+)$", portname)
    if m and int(m.group(1)) < 10:
        return portname
    else:
        return "\\\\.\\{0}".format(portname)
