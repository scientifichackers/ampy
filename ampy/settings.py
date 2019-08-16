from pathlib import Path
from tempfile import gettempdir

from decouple import config
from esptool import ESPLoader

BAUD = config("AMPY_BAUD", ESPLoader.ESP_ROM_BAUD, cast=int)
TMP_DIR = Path(gettempdir()) / "ampy"
try:
    TMP_DIR.mkdir()
except FileExistsError:
    pass
