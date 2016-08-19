# Adafruit MicroPython Tool - File Operations
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
import ast
import textwrap

from ampy.pyboard import PyboardError


BUFFER_SIZE = 32  # Amount of data to read or write to the serial port at a time.
                  # This is kept small because small chips and USB to serial
                  # bridges usually have very small buffers.


class Files(object):
    """Class to interact with a MicroPython board files over a serial connection.
    Provides functions for listing, uploading, and downloading files from the
    board's filesystem.
    """

    def __init__(self, pyboard):
        """Initialize the MicroPython board files class using the provided pyboard
        instance.  In most cases you should create a Pyboard instance (from
        pyboard.py) which connects to a board over a serial connection and pass
        it in, but you can pass in other objects for testing, etc.
        """
        self._pyboard = pyboard

    def ls(self, directory='/'):
        """List the contents of the specified directory (or root if none is
        specified).  Returns a list of strings with the names of files in the
        specified directory.
        """
        # Execute os.listdir() command on the board.
        command = """
            import os
            print(os.listdir('{0}'))
        """.format(directory)
        self._pyboard.enter_raw_repl()
        try:
            out = self._pyboard.exec_(textwrap.dedent(command))
        except PyboardError as ex:
            # Check if this is an OSError #2, i.e. directory doesn't exist and
            # rethrow it as something more descriptive.
            if ex.args[2].decode('utf-8').find('OSError: [Errno 2] ENOENT') != -1:
                raise RuntimeError('No such directory: {0}'.format(directory))
            else:
                raise ex
        self._pyboard.exit_raw_repl()
        # Parse the result list and return it.
        return ast.literal_eval(out.decode('utf-8'))

    def get(self, filename):
        """Retrieve the contents of the specified file and return its contents
        as a byte string.
        """
        # Open the file and read it a few bytes at a time and print out the
        # raw bytes.  Be careful not to overload the UART buffer so only write
        # a few bytes at a time, and don't use print since it adds newlines and
        # expects string data.
        command = """
            import sys
            with open('{0}', 'rb') as infile:
                while True:
                    result = infile.read({1})
                    if result == b'':
                        break
                    len = sys.stdout.write(result)
        """.format(filename, BUFFER_SIZE)
        self._pyboard.enter_raw_repl()
        try:
            out = self._pyboard.exec_(textwrap.dedent(command))
        except PyboardError as ex:
            # Check if this is an OSError #2, i.e. file doesn't exist and
            # rethrow it as something more descriptive.
            if ex.args[2].decode('utf-8').find('OSError: [Errno 2] ENOENT') != -1:
                raise RuntimeError('No such file: {0}'.format(filename))
            else:
                raise ex
        self._pyboard.exit_raw_repl()
        return out

    def put(self, filename, data):
        """Create or update the specified file with the provided data.
        """
        # Open the file for writing on the board and write chunks of data.
        self._pyboard.enter_raw_repl()
        self._pyboard.exec_("f = open('{0}', 'wb')".format(filename))
        size = len(data)
        # Loop through and write a buffer size chunk of data at a time.
        for i in range(0, size, BUFFER_SIZE):
            chunk_size = min(BUFFER_SIZE, size-i)
            chunk = repr(data[i:i+chunk_size])
            # Make sure to send explicit byte strings (handles python 2 compatibility).
            if not chunk.startswith('b'):
                chunk = 'b' + chunk
            self._pyboard.exec_("f.write({0})".format(chunk))
        self._pyboard.exec_('f.close()')
        self._pyboard.exit_raw_repl()

    def rm(self, filename):
        """Remove the specified file or directory."""
        command = """
            import os
            os.remove('{0}')
        """.format(filename)
        self._pyboard.enter_raw_repl()
        try:
            out = self._pyboard.exec_(textwrap.dedent(command))
        except PyboardError as ex:
            message = ex.args[2].decode('utf-8')
            # Check if this is an OSError #2, i.e. file/directory doesn't exist
            # and rethrow it as something more descriptive.
            if message.find('OSError: [Errno 2] ENOENT') != -1:
                raise RuntimeError('No such file/directory: {0}'.format(filename))
            # Check for OSError #13, the directory isn't empty.
            if message.find('OSError: [Errno 13] EACCES') != -1:
                raise RuntimeError('Directory is not empty: {0}'.format(filename))
            else:
                raise ex
        self._pyboard.exit_raw_repl()

    def run(self, filename):
        """Run the provided script and return its output.
        """
        self._pyboard.enter_raw_repl()
        out = self._pyboard.execfile(filename)
        self._pyboard.exit_raw_repl()
        return out
