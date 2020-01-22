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
import platform
import posixpath
import re
import serial.serialutil

import click
import dotenv

# Load AMPY_PORT et al from .ampy file
# Performed here because we need to beat click's decorators.
config = dotenv.find_dotenv(filename=".ampy", usecwd=True)
if config:
    dotenv.load_dotenv(dotenv_path=config)

import ampy.files as files
import ampy.pyboard as pyboard


_board = None


def windows_full_port_name(portname):
    # Helper function to generate proper Windows COM port paths.  Apparently
    # Windows requires COM ports above 9 to have a special path, where ports below
    # 9 are just referred to by COM1, COM2, etc. (wacky!)  See this post for
    # more info and where this code came from:
    # http://eli.thegreenplace.net/2009/07/31/listing-all-serial-ports-on-windows-with-python/
    m = re.match("^COM(\d+)$", portname)
    if m and int(m.group(1)) < 10:
        return portname
    else:
        return "\\\\.\\{0}".format(portname)


@click.group()
@click.option(
    "--port",
    "-p",
    envvar="AMPY_PORT",
    required=True,
    type=click.STRING,
    help="Name of serial port for connected board.  Can optionally specify with AMPY_PORT environment variable.",
    metavar="PORT",
)
@click.option(
    "--baud",
    "-b",
    envvar="AMPY_BAUD",
    default=115200,
    type=click.INT,
    help="Baud rate for the serial connection (default 115200).  Can optionally specify with AMPY_BAUD environment variable.",
    metavar="BAUD",
)
@click.option(
    "--delay",
    "-d",
    envvar="AMPY_DELAY",
    default=0,
    type=click.FLOAT,
    help="Delay in seconds before entering RAW MODE (default 0). Can optionally specify with AMPY_DELAY environment variable.",
    metavar="DELAY",
)
@click.version_option()
def cli(port, baud, delay):
    """ampy - Adafruit MicroPython Tool

    Ampy is a tool to control MicroPython boards over a serial connection.  Using
    ampy you can manipulate files on the board's internal filesystem and even run
    scripts.
    """
    global _board
    # On Windows fix the COM port path name for ports above 9 (see comment in
    # windows_full_port_name function).
    if platform.system() == "Windows":
        port = windows_full_port_name(port)
    _board = pyboard.Pyboard(port, baudrate=baud, rawdelay=delay)


@cli.command()
@click.argument("remote_file")
@click.argument("local_file", type=click.File("wb"), required=False)
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
        print(contents.decode("utf-8"))
    else:
        local_file.write(contents)


@cli.command()
@click.option(
    "--exists-okay", is_flag=True, help="Ignore if the directory already exists."
)
@click.argument("directory")
def mkdir(directory, exists_okay):
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
    board_files.mkdir(directory, exists_okay=exists_okay)


@cli.command()
@click.argument("directory", default="/")
@click.option(
    "--long_format",
    "-l",
    is_flag=True,
    help="Print long format info including size of files.  Note the size of directories is not supported and will show 0 values.",
)
@click.option(
    "--recursive",
    "-r",
    is_flag=True,
    help="recursively list all files and (empty) directories.",
)
def ls(directory, long_format, recursive):
    """List contents of a directory on the board.

    Can pass an optional argument which is the path to the directory.  The
    default is to list the contents of the root, /, path.

    For example to list the contents of the root run:

      ampy --port /board/serial/port ls

    Or to list the contents of the /foo/bar directory on the board run:

      ampy --port /board/serial/port ls /foo/bar

    Add the -l or --long_format flag to print the size of files (however note
    MicroPython does not calculate the size of folders and will show 0 bytes):

      ampy --port /board/serial/port ls -l /foo/bar
    """
    # List each file/directory on a separate line.
    board_files = files.Files(_board)
    for f in board_files.ls(directory, long_format=long_format, recursive=recursive):
        print(f)


@cli.command()
@click.argument("local", type=click.Path(exists=True))
@click.argument("remote", required=False)
def put(local, remote):
    """Put a file or folder and its contents on the board.

    Put will upload a local file or folder  to the board.  If the file already
    exists on the board it will be overwritten with no warning!  You must pass
    at least one argument which is the path to the local file/folder to
    upload.  If the item to upload is a folder then it will be copied to the
    board recursively with its entire child structure.  You can pass a second
    optional argument which is the path and name of the file/folder to put to
    on the connected board.

    For example to upload a main.py from the current directory to the board's
    root run:

      ampy --port /board/serial/port put main.py

    Or to upload a board_boot.py from a ./foo subdirectory and save it as boot.py
    in the board's root run:

      ampy --port /board/serial/port put ./foo/board_boot.py boot.py

    To upload a local folder adafruit_library and all of its child files/folders
    as an item under the board's root run:

      ampy --port /board/serial/port put adafruit_library

    Or to put a local folder adafruit_library on the board under the path
    /lib/adafruit_library on the board run:

      ampy --port /board/serial/port put adafruit_library /lib/adafruit_library
    """
    # Use the local filename if no remote filename is provided.
    if remote is None:
        remote = os.path.basename(os.path.abspath(local))
    # Check if path is a folder and do recursive copy of everything inside it.
    # Otherwise it's a file and should simply be copied over.
    if os.path.isdir(local):
        # Directory copy, create the directory and walk all children to copy
        # over the files.
        board_files = files.Files(_board)
        for parent, child_dirs, child_files in os.walk(local, followlinks=True):
            # Create board filesystem absolute path to parent directory.
            remote_parent = posixpath.normpath(
                posixpath.join(remote, os.path.relpath(parent, local))
            )
            try:
                # Create remote parent directory.
                board_files.mkdir(remote_parent)
            except files.DirectoryExistsError:
                # Ignore errors for directories that already exist.
                pass
            # Loop through all the files and put them on the board too.
            for filename in child_files:
                with open(os.path.join(parent, filename), "rb") as infile:
                    remote_filename = posixpath.join(remote_parent, filename)
                    board_files.put(remote_filename, infile.read())


    else:
        # File copy, open the file and copy its contents to the board.
        # Put the file on the board.
        with open(local, "rb") as infile:
            board_files = files.Files(_board)
            board_files.put(remote, infile.read())


@cli.command()
@click.argument("remote_file")
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
@click.option(
    "--missing-okay", is_flag=True, help="Ignore if the directory does not exist."
)
@click.argument("remote_folder")
def rmdir(remote_folder, missing_okay):
    """Forcefully remove a folder and all its children from the board.

    Remove the specified folder from the board's filesystem.  Must specify one
    argument which is the path to the folder to delete.  This will delete the
    directory and ALL of its children recursively, use with caution!

    For example to delete everything under /adafruit_library from the root of a
    board run:

      ampy --port /board/serial/port rmdir adafruit_library
    """
    # Delete the provided file/directory on the board.
    board_files = files.Files(_board)
    board_files.rmdir(remote_folder, missing_okay=missing_okay)


@cli.command()
@click.argument("local_file")
@click.option(
    "--no-output",
    "-n",
    is_flag=True,
    help="Run the code without waiting for it to finish and print output.  Use this when running code with main loops that never return.",
)
def run(local_file, no_output):
    """Run a script and print its output.

    Run will send the specified file to the board and execute it immediately.
    Any output from the board will be printed to the console (note that this is
    not a 'shell' and you can't send input to the program).

    Note that if your code has a main or infinite loop you should add the --no-output
    option.  This will run the script and immediately exit without waiting for
    the script to finish and print output.

    For example to run a test.py script and print any output until it finishes:

      ampy --port /board/serial/port run test.py

    Or to run test.py and not wait for it to finish:

      ampy --port /board/serial/port run --no-output test.py
    """
    # Run the provided file and print its output.
    board_files = files.Files(_board)
    try:
        output = board_files.run(local_file, not no_output, not no_output)
        if output is not None:
            print(output.decode("utf-8"), end="")
    except IOError:
        click.echo(
            "Failed to find or read input file: {0}".format(local_file), err=True
        )


@cli.command()
@click.option(
    "--bootloader", "mode", flag_value="BOOTLOADER", help="Reboot into the bootloader"
)
@click.option(
    "--hard",
    "mode",
    flag_value="NORMAL",
    help="Perform a hard reboot, including running init.py",
)
@click.option(
    "--repl",
    "mode",
    flag_value="SOFT",
    default=True,
    help="Perform a soft reboot, entering the REPL  [default]",
)
@click.option(
    "--safe",
    "mode",
    flag_value="SAFE_MODE",
    help="Perform a safe-mode reboot.  User code will not be run and the filesystem will be writeable over USB",
)
def reset(mode):
    """Perform soft reset/reboot of the board.

    Will connect to the board and perform a reset.  Depending on the board
    and firmware, several different types of reset may be supported.

      ampy --port /board/serial/port reset
    """
    _board.enter_raw_repl()
    if mode == "SOFT":
        _board.exit_raw_repl()
        return

    _board.exec_(
        """if 1:
        def on_next_reset(x):
            try:
                import microcontroller
            except:
                if x == 'NORMAL': return ''
                return 'Reset mode only supported on CircuitPython'
            try:
                microcontroller.on_next_reset(getattr(microcontroller.RunMode, x))
            except ValueError as e:
                return str(e)
            return ''
        def reset():
            try:
                import microcontroller
            except:
                import machine as microcontroller
            microcontroller.reset()
    """
    )
    r = _board.eval("on_next_reset({})".format(repr(mode)))
    print("here we are", repr(r))
    if r:
        click.echo(r, err=True)
        return

    try:
        _board.exec_raw_no_follow("reset()")
    except serial.serialutil.SerialException as e:
        # An error is expected to occur, as the board should disconnect from
        # serial when restarted via microcontroller.reset()
        pass


if __name__ == "__main__":
    try:
        cli()
    finally:
        # Try to ensure the board serial connection is always gracefully closed.
        if _board is not None:
            try:
                _board.close()
            except:
                # Swallow errors when attempting to close as it's just a best effort
                # and shouldn't cause a new error or problem if the connection can't
                # be closed.
                pass
