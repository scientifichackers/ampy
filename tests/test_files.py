# Adafruit MicroPython Tool - File Operation Tests
# Author: Tony DiCola
import unittest
# Try importing python 3 mock library, then fall back to python 2 (external module).
try:
    import unittest.mock as mock
except ImportError:
    import mock

import ampy.files as files
from ampy.pyboard import PyboardError


class TestFiles(unittest.TestCase):

    def test_ls_multiple_files(self):
        pyboard = mock.Mock()
        pyboard.exec_ = mock.Mock(return_value=b"['boot.py', 'main.py', 'foo.txt']")
        board_files = files.Files(pyboard)
        result = board_files.ls()
        self.assertListEqual(result, ['boot.py', 'main.py', 'foo.txt'])

    def test_ls_no_files(self):
        pyboard = mock.Mock()
        pyboard.exec_ = mock.Mock(return_value=b"[]")
        board_files = files.Files(pyboard)
        result = board_files.ls()
        self.assertListEqual(result, [])

    def test_ls_bad_directory(self):
        pyboard = mock.Mock()
        pyboard.exec_ = mock.Mock(side_effect=PyboardError('exception', b'', b'Traceback (most recent call last):\r\n  File "<stdin>", line 3, in <module>\r\nOSError: [Errno 2] ENOENT\r\n'))
        with self.assertRaisesRegex(RuntimeError, 'No such directory: /foo'):
            board_files = files.Files(pyboard)
            result = board_files.ls('/foo')

    def test_get_with_data(self):
        pyboard = mock.Mock()
        pyboard.exec_ = mock.Mock(return_value=b"hello world")
        board_files = files.Files(pyboard)
        result = board_files.get('foo.txt')
        self.assertEqual(result, b"hello world")

    def test_get_bad_file(self):
        pyboard = mock.Mock()
        pyboard.exec_ = mock.Mock(side_effect=PyboardError('exception', b'', b'Traceback (most recent call last):\r\n  File "<stdin>", line 3, in <module>\r\nOSError: [Errno 2] ENOENT\r\n'))
        with self.assertRaisesRegex(RuntimeError, 'No such file: foo.txt'):
            board_files = files.Files(pyboard)
            result = board_files.get('foo.txt')

    def test_put(self):
        pyboard = mock.Mock()
        pyboard.exec_ = mock.Mock(return_value=b"")
        board_files = files.Files(pyboard)
        board_files.put('foo.txt', 'hello world')

    def test_rm(self):
        pyboard = mock.Mock()
        pyboard.exec_ = mock.Mock(return_value=b"")
        board_files = files.Files(pyboard)
        board_files.rm('foo.txt')

    def test_rm_file_doesnt_exist(self):
        pyboard = mock.Mock()
        pyboard.exec_ = mock.Mock(side_effect=PyboardError('exception', b'', b'Traceback (most recent call last):\r\n  File "<stdin>", line 3, in <module>\r\nOSError: [Errno 2] ENOENT\r\n'))
        with self.assertRaisesRegex(RuntimeError, 'No such file/directory: foo.txt'):
            board_files = files.Files(pyboard)
            result = board_files.rm('foo.txt')

    def test_rm_directory_not_empty(self):
        pyboard = mock.Mock()
        pyboard.exec_ = mock.Mock(side_effect=PyboardError('exception', b'', b'Traceback (most recent call last):\r\n  File "<stdin>", line 3, in <module>\r\nOSError: [Errno 13] EACCES\r\n'))
        with self.assertRaisesRegex(RuntimeError, 'Directory is not empty: foo'):
            board_files = files.Files(pyboard)
            result = board_files.rm('foo')
