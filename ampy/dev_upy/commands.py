from . import virtual_term


def open_term(addr: tuple, port: int, mode: str):
    virtual_term.add_client((addr[0], port), mode)


def exec_func(addr: tuple, as_str: str):
    res = {"result": None}
    try:
        exec('%s\nres["result"] = main(%s)' % (as_str, repr(addr)), {"res": res})
    except Exception as e:
        res["status"] = "failed"
        res["result"] = repr(e)
    else:
        res["status"] = "success"
    return res
