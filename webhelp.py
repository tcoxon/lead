import web, json
import web.webapi as webapi


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

class _Application(web.application):
    pass

def application(urlhandlers):
    return _Application(*_mk_application_args(urlhandlers))

# Edit the error messages to return valid json:
def _json_wrap(error_class):
    error_class.message = json.dumps({'error': error_class.message})
for cls in ['badrequest', 'unauthorized', 'forbidden', '_NotFound',
        'notacceptable', 'conflict', 'gone', 'preconditionfailed',
        'unsupportedmediatype', '_InternalError']:
    _json_wrap(getattr(webapi, cls))

if __name__ == '__main__':
    class A(object):pass
    class B(object):pass
    class C(object):pass
    urlhs = {'/a':A, '/b':B, '/c':C}
    print(_mk_application_args(urlhs))
