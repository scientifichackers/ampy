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


def shell(cmd: str, *args, **kwargs):
    call(cmd, *args, **kwargs, shell=True)


def call(cmd: str, *args, **kwargs):
    if not kwargs.pop("silent", False):
        print("$", cmd, *args)

    if kwargs.get("shell", False):
        subprocess.check_call(cmd, **kwargs)
    else:
        subprocess.check_call([commands[cmd], *args], **kwargs)
