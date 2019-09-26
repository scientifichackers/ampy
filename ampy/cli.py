import sys
from dataclasses import asdict
from pathlib import Path
from pprint import pprint

import click
import serial

from ampy import board_finder, firmware_builder
from ampy.firmware_builder import generate_main_py
from ampy.settings import BAUD
from ampy.util import clean_mpy_repo


@click.group()
def cli():
    pass


@cli.add_command
@click.command(
    help="List all micropython boards attached via USB serial port.\n\n"
    "Will soft-reset all devices when run."
)
def devices():
    for board in board_finder.main():
        pprint(asdict(board))


@cli.add_command
@click.command(help="Stream logs from device.")
@click.option("--port", "-p")
@click.option("--baud", "-b", default=BAUD)
def logs(port, baud):
    if not port:
        port = next(board_finder.main()).port
    print(click.style(f"Streaming logs for port: {port}", fg="cyan"))
    with serial.Serial(port, baudrate=baud) as ser:
        ser.flush()
        while True:
            sys.stdout.buffer.write(ser.read(1))
            sys.stdout.buffer.flush()


@cli.add_command
@click.command(help="Flash micropython firmware.")
@click.argument("firmware", type=click.Path(exists=True, resolve_path=True))
def flash(firmware):
    for board in board_finder.main():
        board.flash(Path(firmware))


@cli.add_command
@click.command(help="Build micropython firmware.")
@click.option("--clean", is_flag=True, help="Clean local build cache.")
@click.option(
    "--module",
    "-m",
    type=click.Path(exists=True, resolve_path=True),
    multiple=True,
    help="Path to python module / python script. Can be used multiple times.",
)
@click.option(
    "--entrypoint",
    "-e",
    multiple=True,
    help="Module or function to be executed on boot. Can be used multiple times.",
)
@click.option("--yes", "-y", is_flag=True)
def build(clean, module, entrypoint, yes):
    if clean:
        clean_mpy_repo()
        return

    for board in board_finder.main():
        print("Building firmware for:", board)
        firmware = firmware_builder.main(
            board, generate_main_py(entrypoint), (Path(i) for i in module)
        )
        print("Built firmware:", firmware)

        if not yes and not click.confirm(
            "Do you want to flash this firmware right now? You can flash it later using:"
            f"\n\t$ ampy flash {firmware}\n"
        ):
            continue

        board.flash(Path(firmware))
