from pathlib import Path
from tempfile import gettempdir

TMP_DIR = Path(gettempdir()) / "ampy"
CACHE_DIR = Path.home() / ".cache" / "ampy"

MPY_REPO_URL = "https://github.com/micropython/micropython.git"
MPY_REPO_DIR = CACHE_DIR / "micropython"

DEV_MODULE = Path(__file__).parent.parent / "dev_upy"

for dir in TMP_DIR, CACHE_DIR:
    try:
        dir.mkdir()
    except FileExistsError:
        pass
