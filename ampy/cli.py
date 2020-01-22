import shutil
import sys
from pathlib import Path
from pprint import pformat, pprint
from typing import Optional, List

import click
import dotenv
import serial
from click import style
from halo import Halo

from ampy.core import board_finder, firmware_builder
from ampy.core.settings import DEV_MODULE, MPY_REPO_DIR
from ampy.core.util import clean_mpy_repo, update_mpy_repo
from ampy.dev import discovery_client, commands
from .cli_util import (
    pass_dev_board,
    pass_many_boards,
    pass_single_board,
    FINDING_USB_BOARDS_MSG,
    ESP32_FAIL_MSG,
    DEV_FIRMWARE_NOTE,
    get_params,
)

stdout = sys.stdout.buffer


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


@cli.add_command
@click.command()
def devices():
    """
    List all micropython devices attached via USB serial port, or via the same network.

    Note: This will hard-reset the board when run.
    """
    count = 0

    with Halo(text=FINDING_USB_BOARDS_MSG) as spinner:
        params = get_params()
        baud = params["baud"]
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
    Stream logs from device, over USB serial connection.

    Note: This will hard-reset the board when run.
    """
    print(f"Streaming output for: {board}.\n" f"You may need to reset the device once.")
    with serial.Serial(board.port, baudrate=board.baud) as ser:
        ser.flush()
        while True:
            stdout.write(ser.read(1))
            stdout.flush()


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
@click.option(
    "--dev", "-d", is_flag=True, is_eager=True, help='Flash the development firmware.'
)
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


@cli.add_command
@click.command(
    help=f"""\
Remotely configure a micropython board.

{style('STA_IF', bold=True, bg='black', fg='green')}

Passing --sta-ssid will enable STA_IF \
i.e., connect to the specified SSID. \
--sta-password can be also be specified.

{style('AP_IF', bold=True, bg='black', fg='blue')}

Passing --disable-ap will disable AP_IF \
i.e., turn off the board's own WiFi hotspot.

If --ap-password is not specified, \
then AUTH_OPEN will be used, otherwise AUTH_WPA_WPA2_PSK is used.   

If --ap-ssid is not specified, \
this will use the default SSID and Password. \
Default AP SSID is unique to the board, \
and Password is "micropythoN" (note the upper-case N).

Read more @ https://docs.micropython.org/en/latest/esp8266/tutorial/intro.html#wifi.

{style('TIMER', bold=True, bg='black', fg='yellow')}

The ampy dev firmware needs a micropython Timer for background tasks. \
It uses the Timer with id 0 by default. \

If your application depends this, \
then you can explicitly specify a different Timer id that ampy should use.

{DEV_FIRMWARE_NOTE}
    """
)
@click.option(
    '--sta-ssid',
    envvar='AMPY_STA_SSID',
    help='SSID of WiFi network the board should connect to.',
)
@click.option(
    '--sta-password',
    envvar='AMPY_STA_PASSWORD',
    help='Password of WiFi network the board should connect to.',
)
@click.option(
    '--ap-ssid',
    envvar='AMPY_AP_SSID',
    help="SSID for the board's own WiFi access point.",
)
@click.option(
    '--ap-password',
    envvar='AMPY_AP_PASSWORD',
    help="Password for the board's own WiFi access point.",
)
@click.option(
    '--disable-ap',
    is_flag=True,
    envvar='AMPY_DISABLE_AP',
    help="Disable the board's own WiFi access point.",
)
@click.option(
    '--timer-id',
    envvar='AMPY_TIMERS',
    help='Timer id that ampy to use for background tasks.',
    default=0,
    type=int,
)
@click.option('--yes', '-y', is_flag=True, help="Don't ask for confirmation.")
@pass_dev_board
def config(dev_board: str, **kwargs):
    pprint(kwargs)
    if not click.confirm('Write this config to the board?'):
        raise click.Abort()
    conf = commands.update_config(dev_board, kwargs)['result']
    print(f'Updated config: {pformat(conf)}')
    commands.reset(dev_board)


if __name__ == "__main__":
    # Load AMPY_PORT et al from ~/.ampy file
    # Performed here because we need to beat click's decorators.
    config = dotenv.find_dotenv(filename=".ampy", usecwd=True)
    if config:
        dotenv.load_dotenv(dotenv_path=config)

    cli()
