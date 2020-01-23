import sys

import click
import serial

from ampy.cli.util import pass_single_board
from ampy.core import board_finder
from . import cli

stdout = sys.stdout.buffer


@cli.add_command
@click.command()
@pass_single_board
def logs(board: board_finder.MpyBoard):
    """
    Stream logs from device, over USB serial connection.

    Note: This will hard-reset the board when run.
    """
    print(f"Streaming output for: {board}.\n" f"You may need to reset the device once.")
    with serial.Serial(board.port, baudrate=board.baud) as ser:
        ser.flush()
        while True:
            stdout.write(ser.read(1))
            stdout.flush()
