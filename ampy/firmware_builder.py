import secrets
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import time
from typing import Iterable

from pkg_resources import EntryPoint

from ampy import board_finder
from ampy.settings import TMP_DIR
from ampy.util import call

HOME = "/home/docker"
ESP_INIT_DATA = f"{HOME}/esp-open-sdk/sdk/bin/esp_init_data_default.bin"
MP_DIR = f"{HOME}/micropython"
DOCKER_IMG = "pycampers/micropython:prebuilt"


@dataclass
class Port:
    name: str
    build_dir: str


def generate_main_py(entrypoints: Iterable[EntryPoint]):
    outfile = TMP_DIR / f"{secrets.token_urlsafe(8)}-main.py"
    with open(outfile, "w") as f:
        for ep in entrypoints:
            f.write(f"import {ep.module_name}\n{ep.module_name}.{ep.attrs[0]}()")
    return outfile


def main(port: Port, main_py: Path, code: Path, *, extra_files=None):
    outfile = (
            TMP_DIR
            / f"{'esp8266'} {datetime.now().strftime('%d-%m-%Y_%I-%M-%S_%p')} firmware-combined.bin"
    )
    if extra_files is None:
        extra_files = {}

    container = f"ampy-builder--{secrets.token_urlsafe(8)}"
    port_dir = f"{MP_DIR}/ports/{port.name}"

    # start a container
    call(
        "docker",
        "run",
        "-td",  # keeps container running in background
        f"-w={port_dir}",
        f"--name={container}",
        DOCKER_IMG,
    )

    try:
        # copy code from host to container
        call("docker", "cp", code, f"{container}:{port_dir}/modules")
        call("docker", "cp", main_py, f"{container}:{port_dir}/modules/main.py")

        # build firmware
        call("docker", "exec", container, "make")

        # copy build output from container to host
        files = {
            f"{port_dir}/{port.build_dir}/firmware-combined.bin": outfile,
            **extra_files,
        }
        for src, dest in files.items():
            call("docker", "cp", f"{container}:{src}", dest)
    finally:
        call("docker", "rm", "-f", container)

    return outfile


if __name__ == "__main__":
    s = time()
    board = next(board_finder.main())
    print(board)

    firmware = main(
        Port("esp8266", "build"),
        generate_main_py([EntryPoint.parse("x=hello:main")]),
        Path(__file__).parent / "hello.py",
        extra_files={ESP_INIT_DATA: Path.cwd()},
    )

    call("esptool.py", f"--port={board.port}", "erase_flash")
    call("esptool.py", f"--port={board.port}", "write_flash", "--verify", "0", firmware)
    print(time() - s)
