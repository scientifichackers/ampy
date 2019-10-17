import os
from contextlib import redirect_stdout
from typing import Generator, Iterable

from esptool import ESPLoader, ESP8266ROM, ESP32ROM, DETECTED_FLASH_SIZES
from serial import SerialException
from serial.tools import list_ports as _list_ports

from ampy.core.mpy_boards import MpyBoard, ESP8266Board, ESP32Board

CHIP_CLASSES = {
    ESP8266ROM.DATE_REG_VALUE: (ESP8266ROM, ESP8266Board),
    ESP32ROM.DATE_REG_VALUE: (ESP32ROM, ESP32Board),
}


def main(baud: int) -> Generator[MpyBoard, None, None]:
    for port in list_ports():
        try:
            yield detect_board(port, baud)
        except SerialException:
            pass
        except StopIteration:
            pass


def list_ports() -> Iterable[str]:
    return (
        it.device for it in _list_ports.comports() if "BLUE" not in it.device.upper()
    )


def detect_board(port: str, baud: int) -> MpyBoard:
    loader = ESPLoader(port, baud)
    try:
        connect_attempt(loader)
        data_reg = loader.read_reg(ESPLoader.UART_DATA_REG_ADDR)
        rom_cls, board_cls = CHIP_CLASSES[data_reg]
        esp_rom = rom_cls(loader._port, loader._port.baudrate)
        try:
            return board_cls(
                chip=esp_rom.CHIP_NAME,
                description=esp_rom.get_chip_description(),
                features=esp_rom.get_chip_features(),
                crystal_mhz=esp_rom.get_crystal_freq(),
                flash_size=detect_flash_size(esp_rom),
                mac=":".join(f"{it:02x}" for it in esp_rom.read_mac()),
                port=port,
                baud=baud,
                board_type="GENERIC",
            )
        finally:
            esp_rom.soft_reset(False)
    finally:
        loader._port.close()


def detect_flash_size(esp: ESPLoader):
    with open(os.devnull, "w") as f, redirect_stdout(f):
        esp.flash_spi_attach(0)
    return DETECTED_FLASH_SIZES.get(esp.run_spiflash_command(0x9F, b"", 24) >> 16)


def connect_attempt(loader: ESPLoader):
    for it in False, True:
        with open(os.devnull, "w") as f, redirect_stdout(f):
            if loader._connect_attempt(mode="default_reset", esp32r0_delay=it) is None:
                return
