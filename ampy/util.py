import os
import re
import shutil
import subprocess
from distutils.spawn import find_executable
from pathlib import Path

from click import style

from ampy.settings import MPY_REPO_URL, MPY_REPO_DIR

ESP32_MAKEFILE_PATH = MPY_REPO_DIR / "ports" / "esp32" / "Makefile"
ESPIDF_SUPHASH_REGEX = re.compile("(ESPIDF_SUPHASH)(\s+)(:=)(\s+)([A-z0-9]+)")
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


class CommandFinder:
    cache = {}

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


commands = CommandFinder()


def shell(cmd: str, *args, **kwargs):
    call(cmd, *args, **kwargs, shell=True)


def call(cmd: str, *args, read_stdout=False, silent=False, **kwargs):
    if not silent:
        print(style(f"$ {cmd} {' '.join(map(str, args))}", fg="yellow"))

    if kwargs.get("shell", False):
        arg = cmd
    else:
        arg = [commands[cmd], *args]

    if read_stdout:
        return subprocess.check_output(arg, encoding="utf-8", **kwargs)
    else:
        return subprocess.check_call(arg, **kwargs)


if __name__ == "__main__":
    print(update_mpy_repo())
    print(extract_espidf_suphash())
