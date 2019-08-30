import secrets
import shlex
import shutil
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from time import time
from typing import Iterable, NamedTuple

from pkg_resources import EntryPoint

from ampy.settings import TMP_DIR, CACHE_DIR
from ampy.util import call

ESP_INIT_DATA_BIN = "/home/docker/esp-open-sdk/sdk/bin/esp_init_data_default.bin"
MP_GIT = "https://github.com/micropython/micropython.git"
MP_CACHE_DIR = CACHE_DIR / "micropython"
DOCKER_IMG = "micropython"


class MicropythonPort(NamedTuple):
    name: str
    build_dir_name: str


class ItemToCopy(NamedTuple):
    src: Path
    dest: Path


def main(mp_port: MicropythonPort, main_py: Path, mpy_code: Path) -> Path:
    if not MP_CACHE_DIR.exists():
        call("git", "clone", MP_GIT, MP_CACHE_DIR)

    mp_port_dir = MP_CACHE_DIR / "ports" / mp_port.name
    modules_dir = mp_port_dir / "modules"

    with clean_copy(
        ItemToCopy(src=main_py, dest=modules_dir / "main.py"),
        ItemToCopy(src=mpy_code, dest=modules_dir / mpy_code.name),
    ):
        for build_cmd in [
            "git submodule update --init lib/axtls lib/berkeley-db-1.xx",
            "make -C mpy-cross",
            "make -C ports/esp8266",
        ]:
            call(
                "docker",
                "run",
                f"-v={MP_CACHE_DIR}:{MP_CACHE_DIR}",
                f"-w={MP_CACHE_DIR}",
                DOCKER_IMG,
                *shlex.split(build_cmd),
            )

        return shutil.copy(
            mp_port_dir / mp_port.build_dir_name / "firmware-combined.bin",
            TMP_DIR
            / f"{'esp8266'} {datetime.now().strftime('%d-%m-%Y_%I-%M-%S_%p')} firmware-combined.bin",
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


def generate_main_py(entrypoints: Iterable[EntryPoint]):
    outfile = TMP_DIR / f"{secrets.token_urlsafe(8)}-main.py"
    with open(outfile, "w") as f:
        for ep in entrypoints:
            f.write(f"import {ep.module_name}\n{ep.module_name}.{ep.attrs[0]}()")
    return outfile


if __name__ == "__main__":
    s = time()
    # board = next(board_finder.main())
    # print(board)

    firmware = main(
        MicropythonPort("esp8266", "build"),
        generate_main_py([EntryPoint.parse("x=hello:main")]),
        Path(__file__).parent / "hello.py",
    )
    print(firmware)
    # call("esptool.py", f"--port={board.port}", "erase_flash")
    # call("esptool.py", f"--port={board.port}", "write_flash", "--verify", "0", firmware)
    print(time() - s)
