import web


def _zip(xs, ys):
    r = [None]*(len(xs)+len(ys))
    r[::2] = xs
    r[1::2] = ys
    return r

def _mk_application_args(urlhandlers):
    assert isinstance(urlhandlers, dict)

    ks = list(urlhandlers.keys())
    urls = _zip(ks, [urlhandlers[k].__name__ for k in ks])
    handlers = {v.__name__: v for (k,v) in urlhandlers.iteritems()}
    return (urls, handlers)

def application(urlhandlers):
    return web.application(*_mk_application_args(urlhandlers))


if __name__ == '__main__':
    class A(object):pass
    class B(object):pass
    class C(object):pass
    urlhs = {'/a':A, '/b':B, '/c':C}
    print(_mk_application_args(urlhs))
