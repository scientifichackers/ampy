import os
import re
import shutil
import subprocess
from contextlib import contextmanager
from distutils.spawn import find_executable
from pathlib import Path
from typing import Dict, List, Union, Tuple, Iterable

from click import style

from ampy.core.settings import MPY_REPO_DIR

MPY_REPO_URL = "https://github.com/micropython/micropython.git"
ESP32_MAKEFILE_PATH = MPY_REPO_DIR / "ports" / "esp32" / "Makefile"
ESPIDF_SUPHASH_REGEX = re.compile(
    r"(ESPIDF_SUPHASH_V4|ESPIDF_SUPHASH)(\s+)(:=)(\s+)([A-z0-9]+)"
)
DOCKER_HOME = "/root"


def update_mpy_repo(version: str = "master") -> str:
    if not MPY_REPO_DIR.exists():
        call("git", "clone", MPY_REPO_URL, MPY_REPO_DIR)
    os.chdir(MPY_REPO_DIR)

    call("git", "fetch")
    call("git", "checkout", version)
    call("git", "pull")
    call("git", "submodule", "update", "--init", "--recursive")

    return version


def clean_mpy_repo():
    print(f"Deleting {MPY_REPO_DIR}...")
    shutil.rmtree(MPY_REPO_DIR, ignore_errors=True)


def extract_espidf_suphash() -> str:
    return ESPIDF_SUPHASH_REGEX.findall(ESP32_MAKEFILE_PATH.read_text())[0][-1]


def docker_run(image: str, script: Path, *, mount: Path = MPY_REPO_DIR, env=None):
    if env is None:
        env = {}
    env_arg = " ".join(f"-e {i}={j}" for i, j in env.items())
    shell(
        f"docker run {env_arg} -v {mount}:{mount} -v {script}:{script} -w {mount} {image} {script}"
    )


class ExecutableStore:
    cache: Dict[str, Path] = {}

    def __getitem__(self, item):
        try:
            path = self.cache[item]
        except KeyError:
            path = self._find_executable(item)
        if path is None:
            print(f"Please install '{item}' on your machine to use this feature!")
            exit(1)
        return path

    def _find_executable(self, item):
        path = find_executable(item)
        self.cache[item] = path
        return path


executables = ExecutableStore()


def shell(cmd: str, *args, **kwargs):
    call(cmd, *args, **kwargs, shell=True)


def call(cmd: str, *args, read_stdout=False, **kwargs):
    print(style(f"$ {cmd} {' '.join(map(str, args))}", fg="yellow"))

    arg: Union[List[str], str]
    if kwargs.get("shell", False):
        arg = cmd
    else:
        arg = [executables[cmd], *args]

    if read_stdout:
        return subprocess.check_output(arg, encoding="utf-8", **kwargs)
    else:
        return subprocess.check_call(arg, **kwargs)


@contextmanager
def clean_copy(*to_copy: Tuple[Path, Path]):
    dest_paths = [it[1] for it in to_copy]
    rm_r(dest_paths)
    try:
        for src, dest in to_copy:
            print(f"Copying '{src}' -> '{dest}'...")
            try:
                shutil.copy(src, dest)
            except IsADirectoryError:
                shutil.copytree(src, dest)
        yield
    finally:
        rm_r(dest_paths)


def rm_r(paths: Iterable[Path]):
    for path in paths:
        print(f"Deleting '{path}'...")
        try:
            shutil.rmtree(path)
        except FileNotFoundError:
            pass
        except NotADirectoryError:
            path.unlink()


if __name__ == "__main__":
    print(update_mpy_repo())
    print(extract_espidf_suphash())
