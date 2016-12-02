# Adafruit MicroPython Tool - Command Line Interface
# Author: Tony DiCola
# Copyright (c) 2016 Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from __future__ import print_function
import os

import click

import ampy.files as files
import ampy.pyboard as pyboard


_board = None


@click.group()
@click.option('--port', '-p', envvar='AMPY_PORT', required=True, type=click.STRING,
              help='Name of serial port for connected board.  Can optionally specify with AMPY_PORT environemnt variable.',
              metavar='PORT')
@click.option('--baud', '-b', envvar='AMPY_BAUD', default=115200, type=click.INT,
              help='Baud rate for the serial connection (default 115200).  Can optionally specify with AMPY_BAUD environment variable.',
              metavar='BAUD')
@click.version_option()
def cli(port, baud):
    """ampy - Adafruit MicroPython Tool

    Ampy is a tool to control MicroPython boards over a serial connection.  Using
    ampy you can manipulate files on the board's internal filesystem and even run
    scripts.
    """
    global _board
    _board = pyboard.Pyboard(port, baudrate=baud)

@cli.command()
@click.argument('remote_file')
@click.argument('local_file', type=click.File('wb'), required=False)
def get(remote_file, local_file):
    """
    Retrieve a file from the board.

    Get will download a file from the board and print its contents or save it
    locally.  You must pass at least one argument which is the path to the file
    to download from the board.  If you don't specify a second argument then
    the file contents will be printed to standard output.  However if you pass
    a file name as the second argument then the contents of the downloaded file
    will be saved to that file (overwriting anything inside it!).

    For example to retrieve the boot.py and print it out run:

      ampy --port /board/serial/port get boot.py

    Or to get main.py and save it as main.py locally run:

      ampy --port /board/serial/port get main.py main.py
    """
    # Get the file contents.
    board_files = files.Files(_board)
    contents = board_files.get(remote_file)
    # Print the file out if no local file was provided, otherwise save it.
    if local_file is None:
        print(contents.decode('utf-8'))
    else:
        local_file.write(contents)

@cli.command()
@click.argument('directory')
def mkdir(directory):
    """
    Create a directory on the board.

    Mkdir will create the specified directory on the board.  One argument is
    required, the full path of the directory to create.

    Note that you cannot recursively create a hierarchy of directories with one
    mkdir command, instead you must create each parent directory with separate
    mkdir command calls.

    For example to make a directory under the root called 'code':

      ampy --port /board/serial/port mkdir /code
    """
    # Run the mkdir command.
    board_files = files.Files(_board)
    board_files.mkdir(directory)

@cli.command()
@click.argument('directory', default='/')
def ls(directory):
    """List contents of a directory on the board.

    Can pass an optional argument which is the path to the directory.  The
    default is to list the contents of the root, /, path.

    For example to list the contents of the root run:

      ampy --port /board/serial/port ls

    Or to list the contents of the /foo/bar directory on the board run:

      ampy --port /board/serial/port ls /foo/bar
    """
    # List each file/directory on a separate line.
    board_files = files.Files(_board)
    for f in board_files.ls(directory):
        print(f)

@cli.command()
@click.argument('local_file', type=click.File('rb'))
@click.argument('remote_file', required=False)
def put(local_file, remote_file):
    """Put a file on the board.

    Put will upload a local file to the board.  If the file already exists on
    the board it will be overwritten with no warning!  You must pass at least
    one argument which is the path to the local file to upload.  You can pass
    a second optional argument which is the path and name of the file to put to
    on the connected board.

    For example to upload a main.py from the current directory to the board's
    root run:

      ampy --port /board/serial/port put main.py

    Or to upload a board_boot.py from a ./foo subdirectory and save it as boot.py
    in the board's root run:

      ampy --port /board/serial/port put ./foo/board_boot.py boot.py
    """
    # Use the local filename if no remote filename is provided.
    if remote_file is None:
        remote_file = os.path.basename(local_file.name)
    # Put the file on the board.
    board_files = files.Files(_board)
    board_files.put(remote_file, local_file.read())

@cli.command()
@click.argument('remote_file')
def rm(remote_file):
    """Remove a file from the board.

    Remove the specified file from the board's filesystem.  Must specify one
    argument which is the path to the file to delete.  Note that this can't
    delete directories which have files inside them, but can delete empty
    directories.

    For example to delete main.py from the root of a board run:

      ampy --port /board/serial/port rm main.py
    """
    # Delete the provided file/directory on the board.
    board_files = files.Files(_board)
    board_files.rm(remote_file)

@cli.command()
@click.argument('remote_dir')
def rmdir(remote_dir):
    """Remove a directory from the board.

    Remove the specified directory from the board's filesystem.  Must specify one
    argument which is the path to the directory to delete.  Note that this can't
    delete directories which have files inside them, but can delete empty
    directories.

    For example to delete /foo from the root of a board run:

      ampy --port /board/serial/port rmdir /foo
    """
    # Delete the provided directory on the board.
    board_files = files.Files(_board)
    board_files.rmdir(remote_dir)

@cli.command()
@click.argument('local_file')
@click.option('--no-output', '-n', is_flag=True,
              help="Run the code without waiting for it to finish and print output.  Use this when running code with main loops that never return.")
def run(local_file, no_output):
    """Run a script and print its output.

    Run will send the specified file to the board and execute it immediately.
    Any output from the board will be printed to the console (note that this is
    not a 'shell' and you can't send input to the program).

    Note that if your code has a main or infinite loop you should add the --no-output
    option.  This will run the script and immediately exit without waiting for
    the script to finish and print output.

    For example to run a test.py script and print any output after it finishes:

      ampy --port /board/serial/port run test.py

    Or to run test.py and not wait for it to finish:

      ampy --port /board/serial/port run --no-output test.py
    """
    # Run the provided file and print its output.
    board_files = files.Files(_board)
    output = board_files.run(local_file, not no_output)
    if output is not None:
        print(output.decode('utf-8'), end='')

@cli.command()
def reset():
    """Perform soft reset/reboot of the board.

    Will connect to the board and perform a soft reset.  No arguments are
    necessary:

      ampy --port /board/serial/port reset
    """
    # Enter then exit the raw REPL, in the process the board will be soft reset
    # (part of enter raw REPL).
    _board.enter_raw_repl()
    _board.exit_raw_repl()

if __name__ == '__main__':
    cli()
