from pprint import pformat, pprint

import click
from click import style

from ampy.cli.util import pass_dev_board, DEV_FIRMWARE_NOTE
from ampy.dev import commands
from . import cli


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
    print(f'Updated config:\n{pformat(conf)}')
    commands.reset(dev_board)
