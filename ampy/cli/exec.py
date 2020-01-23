import sys
from pathlib import Path

import click
from halo import Halo

from ampy.cli.util import pass_dev_board, DEV_FIRMWARE_NOTE
from ampy.dev import commands
from . import cli

stdout = sys.stdout.buffer


@cli.add_command
@click.command(
    help=f"""
Remotely execute code on a board.

This finds a board on network, runs the provided SCRIPT on it. s

The output from the board is also streamed over TCP.

{DEV_FIRMWARE_NOTE}
    """
)
@click.argument("script", type=click.Path(exists=True, dir_okay=False))
@pass_dev_board
def exec(dev_board: str, script: str):
    code = Path(script).read_text()

    with Halo(text="Sending code to board") as spinner:
        res, f = commands.exec_code(dev_board, code)
        try:
            if res["status"] == "failed":
                spinner.fail(click.style(f"That didn't work! ({res})", fg='red'))
                exit(1)

            spinner.succeed("Sent code. Now streaming logs...")

            while True:
                b = f.recv(1024)
                if not b:
                    return
                stdout.write(b)
                stdout.flush()
        finally:
            f.close()
