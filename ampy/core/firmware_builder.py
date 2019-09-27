import secrets
import shutil
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterable, NamedTuple

from pkg_resources import EntryPoint

from ampy.core.mpy_boards import MpyBoard
from ampy.core.settings import TMP_DIR


class ItemToCopy(NamedTuple):
    src: Path
    dest: Path


def main(board: MpyBoard, entrypoints: Iterable[str], modules: Iterable[Path]) -> Path:
    main_py = generate_main_py(entrypoints, modules)
    print("-" * 10 + " main.py " + "-" * 10, main_py.read_text(), "-" * 29, sep="\n")

    with clean_copy(
        # include generated main.py file in build
        ItemToCopy(src=main_py, dest=board.modules_dir / "main.py"),
        # include specified modules in build
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


def generate_main_py(entrypoints: Iterable[str], modules: Iterable[Path]):
    outfile = TMP_DIR / f"{secrets.token_urlsafe(8)}-main.py"

    with open(outfile, "w") as f:
        if entrypoints:
            for entrypoint_str in entrypoints:
                # parse entrypoint string of the format "<module>:<attrs>"
                entrypoint_obj = EntryPoint.parse(f"name={entrypoint_str} [extras]")

                # write import statement
                f.write(f"import {entrypoint_obj.module_name}\n")

                # write function call if provided
                if not entrypoint_obj.attrs:
                    continue
                f.write(f"{entrypoint_obj.module_name}.{entrypoint_obj.attrs[0]}()\n")
        else:
            # if no explicit entrypoint was provided, use the modules
            for module in modules:
                if module.is_dir():
                    # if it's a package, execute the __main__.py file
                    if not (module / "__main__.py").exists():
                        continue
                    f.write(f"import {module.name}.__main__")
                else:
                    f.write(f"import {module.name}")

    return outfile
