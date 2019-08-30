import os
from contextlib import redirect_stdout
from typing import Generator, List, NamedTuple

from esptool import ESPLoader, ESP8266ROM, ESP32ROM
from serial.tools import list_ports

from ampy import settings


class Board(NamedTuple):
    chip: str
    features: List[str]
    crystal_mhz: int
    mac: str
    port: str


def main() -> Generator[Board, None, None]:
    ser_list = [it.device for it in list_ports.comports()]
    ser_list.sort(reverse=True)

    for port in ser_list:
        try:
            esp = detect_chip(port)
        except StopIteration:
            pass
        else:
            yield Board(
                esp.get_chip_description(),
                esp.get_chip_features(),
                esp.get_crystal_freq(),
                ":".join(f"{it:02x}" for it in esp.read_mac()),
                port,
            )


class ConnectModes:
    default_reset = "default_reset"
    no_reset = "no_reset"
    no_reset_no_sync = "no_reset_no_sync"


CHIP_CLASSES = {
    ESP8266ROM.DATE_REG_VALUE: ESP8266ROM,
    ESP32ROM.DATE_REG_VALUE: ESP32ROM,
}


def detect_chip(port: str):
    loader = ESPLoader(port, settings.BAUD)
    with open(os.devnull, "w") as f, redirect_stdout(f):
        connect_attempt(loader, ConnectModes.default_reset)
    data_reg = loader.read_reg(ESPLoader.UART_DATA_REG_ADDR)
    return CHIP_CLASSES[data_reg](loader._port, loader._port.baudrate)


def connect_attempt(loader: ESPLoader, mode: str):
    for it in False, True:
        last_error = loader._connect_attempt(mode=mode, esp32r0_delay=it)
        if last_error is None:
            break


if __name__ == "__main__":
    for it in main():
        print(it)
