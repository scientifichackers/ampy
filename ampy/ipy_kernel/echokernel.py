from ipykernel.kernelbase import Kernel
from traitlets import Instance

from ampy.dev import discovery_client, commands
from ampy.dev_upy import settings

host = next(discovery_client.main())
print(host)


class EchoKernel(Kernel):
    implementation = 'Echo'
    implementation_version = '1.0'
    language = 'no-op'
    language_version = '0.1'
    language_info = {
        'name': 'python',
        'mimetype': 'text/x-python',
        'file_extension': '.py',
    }
    banner = "ampy micropython kernel"

    input_transformer_manager = Instance('IPython.core.inputtransformer2.TransformerManager', ())

    # do_complete
    # do_inspect
    # do_history
    # do_shutdown

    def do_execute(self, code, silent, store_history=True, user_expressions=None,
                   allow_stdin=False):
        try:
            res, f = commands.exec_code(host, code, silent=silent)
            while True:
                b = f.recv(1024)
                if not b:
                    break
                self.send_response(
                    self.iopub_socket, 'stream', {
                        'name': 'stdout', 'text': b.decode()
                    }
                )
        except KeyboardInterrupt:
            commands.send_ctrl_c(host)

        return {
            'status': 'ok',
            # The base class increments the execution count
            'execution_count': self.execution_count,
            'payload': [],
            'user_expressions': {},
        }

    def do_is_complete(self, code):
        """
        Stolen from IPythonKernel (ipykernel/ipykernel/ipkernel.py).
        """
        status, indent_spaces = self.input_transformer_manager.check_complete(code)
        r = {'status': status}
        if status == 'incomplete':
            r['indent'] = ' ' * indent_spaces
        return r


if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp

    IPKernelApp.launch_instance(kernel_class=EchoKernel)
