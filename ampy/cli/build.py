import shutil
from pathlib import Path
from typing import Optional, List

import click

from ampy.cli.util import pass_many_boards
from ampy.core import board_finder, firmware_builder
from ampy.core.settings import DEV_MODULE, MPY_REPO_DIR
from ampy.core.util import clean_mpy_repo, update_mpy_repo
from . import cli


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
