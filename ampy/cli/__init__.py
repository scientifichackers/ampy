import pkgutil

from .main import main, cli

__all__ = ['main', 'cli']

# import all commands files, so they can add themselves to the cli
for pkg in pkgutil.walk_packages(__path__):
    if pkg.name == '__main__':
        continue
    __import__(f'{__package__}.{pkg.name}')
