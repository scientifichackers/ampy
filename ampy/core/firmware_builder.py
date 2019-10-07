import io
import shutil
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterable, Tuple, Optional

from pkg_resources import EntryPoint

from ampy.core.mpy_boards import MpyBoard
from ampy.core.settings import TMP_DIR


def main(board: MpyBoard, entrypoint: Optional[str], modules: Iterable[Path]) -> Path:
    main_py = generate_main_py(entrypoint, modules)
    print("-" * 10 + " main.py " + "-" * 10, main_py, "-" * 29, sep="\n")

    with clean_create(
        # include generated main.py file in build
        (main_py, board.modules_dir / "main.py")
    ), clean_copy(
        # include specified modules in build
        *((module, board.modules_dir / module.name) for module in modules)
    ):
        board.build()
        return shutil.copy(
            board.firmware_bin,
            TMP_DIR
            / f"{board.chip}-firmware@{datetime.now().strftime('%d-%m-%Y_%I-%M-%S_%p')}.bin",
        )


@contextmanager
def clean_copy(*to_copy: Tuple[Path, Path]):
    with ensure_rm_r(*(it[1] for it in to_copy)):
        for src, dest in to_copy:
            print(f"Copying '{src}' -> '{dest}'...")
            try:
                shutil.copy(src, dest)
            except IsADirectoryError:
                shutil.copytree(src, dest)
        yield


@contextmanager
def clean_create(*to_create: Tuple[str, Path]):
    with ensure_rm_r(*(it[1] for it in to_create)):
        for text, dest in to_create:
            print(f"Creating '{dest}'...")
            dest.write_text(text)
        yield


@contextmanager
def ensure_rm_r(*paths: Path):
    rm_r(*paths)
    try:
        yield
    finally:
        rm_r(*paths)


def rm_r(*paths: Path):
    for path in paths:
        print(f"Deleting '{path}'...")
        try:
            shutil.rmtree(path)
        except FileNotFoundError:
            pass
        except NotADirectoryError:
            path.unlink()


def generate_main_py(entrypoint: Optional[str], modules: Iterable[Path]) -> str:
    with io.StringIO() as f:
        if entrypoint is not None:
            # parse entrypoint string of the format "<module>:<attrs>"
            entrypoint_obj = EntryPoint.parse(f"name={entrypoint} [extras]")

            # write import statement
            f.write(f"import {entrypoint_obj.module_name}\n")

            # write function call if provided
            if entrypoint_obj.attrs:
                f.write(f"{entrypoint_obj.module_name}.{entrypoint_obj.attrs[0]}()\n")
        else:
            # if no explicit entrypoint was provided, use the modules
            for module in modules:
                # if it's a package, import the __main__.py file
                # else, just import the module.
                if module.is_dir():
                    if not (module / "__main__.py").exists():
                        continue
                    f.write(f"import {module.name}.__main__\n")
                    break
                else:
                    f.write(f"import {module.name}\n")
                    break

        return f.getvalue()
