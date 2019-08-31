import os
from contextlib import redirect_stdout
from typing import Generator

from esptool import ESPLoader, ESP8266ROM, ESP32ROM, DETECTED_FLASH_SIZES
from serial.tools import list_ports

from ampy import settings
from ampy.mpy_boards import MpyBoard, ESP8266Board, ESP32Board


def main() -> Generator[MpyBoard, None, None]:
    ports = [it.device for it in list_ports.comports()]
    ports.sort(reverse=True)
    for port in ports:
        try:
            yield detect_board(port)
        except StopIteration:
            pass


class ConnectModes:
    default_reset = "default_reset"
    no_reset = "no_reset"
    no_reset_no_sync = "no_reset_no_sync"


CHIP_CLASSES = {
    ESP8266ROM.DATE_REG_VALUE: (ESP8266ROM, ESP8266Board),
    ESP32ROM.DATE_REG_VALUE: (ESP32ROM, ESP32Board),
}


def detect_board(port: str) -> MpyBoard:
    loader = ESPLoader(port, settings.BAUD)
    try:
        with open(os.devnull, "w") as f, redirect_stdout(f):
            connect_attempt(loader, ConnectModes.default_reset)

        data_reg = loader.read_reg(ESPLoader.UART_DATA_REG_ADDR)
        rom_cls, board_cls = CHIP_CLASSES[data_reg]
        esp = rom_cls(loader._port, loader._port.baudrate)
        try:
            return board_cls(
                chip=esp.CHIP_NAME,
                description=esp.get_chip_description(),
                # flash_size=detect_flash_size(esp),
                flash_size='x',
                features=esp.get_chip_features(),
                crystal_mhz=esp.get_crystal_freq(),
                mac=":".join(f"{it:02x}" for it in esp.read_mac()),
                port=port,
                board_type="GENERIC",
            )
        finally:
            esp.hard_reset()
    finally:
        loader._port.close()


def detect_flash_size(esp: ESPLoader):
    with open(os.devnull, "w") as f, redirect_stdout(f):
        esp.flash_spi_attach(0)
    return DETECTED_FLASH_SIZES.get(esp.run_spiflash_command(0x9F, b"", 24) >> 16)


def connect_attempt(loader: ESPLoader, mode: str):
    for it in False, True:
        last_error = loader._connect_attempt(mode=mode, esp32r0_delay=it)
        if last_error is None:
            break


if __name__ == "__main__":
    for it in main():
        print(it)
