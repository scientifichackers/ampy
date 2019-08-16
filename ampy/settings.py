from pathlib import Path
from tempfile import gettempdir

from decouple import config
from esptool import ESPLoader

BAUD = config("AMPY_BAUD", ESPLoader.ESP_ROM_BAUD, cast=int)
TMPDIR = Path(gettempdir()) / "ampy"
try:
    TMPDIR.mkdir()
except FileExistsError:
    pass
