import shlex
import subprocess
from distutils.spawn import find_executable


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


def call(cmd: str, *args):
    print("$", cmd, *args)
    subprocess.run([commands[cmd], *args])
