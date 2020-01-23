import click
from halo import Halo

from ampy.cli.util import FINDING_USB_BOARDS_MSG, ESP32_FAIL_MSG, get_params
from ampy.core import board_finder
from ampy.dev import discovery_client
from . import cli


@cli.add_command
@click.command()
@click.option('-u', '--usb', is_flag=True)
@click.option('-n', '--net', is_flag=True)
@click.option(
    '-t', '--timeout', default=5.0, help='Timeout in seconds for network scan.'
)
def devices(usb: bool, net: bool, timeout: float):
    """
    List all micropython devices attached via USB serial port, or via the same network.

    By default this will scan both USB serial ports and the network,
    unless either --usb or --net is explicitly specified.

    Note: This will hard-reset the board when run.
    """
    count = 0

    if not (usb or net):
        usb = net = True

    if net:
        with Halo(text="Finding boards on local network.") as spinner:
            try:
                for host in discovery_client.main(timeout=timeout):
                    spinner.clear()
                    count += 1
                    print(f"({count}) Remote board @ {host!r}")
            except TimeoutError as e:
                spinner.fail(str(e))
            else:
                spinner.succeed()

    if usb:
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
