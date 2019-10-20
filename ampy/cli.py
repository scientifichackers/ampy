import shutil
import sys
from functools import update_wrapper
from pathlib import Path
from typing import Optional, List

import click
import dotenv
import serial
from bullet import Bullet, Check
from halo import Halo

from ampy.core import board_finder, firmware_builder
from ampy.core.settings import DEV_MODULE, MPY_REPO_DIR
from ampy.core.util import clean_mpy_repo, update_mpy_repo
from ampy.dev import discovery_client, commands

ESP32_FAIL_MSG = """\
\tNote: If you're using an ESP32, you may need to hold down the 'BOOT' button on your device while runing this command.
\t      Read more @ https://randomnerdtutorials.com/solved-failed-to-connect-to-esp32-timed-out-waiting-for-packet-header/\
"""

# Load AMPY_PORT et al from ~/.ampy file
# Performed here because we need to beat click's decorators.
config = dotenv.find_dotenv(filename=".ampy", usecwd=True)
if config:
    dotenv.load_dotenv(dotenv_path=config)


@click.group()
@click.option(
    "--port",
    "-p",
    envvar="AMPY_PORT",
    required=False,
    help="Name of serial port for connected board.\n\n"
    "Can be optionally specified with 'AMPY_PORT' environment variable.",
)
@click.option(
    "--baud",
    "-b",
    envvar="AMPY_BAUD",
    default=115200,
    help="Baud rate for the serial connection (default 115200).\n\n"
    "Can be optionally specified with 'AMPY_BAUD' environment variable.",
)
@click.pass_context
def cli(ctx: click.Context, port: Optional[str], baud: int):
    ctx.obj = {"port": port, "baud": baud}


def find_boards() -> List[board_finder.MpyBoard]:
    obj = click.get_current_context().obj
    port = obj["port"]
    baud = obj["baud"]

    with Halo(text="Finding boards connected to your computer.") as spinner:
        if port is not None:
            boards = [board_finder.detect_board(port, baud)]
        else:
            boards = list(board_finder.main(baud))

        if not boards:
            spinner.fail(click.style("No boards detected!", fg="red"))
            print(ESP32_FAIL_MSG)
            exit(1)
        spinner.succeed()

    return boards


def pass_many_boards(f):
    def new_func(*args, **kwargs):
        boards = find_boards()

        if len(boards) > 1:
            choices = {str(it): it for it in boards}
            boards = [
                choices[it]
                for it in Check(
                    prompt="Please choose any number of boards you want",
                    choices=list(choices.keys()),
                ).launch()
            ]

        f(boards, *args, **kwargs)

    return update_wrapper(new_func, f)


def pass_single_board(f):
    def new_func(*args, **kwargs):
        boards = find_boards()

        if len(boards) > 1:
            choices = {str(it): it for it in boards}
            board = choices[
                Bullet(
                    prompt="Please choose a single board", choices=list(choices.keys())
                ).launch()
            ]
        else:
            board = boards[0]

        f(board, *args, **kwargs)

    return update_wrapper(new_func, f)


@cli.add_command
@click.command()
def devices():
    """
    List all micropython boards attached via USB serial port.

    Note: This will soft-reset all devices when run.
    """
    count = 0

    with Halo(text="Finding boards connected to your computer.") as spinner:
        obj = click.get_current_context().obj
        baud = obj["baud"]
        found = False
        for board in board_finder.main(baud):
            found = True
            spinner.clear()
            count += 1
            print(f"({count}) {board!r}")
        if not found:
            spinner.fail(
                click.style("No board is connected to your computer.", fg="red")
            )
            print(ESP32_FAIL_MSG)
        else:
            spinner.succeed()

    with Halo(text="Finding boards on local network.") as spinner:
        try:
            for host in discovery_client.main():
                spinner.clear()
                count += 1
                print(f"({count}) Remote board @ {host!r}")
        except TimeoutError as e:
            spinner.fail(str(e))
        else:
            spinner.succeed()


@cli.add_command
@click.command()
@pass_single_board
def logs(board: board_finder.MpyBoard):
    """
    Stream logs from device, through serial connection.
    """
    print(f"Streaming output for: {board}.\n" f"You may need to reset the device once.")
    with serial.Serial(board.port, baudrate=board.baud) as ser:
        ser.flush()
        while True:
            sys.stdout.buffer.write(ser.read(1))
            sys.stdout.buffer.flush()


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


@cli.add_command
@click.command()
@click.option(
    "--clean", "-c", is_flag=True, help="Clean local build cache.", is_eager=True
)
@click.option(
    "--mpy-version",
    "-u",
    help="Micropython repo's git tag or branch. " "Uses 'master' branch by default",
    required=True,
    default="master",
)
@click.option("--dev", "-d", is_flag=True, is_eager=True)
@click.option("--offline", is_flag=True, help="Offline mode.")
@click.option(
    "--module",
    "-m",
    type=click.Path(exists=True, resolve_path=True),
    multiple=True,
    help="Path to python package or script. Can be used multiple times.",
)
@click.option("--entrypoint", "-e", help="Script or Function to be called after boot.")
@click.option("--yes", "-y", is_flag=True, help="Don't ask for confirmation.")
@click.option("--output-path", "-o")
@pass_many_boards
def build(
    boards: List[board_finder.MpyBoard],
    clean: bool,
    module: List[str],
    entrypoint: Optional[str],
    yes: bool,
    dev: bool,
    output_path: str,
    mpy_version: str,
    offline: bool,
):
    """Build micropython firmware."""
    modules = [Path(i) for i in module]

    if clean:
        clean_mpy_repo()
        return

    if output_path and len(boards) > 1:
        print(
            click.style(
                "The '--output-path' option is ambiguous with multiple boards attached.",
                fg="red",
            )
        )

    if dev:
        if entrypoint is not None:
            print(
                click.style(
                    "It might not be a good idea to use '--entrypoint' with '--dev'!",
                    fg="red",
                )
            )
        modules = [DEV_MODULE] + modules

    if offline:
        if not MPY_REPO_DIR.exists():
            print(
                click.style(
                    "Micropython repository is not cached. Can't proceed in '--offline' mode.",
                    fg="red",
                )
            )
            print(
                f"You can manually place the repository @ '{MPY_REPO_DIR}', "
                f"but make sure to recursively clone the submodules."
            )
            exit(1)
    else:
        update_mpy_repo(mpy_version)

    for board in boards:
        print("Building firmware for:", board)
        firmware = firmware_builder.main(board, entrypoint, modules)

        if output_path is not None:
            shutil.copy(firmware, output_path)
            firmware = Path(output_path)

        print("Built firmware:", firmware)

        if not yes and not click.confirm(
            "Do you want to flash this firmware right now? You can flash it later using:"
            f"\n\t$ ampy flash '{firmware}'\n"
        ):
            continue

        board.flash(firmware)


stdout = sys.stdout.buffer


@cli.add_command
@click.command()
@click.argument("script", type=click.Path(exists=True, dir_okay=False))
def run(script: str):
    """
    Remotely execute code on a board.

    This will first, try to find a board on the network,
    and then send the contents of the provided script.
    The board will then, stream the output from the script.

    The script must contain a main() function like so:

    \b
        def main(host):
            ...

    where, host is the hostname or IP address of
    of the computer that sent the request, as visible from the board.
    """
    code = Path(script).read_text()

    host = next(discovery_client.main())
    print("Found board @", host)

    with commands.exec_func(host, code) as f:
        while True:
            b = f.read(1)
            if not b:
                return
            stdout.write(b)
            stdout.flush()


if __name__ == "__main__":
    cli()
