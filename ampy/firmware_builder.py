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


def main(board: MpyBoard, main_py: Path, mpy_code: Path) -> Path:
    update_mpy_repo()

    with clean_copy(
        ItemToCopy(src=main_py, dest=board.modules_dir / "main.py"),
        ItemToCopy(src=mpy_code, dest=board.modules_dir / mpy_code.name),
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
            shutil.rmtree(item.dest)
        except FileNotFoundError:
            pass
        except NotADirectoryError:
            item.dest.unlink()


def generate_main_py(entrypoints: Iterable[str]):
    outfile = TMP_DIR / f"{secrets.token_urlsafe(8)}-main.py"

    with open(outfile, "w") as f:
        for ep_str in entrypoints:
            ep = EntryPoint.parse(ep_str)
            f.write(f"import {ep.module_name}\n")
            if not ep.attrs:
                continue
            f.write(f"{ep.module_name}.{ep.attrs[0]}()\n")

    return outfile


if __name__ == "__main__":
    s = time()
    board = next(board_finder.main())
    print(board)

    firmware = main(
        board,
        generate_main_py(["task1=testmodule.hello:main", "task2=testmodule.bye"]),
        Path(__file__).parent / "testmodule",
    )
    print(firmware)

    board.flash(firmware)
    print(time() - s)
