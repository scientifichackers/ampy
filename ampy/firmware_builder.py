import secrets
import shutil
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from time import time
from typing import Iterable, NamedTuple

from pkg_resources import EntryPoint

from ampy import board_finder
from ampy.mpy_boards import MpyBoard
from ampy.settings import TMP_DIR
from ampy.util import update_mpy_repo


class ItemToCopy(NamedTuple):
    src: Path
    dest: Path


def main(board: MpyBoard, main_py: Path, modules: Iterable[Path]) -> Path:
    update_mpy_repo()

    with clean_copy(
        ItemToCopy(src=main_py, dest=board.modules_dir / "main.py"),
        *(
            ItemToCopy(src=module, dest=board.modules_dir / module.name)
            for module in modules
        ),
    ):
        board.build()
        return shutil.copy(
            board.firmware_bin,
            TMP_DIR
            / f"{board.chip}-firmware@{datetime.now().strftime('%d-%m-%Y_%I-%M-%S_%p')}.bin",
        )


@contextmanager
def clean_copy(*items: ItemToCopy):
    delete_multiple(*items)
    for item in items:
        print(f"Copying '{item.src}' -> '{item.dest}'...")
        try:
            shutil.copy(item.src, item.dest)
        except IsADirectoryError:
            shutil.copytree(item.src, item.dest)
    try:
        yield
    finally:
        delete_multiple(*items)


def delete_multiple(*items: ItemToCopy):
    for item in items:
        try:
            print(f"Deleting '{item.dest}'...")
            shutil.rmtree(item.dest)
        except FileNotFoundError:
            pass
        except NotADirectoryError:
            item.dest.unlink()


def generate_main_py(entrypoints: Iterable[str]):
    outfile = TMP_DIR / f"{secrets.token_urlsafe(8)}-main.py"

    with open(outfile, "w") as f:
        for entrypoint_str in entrypoints:
            # parse entrypoint string of the format "<module>:<attrs>"
            entrypoint_obj = EntryPoint.parse(f"name={entrypoint_str} [extras]")

            # write import statement
            f.write(f"import {entrypoint_obj.module_name}\n")

            # write function call if provided
            if not entrypoint_obj.attrs:
                continue
            f.write(f"{entrypoint_obj.module_name}.{entrypoint_obj.attrs[0]}()\n")

    return outfile


if __name__ == "__main__":
    s = time()
    board = next(board_finder.main())
    print(board)

    firmware = main(
        board,
        generate_main_py(["testmodule.hello:main", "testmodule.bye"]),
        "dw",
    )
    print(firmware)

    board.flash(firmware)
    print(time() - s)
