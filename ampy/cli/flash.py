from pathlib import Path
from typing import List

import click

from ampy.cli.util import pass_many_boards
from ampy.core import board_finder
from . import cli


@cli.add_command
@click.command()
@click.argument("firmware", type=click.Path(exists=True, resolve_path=True))
@pass_many_boards
def flash(boards: List[board_finder.MpyBoard], firmware: str):
    """Flash micropython firmware."""
    f = Path(firmware)
    for board in boards:
        print(f"Flashing firmware to board: {board}")
        board.flash(f)
