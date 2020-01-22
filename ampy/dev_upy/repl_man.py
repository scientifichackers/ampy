from time import sleep, sleep_ms

from . import settings
from .remote_term import RemoteTerm


class ReplMan:
    _instance = None

    @classmethod
    def get_instance(cls) -> 'ReplMan':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.default_mode = self.do_nothing_mode
        self._mode = self.default_mode
        self.rt = RemoteTerm.get_instance()

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, f):
        self._mode = f
        self.rt.send_ctrl_c()

    def main(self):
        rt = self.rt
        while True:
            try:
                self.mode()
            except KeyboardInterrupt:
                if rt.fake_ctrl_c_flag:
                    rt.fake_ctrl_c_flag = False
                    continue
                raise
            self._mode = self.default_mode

    @staticmethod
    def do_nothing_mode():
        sleep(-1)

    def get_exec_code_mode(self, src: str, conn: tuple = None):
        if conn is not None:
            addr, sock = conn
        loc = {}
        files = self.rt.tx_files

        def func():
            if conn is not None:
                f = sock.makefile()
                files[addr] = f
            try:
                exec(src, loc)
            except Exception as e:
                print(repr(e))
            finally:
                if conn is not None:
                    sock.close()
                    f.close()

        return func

    @staticmethod
    def exec_saved_code_mode():
        try:
            import user_main
        except ImportError:
            sleep_ms(settings.SAVED_CODE_POLL_MS)
        else:
            print("[ampy] Executing saved code...")
            user_main.main()
