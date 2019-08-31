import sys
from dataclasses import asdict
from pathlib import Path
from pprint import pprint
from time import sleep

import click
import serial

from ampy import board_finder, firmware_builder
from ampy.firmware_builder import generate_main_py
from ampy.settings import BAUD


@click.group()
def cli():
    pass


@cli.add_command
@click.command()
def devices():
    for board in board_finder.main():
        pprint(asdict(board))


@cli.add_command
@click.command()
@click.option("--port", "-p")
@click.option("--baud", "-b", default=BAUD)
def logs(port, baud):
    if not port:
        port = next(board_finder.main()).port
    print(click.style(f"Streaming logs for port: {port}", fg="cyan"))
    sleep(0.5)  # remove garbage from reset
    with serial.Serial(port, baudrate=baud) as ser:
        ser.flush()
        while True:
            sys.stdout.buffer.write(ser.read(1))
            sys.stdout.buffer.flush()


@cli.add_command
@click.command()
@click.argument("firmware")
def flash(firmware):
    for board in board_finder.main():
        board.flash(firmware)


@cli.add_command
@click.command()
@click.option("--module", type=click.Path(exists=True, resolve_path=True))
@click.argument("entrypoints", nargs=-1)
def build(module, entrypoints):
    for board in board_finder.main():
        print("Building firmware for:", board)
        firmware = firmware_builder.main(
            board, generate_main_py(entrypoints), Path(module)
        )
        print("Built firmware:", firmware)
