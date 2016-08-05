# Adafruit MicroPython Tool - Command Line Interface
# Author: Tony DiCola
import os

import click

import ampy.files as files
import ampy.pyboard as pyboard


_board = None


@click.group()
@click.option('--port', '-p', envvar='MPY_PORT', required=True, type=click.STRING,
              help='Name of serial port for connected board.',
              metavar='PORT')
@click.option('--baud', '-b', envvar='MPY_BAUD', default=115200, type=click.INT,
              help='Baud rate for the serial connection. (default 115200)',
              metavar='BAUD')
def cli(port, baud):
    global _board
    _board = pyboard.Pyboard(port, baudrate=baud)

@cli.command()
@click.argument('directory', default='/')
def ls(directory):
    # List each file/directory on a separate line.
    board_files = files.Files(_board)
    for f in board_files.ls(directory):
        print(f)

@cli.command()
@click.argument('remote_file')
@click.argument('local_file', type=click.File('wb'), required=False)
def get(remote_file, local_file):
    # Get the file contents.
    board_files = files.Files(_board)
    contents = board_files.get(remote_file)
    # Print the file out if no local file was provided, otherwise save it.
    if local_file is None:
        print(contents.decode('utf-8'))
    else:
        local_file.write(contents)

@cli.command()
@click.argument('local_file', type=click.File('rb'))
@click.argument('remote_file', required=False)
def put(local_file, remote_file):
    # Use the local filename if no remote filename is provided.
    if remote_file is None:
        remote_file = os.path.basename(local_file.name)
    # Put the file on the board.
    board_files = files.Files(_board)
    board_files.put(remote_file, local_file.read())

@cli.command()
@click.argument('remote_file')
def rm(remote_file):
    # Delete the provided file/directory on the board.
    board_files = files.Files(_board)
    board_files.rm(remote_file)


if __name__ == '__main__':
    cli()
