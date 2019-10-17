from . import virtual_term


def open_term(host: str, port: int, mode: str):
    virtual_term.add_client((host, port), mode)


def exec_func(host: str, main_fn: str, fn_args: tuple, fn_kwargs: dict):
    response = {}

    code = main_fn + "\nresponse['result'] = main(host, *fn_args, **fn_kwargs)"
    locals = {
        "response": response,
        "host": host,
        "fn_args": fn_args,
        "fn_kwargs": fn_kwargs,
    }

    try:
        exec(code, locals)
    except Exception as e:
        response["status"] = "failed"
        response["result"] = repr(e)
    else:
        response["status"] = "success"

    return response
