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
import io
import posixpath
import re
import serial.serialutil
from time import sleep

import subprocess

import click
import dotenv
import ampy.progress_bar as progress_bar


# Load AMPY_PORT et al from .ampy file
# Performed here because we need to beat click's decorators.
config = dotenv.find_dotenv(filename=".ampy", usecwd=True)
if config:
    dotenv.load_dotenv(dotenv_path=config)

import ampy.files as files
import ampy.pyboard as pyboard


# On Windows fix the COM port path name for ports above 9 (see comment in
# windows_full_port_name function).
_board = None
port = "/dev/ttyACM0"
baud = 115200
delay = 0
history = []
pico_wd = '/'
pc_wd = os.getcwd()
queued_cmd = None
cmd = None
os.chdir(os.path.expanduser('~'))


if platform.system() == "Windows":
    port = windows_full_port_name(port)
    
def init_board(port, baud, delay):
    try:
        return pyboard.Pyboard(port, baudrate=baud, rawdelay=delay), None
    except pyboard.PyboardError as e:
        return None, e
 
def get_port():
    try:
        return input("\nEnter port address >> ")
    except KeyboardInterrupt:
        return get_port()


def init_board_interactively():
    global _board
    global port
    global baud
    global delay
    do_sleep = False
    _board = None
    while _board is None:
        
        try:
            if do_sleep:
                sleep(1.5)
                do_sleep = False
            else:
                _board  = pyboard.Pyboard(port, baudrate=baud, rawdelay=delay) 
        except pyboard.PyboardError as e:
            print(f"Error: {e}. Ctrl+C to change port. Ctrl+C, Ctrl+D to exit.")
            do_sleep = True
        except KeyboardInterrupt:
            try:
                port = get_port()
            except EOFError:
                exit("\nTerminating program...\n")
            


def windows_full_port_name(portname):
    # Helper function to generate proper Windows COM port paths.  Apparently
    # Windows requires COM ports above 9 to have a special path, where ports below
    # 9 are just referred to by COM1, COM2, etc. (wacky!)  See this post for
    # more info and where this code came from:
    # http://eli.thegreenplace.net/2009/07/31/listing-all-serial-ports-on-windows-with-python/
    m = re.match(r"^COM(\d+)$", portname)
    if m and int(m.group(1)) < 10:
        return portname
    else:
        return "\\\\.\\{0}".format(portname)


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
        return contents.decode("utf-8")
    else:
        local_file.write(contents)

def mkdir(directory, exists_okay, make_parents):
    """
    Create a directory on the board.

    Mkdir will create the specified directory on the board.  One argument is
    required, the full path of the directory to create.

    By default you cannot recursively create a hierarchy of directories with one
    mkdir command. You may create each parent directory with separate
    mkdir command calls, or use the --make-parents option.
    
    For example to make a directory under the root called 'code':

      ampy --port /board/serial/port mkdir /code
      
    To make a directory under the root called 'code/for/ampy', along with all
    missing parents:

      ampy --port /board/serial/port mkdir --make-parents /code/for/ampy
    """ # Run the mkdir command.
    board_files = files.Files(_board)
    if make_parents:
        if directory[0] != '/':
            directory = "/" + directory
        dirpath = ""
        for dir in directory.split("/")[1:-1]:
            dirpath += "/" + dir
            board_files.mkdir(dirpath, exists_okay=True)
    board_files.mkdir(directory, exists_okay=exists_okay)

def ls(directory):
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
    dlist = []
    for f in board_files.lsi(directory):
        d = f[0].split('/')[-1] # file or dir name
        if f[1] == 0x4000: # a directory
            dlist.insert(0, "+ " + d)
        else:
            dlist.append("- " + d)
    return dlist

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
        # Create progress bar for each file
        pb_bath =  progress_bar.ProgressBarBath('Overall progress')
        for parent, child_dirs, child_files in os.walk(local, followlinks=True):
            for filename in child_files:
                path = os.path.join(parent, filename)
                size = os.stat(path).st_size
                pb_bath.add_subjob(progress_bar.ProgressBar(name=path, total=size))

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
                local_path = os.path.join(parent, filename)
                with open(local_path, "rb") as infile:
                    remote_filename = posixpath.join(remote_parent, filename)
                    data = infile.read()
                    job = pb_bath.get_subjob(local_path)
                    callback = job.on_progress_done
                    board_files.put(remote_filename, data, callback)
    else:
        # File copy, open the file and copy its contents to the board.
        # Put the file on the board.
        with open(local, "rb") as infile:
            data = infile.read()
            progress = progress_bar.ProgressBar(name=local, total=len(data))
            board_files = files.Files(_board)
            board_files.put(remote, data, progress.on_progress_done)
    print('')

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

def rmdir(remote_folder, missing_okay):
    """Forcefully remove a folder and all its children from the board.

    Remove the specified folder from the board's filesystem.  Must specify one
    argument which is the path to the folder to delete.  This will delete the
    directory and ALL of its children recursively, use with caution!

    If missing_okay: ignore if directory does not exist

    For example to delete everything under /adafruit_library from the root of a
    board run:

      ampy --port /board/serial/port rmdir adafruit_library
    """
    # Delete the provided file/directory on the board.
    board_files = files.Files(_board)
    board_files.rmdir(remote_folder, missing_okay=missing_okay)

def run(file, no_output):
    """Run a script and print its output.
    
    no_output: suppress output for scripts with infinite loops or no output

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
        output = None
        if type(file) == str:
            output = board_files.run(file, not no_output, not no_output)
        elif type(file) == io.BytesIO:
            output = board_files.run_file(file, not no_output, not no_output)
        if output is not None:
            print(output.decode("utf-8"), end="")
    except IOError:
        print("Failed to find or read input file: {0}".format(file))

def run_remote(remote_file, no_output):
    '''Takes an io.BytesIO object as a dummy file'''
    board_files = files.Files(_board)
    try:
        output = board_files.run_file(remote_file, not no_output, not no_output)
        if output is not None:
            print(output.decode("utf-8"), end="")
    except IOError:
        click.echo(
            "Failed to find or read input file: {0}".format(remote_file), err=True
        )

def reset(mode):
    """Perform soft reset/reboot of the board.

    Will connect to the board and perform a reset.  Depending on the board
    and firmware, several different types of reset may be supported.

      ampy --port /board/serial/port reset

    modes: SAFE_MODE, SOFT (to REPL), NORMAL (runs init.py), BOOTLOADER
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

def parse_dir(my_d: str):
    d = my_d
    if d == '..':
        d = pico_wd.split('/')[:-2]
        d = '/'.join(d) if len(d) > 1 else '/'
    elif d[:3] == '../':
        root = pico_wd.split('/')[:-2]
        root = '/'.join(root) if len(root) > 1 else ''
        d = root + d[2:]
    elif d[0] != '/':
        d = pico_wd + d

    d = os.path.normpath(d)
    if '~' in d:
        raise FileNotFoundError("Remote device has no home directory.")
    return d
def base_dir(my_d: str):
    d = parse_dir(my_d)
    # /some/dir/ or /some/dir/file
    # we want same in first case, dir in second
    print(f"last char is {my_d[-1]}")
    if my_d[-1] == '/':
        return d

    d_split = d.split('/')
    print(f"in base_dir: d_split is {d_split}")
    if len(d_split) < 2:
        raise ValueError("Tried to parse an empty string.")
    elif d_split[0] != '':
        raise ValueError("Tried to parse a relative directory.")
    elif len(d_split) == 2:
        return '/'
    else:
        return '/' + '/'.join(d_split[1:-1]) + '/'
    
def get_last_dir_component(my_d: str):
    last = os.path.split(my_d)[1]
    if last != '':
        return last
    else:
        spl = '/'.split(my_d)
        spl.reverse()
        for i in spl:
            if i != '':
                return i
    raise ValueError(f"Couldn't parse directory: {my_d}")
    
def get_help(command):
# get[!], port, put[!], mkdir, ls, cd, pwd, cdl, lsl[a], repl, run, runl, rs, !
    compendium = {
            "get": ["get device_file [new_name]",
                    "Download a file from your MicroPython device. Optionally, give it a new_name. Will not overwrite existing files."],
            "get!": ["get! device_file [new_name]",
                     "Download a file from your MicroPython device. Optionally, give it a new_name. NOTE: WILL overwrite existing files."],
            "port": ["port [new_port_name]",
                     "If called without parameters, prints port name. Otherwise, tries to set port to new_port_name."],
            "put": ["put local_file [new_name]",
                    "Uploads a file from your computer to your MicroPython device."],
            "put!": ["put! local_file [new_name]",
                     "Uploads a file from your computer to your MicroPython device, overwriting if necessary."],
            "mkdir": ["mkdir dir_name [dir_name2 ...]",
                      "Makes one or more directories, using relative or absolute paths."],
            "ls": ["ls [dir_name]",
                   "Lists the contents of the current working directory on your MicroPython device, or of the specified directory."],
            "cd": ["cd [dir_name]",
                   "Changes working directory on your MicroPython device."],
            "pwd": ["pwd",
                    "Prints the working directories on your MicroPython device and local computer."],
            "cdl": ["cdl [dir_name]",
                    "Changes working directory on your local computer."],
            "lsl": ["lsl [dir_name]",
                    "Lists the contents of your local computer's current working directory or of the specified directory. Does not show dotfiles. Mnemonic: ls local."],
            "lsla": ["lsla [dir_name]",
                     "Lists the contents of your local working directory or a specified directory. showing any dotfiles as well."],
            "repl": ["repl",
                     "Invokes tio to provide access to your MicroPython device's REPL."],
            "run": ["run [-q] file",
                    "Runs a script located on your MicroPython device, prints any output, and waits for the script to finish executing. Use -q (mnemonic: quiet) to silence output and proceed without waiting for the script to finish."],
            "runl": ["runl [-q] file",
                     "Same as run, but looks for the file on your local computer instead."],
            "rs": ["rs",
                   "Soft-resets the device as if you sent Ctrl+D through its REPL."],
            "docs-fs": ["",
                     "Notes on filesystem navigation:\nWhenever possible this program emulates filesystem navigation within bash, for familiarity. A filepath beginning with `/` is read as an absolute path starting from the root of the filesystem. Two dots `..` will indicate the directory above your current directory. When a path is for your local computer, a path can begin with a tilde `~` to indicate your home directory. To indicate a file should be copied into the directory foo, you should write `foo/`. To indicate a file should try to overwrite foo, write `foo`. A directory that does not begin with `/` is read as relative to the current working directory."], 
            "help": ["help [entry]",
                     "Prints a help message pertaining to entry, or a list of available commands and documentation if no entry is specified."],
            "!": ["",
                  "The bang command accesses command history much like in bash:\n- A single bang brings up a recent command history.\n- Bang and a number re-enters the corresponding command from the recent history (i.e. `!3`)\n- Bang-bang (i.e. `!!`) re-enters the most recent command.\n- Bang and a non-number query re-enters the first command that starts with that query. If you just entered the command `ls /foo/bar/baz`, you could use `!ls /f` to match that command.\n\nThe log only shows 10 recent commands at most, but it saves every command you enter (although history is not saved between sessions)."]
            } 
    if command in compendium.keys():
        usage, doc = compendium[command]

        print(f"HELP ENTRY: {command}")
        print()
        print('    ' + doc)
        if len(usage) > 0:
            print()
            print("USAGE:")
            print("    " + usage)
    else:
        print("Available help entries:")
        i = 0
        line = '    '
        for k in sorted(compendium.keys()):
            line += k
            if i % 5 == 4:
                print(line)
                line = '    '
            else:
                line += ', '
            i += 1
        

def cli_interactive():
    global pico_wd
    global queued_cmd
    global port
    global _board
    init_board_interactively()
    print("Welcome to Ampy! Type `help` or enter a command to get started!")
    # TODO add descriptive messages for output of cd, for ls an empty folder, etc
    while True:
        if queued_cmd is None:
            print()
        try:
            block_history = False
            if pico_wd[-1] != '/':
                pico_wd = pico_wd + '/'

            if queued_cmd is None:
                query = input(f"MCU:{port}{pico_wd}\nPC:{os.getcwd()}\n >>> ")
                print()
                tokens = query.split(" ")
                command = tokens[0]
                params = tokens[1:]
            else:
                block_history = True
                command = queued_cmd[0]
                params = queued_cmd[1:]
                queued_cmd = None
            if command == "get" or command == "get!":
                remote, local = None, None
                if len(params) == 2:
                    remote, local = params[0], params[1]
                elif len(params) == 1:
                    remote = local = params[0]
                else:
                    print("malformed command")
                    # TODO implement help message
                try:
                    flags = 'xb'
                    if command == "get!":
                        flags = 'wb'
                    with open(local, flags) as f:
                        get(remote, f)
                except RuntimeError as e:
                    print(e)
                except FileExistsError:
                    print("Local file already exists. Use get! to overwrite.")
            elif command == "help":
                if len(params) == 1:
                    get_help(params[0])
                else:
                    get_help(None)
            elif command == "port":
                if len(params) == 0:
                    print(f"Device port is:\n    {port}")
                elif len(params) == 1:
                    old_board = _board
                    old_port = port
                    _board = None
                    try:
                        while _board is None:
                            _board, err = init_board(params[0], baud, delay)
                            if _board is None:
                                print(f"Error: {err}. Ctrl+C to cancel polling.")
                                print()
                                sleep(1)
                        port = params[0]
                        print(f"Device port changed to:\n    {port}")
                    except KeyboardInterrupt:
                        _board = old_board
                        port = old_port
                        print("Cancelled. Device port unchanged.")
                else:
                    print("Malformed command") # TODO help
            elif command in ["put", "put!"]:
                local, remote = None, None
                if len(params) == 2:
                    local, remote = params[0], params[1]
                    tail = '/' if remote[-1] == '/' else ''

                    remote = parse_dir(remote) + tail
                    if remote[-1] == '/':
                        remote = remote + get_last_dir_component(local)
                        remote = os.path.normpath(remote)
                        if remote.startswith('//'):
                            remote = remote[1:]
                    print(f"remote: {remote}")
                elif len(params) == 1:
                    local = params[0]
                    # strip trailing / if it's a folder path
                    local_stripped = local[:-1] if local[-1] == '/' else local
                    spl = local.split('/')
                    remote = spl[-1] # should be a dir or file name
                    remote = parse_dir(remote) # remote path now relative to pico_wd

                reference_dir = pico_wd
                if len(params) == 2:
                    r = params[1]
                    reference_dir = '/'.join(remote.split('/')[:-1]) + '/'
                    print(f"ref dir: {reference_dir}")

                file_exists = False
                file_is_dir = False
                for f in ls(reference_dir):
                    if f[0] == '+':
                        file_is_dir = True
                    else:
                        file_is_dir = False
                        print(f[0])
                    f = reference_dir + f[2:]
                    print(f"if {f} == {remote} then file exists")
                    if f == remote: 
                        file_exists = True
                        break

                try:
                    if local is not None and file_exists == False \
                            or command == "put!" and file_is_dir == False:
                        if remote[-1] == '/':
                            remote = remote + local
                            remote = os.path.normpath(remote)
                        put(os.path.abspath(local), remote)
                    else:
                        if local is None:
                            print("No file specified!") #TODO
                        elif file_exists and file_is_dir:
                            print(f"ERROR: {remote} is a directory. Use rmdir to delete it or choose a different name.")
                        else:
                            print("File exists on device. Use put! to overwrite.")
                except RuntimeError as e:
                    print(e)
                except pyboard.PyboardError as e:
                    if "EISDIR" in str(e):
                        print("A directory by that name exists on the MicroPython device.")
                except FileNotFoundError as e:
                    print(e)
            elif command == "mkdir":
                if len(params) > 0:
                    for d in params:
                        try:
                            mkdir(parse_dir(d), False, True)
                        except files.DirectoryExistsError:
                            print(f"Directory already exists: {d}")
                else:
                    print("malformed command")
                    # TODO help message
            elif command == "ls":
                # TODO: handle malformed commands
                d = None
                if len(params) == 1:
                    d = parse_dir(params[0])
                elif len(params) == 0:
                    d = pico_wd
                if d[0] != '/':
                    d = pico_wd + d
                print(d)
                if d is not None:
                    try:
                        dir_l = ls(d)
                        if len(dir_l) > 0:
                            for f in dir_l:
                                print(f)
                        else:
                            print("Directory empty.")
                    except RuntimeError as e:
                        print(e)
            elif command == "cd":
                if len(params) == 0:
                    pico_wd = '/'
                    queued_cmd = ["ls"]
                    #TODO use parse_dir
                elif len(params) == 1:
                    d = parse_dir(params[0])
                    try:
                        x = ls(d)
                        pico_wd = d
                        queued_cmd = ["ls"]
                    except RuntimeError as e:
                        print(e)
                        
                else:
                    print("Malformed command")
            elif command == "pwd":
                print(f"PC:\n    {os.getcwd()}")
                print(f"{port}:\n    {pico_wd}")
            elif command == "cdl":
                d = None
                if len(params) == 1:
                    d = params[0]
                elif len(params) == 0:
                    d = os.path.expanduser('~')

                try:
                    d = os.path.normpath(d)
                    d = os.path.expanduser(d)
                    d = os.path.expandvars(d)
                    os.chdir(d)
                    queued_cmd = ["lsl"]
                except FileNotFoundError as e:
                    print(e)
            elif command in ['lsl', 'lsla']:
                d = None
                d_list = []
                if len(params) == 1:
                    d = params[0]
                    if d[0] == "~":
                        d = os.path.expanduser(d)
                    if os.path.isdir(d):
                        for f in os.listdir(d):
                            if f[0] == '.' and command != 'lsla':
                                continue
                            elif os.path.isdir(os.path.normpath(d + '/' + f)):
                                d_list.insert(0, "+ " + f)
                            else:
                                d_list.append("- " + f)
                elif len(params) == 0:
                        d = os.getcwd()
                        for f in os.listdir():
                            if f[0] == '.' and command != 'lsla':
                                continue
                            elif os.path.isdir(os.path.normpath(d + '/' + f)):
                                d_list.insert(0, "+ " + f)
                            else:
                                d_list.append("- " + f)
                if d is None:
                    print("malformed command.") # TODO
                elif len(d_list) == 0:
                    print(f"{d}:")
                    print("    <Directory is empty.>")
                else:
                    print(f"{d}:")
                    for f in d_list:
                        print("    " + f)
            elif command == "repl":
                print("Connecting interactively to device. (Requires tio)")
                try:
                    result = subprocess.run(["tio", port],
                                            check=True,
                                            stderr=subprocess.PIPE)
                    print("Exiting REPL mode... ")
                except FileNotFoundError:
                    print("Couldn't find tio. Is it in your PATH?")
            elif command == "run":
                # Runs a script on the device
                if len(params) == 1 or len(params) == 2 and params[0] == '-q':
                    try:
                        silent = False
                        script_i = 0
                        if params[0] == "q":
                            silent = True
                            script_i = 1
                        p = parse_dir(params[script_i])
                        f = get(p, None)
                        fake_file = io.BytesIO(bytes(f, encoding='utf-8'))
                        run(fake_file, silent)
                    except RuntimeError as e:
                        print(e)
                    except pyboard.PyboardError as e:
                        print("Exception raised from MicroPython device:")
                        print()
                        print(e)
                else:
                    print("malformed command.") # TODO
            elif command == "runl":
                # Runs a script <l>ocally, on computer
                if len(params) == 1 or len(params) == 2 and params[0] == '-q':
                    try:
                        silent = False
                        script_i = 0
                        if params[0] == "q":
                            silent = True
                            script_i = 1
                        run(params[script_i], silent)
                    except RuntimeError as e:
                        print(e)
                    except pyboard.PyboardError as e:
                        print("Exception raised from MicroPython device:")
                        print()
                        print(e)
                else:
                    print("malformed command.") # TODO
            elif command in ['rs', 'reset', 'rst']:

                if len(params) == 0:
                    reset("SOFT")
                else:
                    print("malformed command") # TODO
            elif command.startswith('!'):
                block_history = True
                if command == '!':
                    blurb = history[-10:]
                    l = len(blurb)
                    if l > 0:
                        for t in blurb:
                            print(f"{l}: {" ".join(t)}")
                            l -= 1
                else:
                    h_param = command[1:] 
                    if len(params) > 0:
                        h_param += " " + " ".join(params)
                    if h_param.isdigit():
                        i = int(h_param) * -1
                        try:
                            queued_cmd = history[i]
                        except IndexError:
                            if len(history) > 0:
                                print(f"!{h_param} is invalid. Max is !{len(history)}.")
                            else:
                                print("History log is empty.")
                    elif h_param == '!':
                        if len(history) > 0:
                            queued_cmd = history[-1]
                        else:
                            print("History log is empty.")
                    else:
                        h_reversed = history[:]
                        h_reversed.reverse()
                        for t in h_reversed:
                            match = " ".join(t)
                            if match.startswith(h_param):
                                queued_cmd = t
                                break



            elif command in ['rmdir', 'rmdir!']:
                d_list = params
                if len(params) == 1 and params[0] == '*':
                    d_list = [d[2:] for d in ls(pico_wd) if d[0] == '+']

                print(f"Marked for deletion: {', '.join(d_list)}")

                if command == 'rmdir!' and len(d_list) > 0:
                    for d in d_list:
                        d = parse_dir(d)
                        try:
                            rmdir(d, False)
                        except RuntimeError as e:
                            print(e)

                elif command == 'rmdir' and len(d_list) > 0:
                    try:
                        for d in d_list:
                            d = parse_dir(d)
                            print(f"Delete the directory {d} and everything in it?")
                            confirm = input("(y/N) >> ")
                            if confirm in ["y", "yes"]:
                                try:
                                    rmdir(d, False)
                                except RuntimeError as e:
                                    print(e)
                    except KeyboardInterrupt:
                        print("\nCancelling operation!\n")
                elif len(params) == 0:
                    print("Malformed command") # TODO
            elif command in ['rm', 'rm!']:
                d_list = params
                if len(params) == 1 and params[0] == '*':
                    d_list = [d[2:] for d in ls(pico_wd) if d[0] == '-']
                
                if len(d_list) > 0:
                    print(f"Marked for deletion: {', '.join(d_list)}")
                else:
                    print("Directory is empty of files.")

                if command == 'rm!' and len(d_list) > 0:
                    for d in d_list:
                        d = parse_dir(d)
                        try:
                            rm(d)
                        except RuntimeError as e:
                            print(f"No such file, or file is non-empty directory: {d}")

                elif command == 'rm' and len(d_list) > 0:
                    try:
                        for d in d_list:
                            d = parse_dir(d)
                            print(f"Delete {d}?")
                            confirm = input("(y/N) >> ")
                            if confirm in ["y", "yes"]:
                                try:
                                    rm(d)
                                except RuntimeError as e:
                                    print(f"No such file, or file is non-empty directory: {d}")
                    except KeyboardInterrupt:
                        print("\nCancelling operation!\n")
                elif len(params) == 0:
                    print("Malformed command.") # TODO

            if block_history == False:
                history.append(tokens)

        except KeyboardInterrupt:
            print("\n")
            continue
        except EOFError:
            exit("\nTerminating program...")
        except serial.serialutil.SerialException:
            init_board_interactively()

    # Try to ensure the board serial connection is always gracefully closed.
    if _board is not None:
        try:
            _board.close()
        except:
            # Swallow errors when attempting to close as it's just a best effort
            # and shouldn't cause a new error or problem if the connection can't
            # be closed.
            pass
    
if __name__ == "__main__":
    cli_interactive()

