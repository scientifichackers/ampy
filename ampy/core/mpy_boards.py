from dataclasses import dataclass, field, fields, _create_fn
from pathlib import Path
from typing import List

import requests

from ampy.core.settings import MPY_REPO_DIR, CACHE_DIR
from ampy.core.util import call, docker_run, extract_espidf_suphash

BUILD_SCRIPTS = Path(__file__).parent.parent / "build_scripts"
ESP_INIT_DATA_FILE = CACHE_DIR / "esp_init_data_default.bin"


@dataclass
class MpyBoard:
    chip: str
    description: str
    flash_size: str
    features: List[str]
    crystal_mhz: int
    mac: str
    port: str
    baud: int
    board_type: str

    board_dir: Path = field(init=False, repr=False)
    build_dir: Path = field(init=False, repr=False)
    modules_dir: Path = field(init=False, repr=False)
    firmware_bin: Path = field(init=False, repr=False)
    docker_image: str = field(init=False, repr=False)

    esp_init_data_url = "https://github.com/espressif/ESP8266_AT/raw/master/bin/esp_init_data_default.bin"

    def build(self):
        ...

    @property
    def esptool_args(self):
        return "esptool.py", f"--chip={self.chip.lower()}", f"--port={self.port}"

    def flash(self, firmware: Path):
        call(*self.esptool_args, "erase_flash")
        if self.flash_size != "16MB":
            return
        if not ESP_INIT_DATA_FILE.exists():
            ESP_INIT_DATA_FILE.write_bytes(requests.get(self.esp_init_data_url).content)
        call(
            *self.esptool_args,
            "write_flash",
            "--verify",
            "0xffc000",
            ESP_INIT_DATA_FILE,
        )

    def __str__(self):
        return f"{self.description} @ {self.port}"


class ESP8266Board(MpyBoard):
    board_dir = MPY_REPO_DIR / "ports" / "esp8266"
    build_dir = board_dir / "build"
    firmware_bin = build_dir / "firmware-combined.bin"
    modules_dir = board_dir / "modules"

    docker_image = "registry.gitlab.com/alelec/docker-esp-open-sdk"
    xtensa_path = "/tools/xtensa-lx106-elf"
    build_script = BUILD_SCRIPTS / "esp8266.sh"

    def build(self):
        docker_run(
            self.docker_image,
            self.build_script,
            env={
                "AMPY_XTENSA_PATH": self.xtensa_path,
                "AMPY_BOARD_DIR": self.board_dir,
            },
        )

    def flash(self, firmware: Path):
        super().flash(firmware)
        call(*self.esptool_args, "write_flash", "--verify", "0", firmware)


class ESP32Board(MpyBoard):
    board_dir = MPY_REPO_DIR / "ports" / "esp32"
    modules_dir = board_dir / "modules"

    @property
    def build_dir(self) -> Path:
        return self.board_dir / f"build-{self.board_type}"

    @property
    def firmware_bin(self) -> Path:
        return self.build_dir / "firmware.bin"

    docker_image = "registry.gitlab.com/alelec/docker-esp32-toolchain:{ESPIDF_SUPHASH}"
    esp_idf_path = "/esp"
    build_script = BUILD_SCRIPTS / "esp32.sh"

    def build(self):
        docker_run(
            self.docker_image.format(ESPIDF_SUPHASH=extract_espidf_suphash()),
            self.build_script,
            env={
                "AMPY_BOARD_DIR": self.board_dir,
                "AMPY_BOARD": self.board_type,
                "AMPY_ESPIDF": self.esp_idf_path,
            },
        )

    def flash(self, firmware: Path):
        super().flash(firmware)
        call(*self.esptool_args, "write_flash", "--verify", "0x1000", firmware)


# Inject a more pretty __repr__()
setattr(
    MpyBoard,
    "__repr__",
    _create_fn(
        "__repr__",
        ("self",),
        [
            'return f"""{self.__class__.__qualname__}(\n    '
            + "\n    ".join(
                f"{f.name}={{self.{f.name}!r}}," for f in fields(MpyBoard) if f.repr
            )
            + '\n)"""'
        ],
    ),
)
