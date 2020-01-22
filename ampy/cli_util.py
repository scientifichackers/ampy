from functools import update_wrapper
from typing import List

import click
from bullet import Bullet, Check
from halo import Halo

from ampy.core import board_finder
from ampy.dev import discovery_client

FINDING_USB_BOARDS_MSG = "Finding boards connected via USB serial port."

ESP32_FAIL_MSG = """\
\tNote: If you're using an ESP32, you may need to hold down the 'BOOT' button on your device while running this command.
\t      Read more @ https://randomnerdtutorials.com/solved-failed-to-connect-to-esp32-timed-out-waiting-for-packet-header/\
"""

DEV_FIRMWARE_NOTE = (
    'Note: This command only works with a board that '
    'is flashed with ampy development firmware. (see $ ampy flash)'
)


def pass_dev_board(f):
    def new_func(*args, **kwargs):
        with Halo(text="Finding a board on local network.") as spinner:
            try:
                dev_board = next(discovery_client.main())
            except TimeoutError as e:
                spinner.fail(click.style(str(e), fg='red'))
                exit(1)
            spinner.succeed(f"Found board @ {dev_board}")

        f(dev_board, *args, **kwargs)

    return update_wrapper(new_func, f)


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


def find_boards() -> List[board_finder.MpyBoard]:
    params = get_params()
    port = params["port"]
    baud = params["baud"]

    with Halo(text=FINDING_USB_BOARDS_MSG) as spinner:
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


def get_params():
    return click.get_current_context().obj
