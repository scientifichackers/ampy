import typing as T

import click
import dotenv


def main():

    # Load AMPY_PORT et al from ~/.ampy file
    # Performed here because we need to beat click's decorators.
    config = dotenv.find_dotenv(filename=".ampy", usecwd=True)
    if config:
        dotenv.load_dotenv(dotenv_path=config)

    cli()


@click.group()
@click.option(
    "--port",
    "-p",
    envvar="AMPY_PORT",
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
def cli(ctx: click.Context, port: T.Optional[str], baud: int):
    ctx.obj = {"port": port, "baud": baud}
