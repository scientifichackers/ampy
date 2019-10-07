from . import virtual_term


def open_term(addr, port):
    virtual_term.add(addr[0], port)


def exec_func(addr, as_str):
    res = {"result": None}
    try:
        exec('%s\nres["result"] = main(%s)' % (as_str, repr(addr)), {"res": res})
    except Exception as e:
        res["status"] = "failed"
        res["result"] = repr(e)
    else:
       res["status"] = "success"
    return res
