# Adafruit MicroPython Tool - File Operation Tests
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
import tempfile
import sys
import unittest

# Try importing python 3 mock library, then fall back to python 2 (external module).
try:
    import unittest.mock as mock
except ImportError:
    import mock

import ampy.files as files
from ampy.pyboard import PyboardError


class TestFiles(unittest.TestCase):
    def raisesRegex(self, *args, **kwargs):
        # Wrapper to work with the different names for assertRaisesRegex vs.
        # assertRaisesRegexp in Python 3 vs. 2 (ugh).
        if sys.version_info >= (3, 2):
            return self.assertRaisesRegex(*args, **kwargs)
        else:
            return self.assertRaisesRegexp(*args, **kwargs)

    def test_ls_multiple_files(self):
        pyboard = mock.Mock()
        pyboard.exec_ = mock.Mock(return_value=b"['boot.py', 'main.py', 'foo.txt']")
        board_files = files.Files(pyboard)
        result = board_files.ls()
        self.assertListEqual(result, ["boot.py", "main.py", "foo.txt"])

    def test_ls_no_files(self):
        pyboard = mock.Mock()
        pyboard.exec_ = mock.Mock(return_value=b"[]")
        board_files = files.Files(pyboard)
        result = board_files.ls()
        self.assertListEqual(result, [])

    def test_ls_bad_directory(self):
        pyboard = mock.Mock()
        pyboard.exec_ = mock.Mock(
            side_effect=PyboardError(
                "exception",
                b"",
                b'Traceback (most recent call last):\r\n  File "<stdin>", line 3, in <module>\r\nOSError: [Errno 2] ENOENT\r\n',
            )
        )
        with self.raisesRegex(RuntimeError, "No such directory: /foo"):
            board_files = files.Files(pyboard)
            result = board_files.ls("/foo")

    def test_get_with_data(self):
        pyboard = mock.Mock()
        pyboard.exec_ = mock.Mock(return_value=b"hello world")
        board_files = files.Files(pyboard)
        result = board_files.get("foo.txt")
        self.assertEqual(result, b"hello world")

    def test_get_bad_file(self):
        pyboard = mock.Mock()
        pyboard.exec_ = mock.Mock(
            side_effect=PyboardError(
                "exception",
                b"",
                b'Traceback (most recent call last):\r\n  File "<stdin>", line 3, in <module>\r\nOSError: [Errno 2] ENOENT\r\n',
            )
        )
        with self.raisesRegex(RuntimeError, "No such file: foo.txt"):
            board_files = files.Files(pyboard)
            result = board_files.get("foo.txt")

    def test_put(self):
        pyboard = mock.Mock()
        pyboard.exec_ = mock.Mock(return_value=b"")
        board_files = files.Files(pyboard)
        board_files.put("foo.txt", "hello world")

    def test_rm(self):
        pyboard = mock.Mock()
        pyboard.exec_ = mock.Mock(return_value=b"")
        board_files = files.Files(pyboard)
        board_files.rm("foo.txt")

    def test_rm_file_doesnt_exist(self):
        pyboard = mock.Mock()
        pyboard.exec_ = mock.Mock(
            side_effect=PyboardError(
                "exception",
                b"",
                b'Traceback (most recent call last):\r\n  File "<stdin>", line 3, in <module>\r\nOSError: [Errno 2] ENOENT\r\n',
            )
        )
        with self.raisesRegex(RuntimeError, "No such file/directory: foo.txt"):
            board_files = files.Files(pyboard)
            result = board_files.rm("foo.txt")

    def test_rm_directory_not_empty(self):
        pyboard = mock.Mock()
        pyboard.exec_ = mock.Mock(
            side_effect=PyboardError(
                "exception",
                b"",
                b'Traceback (most recent call last):\r\n  File "<stdin>", line 3, in <module>\r\nOSError: [Errno 13] EACCES\r\n',
            )
        )
        with self.raisesRegex(RuntimeError, "Directory is not empty: foo"):
            board_files = files.Files(pyboard)
            result = board_files.rm("foo")

    def test_rmdir(self):
        pyboard = mock.Mock()
        pyboard.exec_ = mock.Mock(return_value=b"")
        board_files = files.Files(pyboard)
        board_files.rmdir("foo")

    def test_rmdir_folder_doesnt_exist(self):
        pyboard = mock.Mock()
        pyboard.exec_ = mock.Mock(
            side_effect=PyboardError(
                "exception",
                b"",
                b'Traceback (most recent call last):\r\n  File "<stdin>", line 3, in <module>\r\nOSError: [Errno 2] ENOENT\r\n',
            )
        )
        with self.raisesRegex(RuntimeError, "No such directory: foo"):
            board_files = files.Files(pyboard)
            result = board_files.rmdir("foo")

    def test_run_with_output(self):
        pyboard = mock.Mock()
        pyboard.execfile = mock.Mock(return_value=b"Hello world")
        board_files = files.Files(pyboard)
        with tempfile.NamedTemporaryFile() as program:
            program.write(b'print("Hello world")')
            program.flush()
            output = board_files.run(program.name)
        self.assertEqual(output, b"Hello world")

    def test_run_without_output(self):
        pyboard = mock.Mock()
        pyboard.exec_raw_no_follow = mock.Mock()
        board_files = files.Files(pyboard)
        with tempfile.NamedTemporaryFile() as program:
            program.write(b'print("Hello world")')
            program.flush()
            output = board_files.run(program.name, wait_output=False)
        self.assertEqual(output, None)
        pyboard.exec_raw_no_follow.assert_called_once_with(b'print("Hello world")')

    def test_mkdir_no_error(self):
        pyboard = mock.Mock()
        pyboard.exec_ = mock.Mock(return_value=b"")
        board_files = files.Files(pyboard)
        board_files.mkdir("/foo")

    def test_mkdir_directory_already_exists(self):
        pyboard = mock.Mock()
        pyboard.exec_ = mock.Mock(
            side_effect=PyboardError(
                "exception",
                b"",
                b'Traceback (most recent call last):\r\n  File "<stdin>", line 3, in <module>\r\nOSError: [Errno 17] EEXIST\r\n',
            )
        )
        with self.raisesRegex(
            files.DirectoryExistsError, "Directory already exists: /foo"
        ):
            board_files = files.Files(pyboard)
            board_files.mkdir("/foo")


if __name__ == "__main__":
    unittest.main()
