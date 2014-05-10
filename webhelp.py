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

def allow_cross_origin():
    # Allow cross-origin requests so that results may be obtained by
    # Javascript apps on other domains
    web.header('Access-Control-Allow-Origin', '*')

# Edit the error messages to return valid json:
def _json_wrap(error_class):
    error_class.message = json.dumps({'error': error_class.message})
for cls in ['badrequest', 'unauthorized', 'forbidden', '_NotFound',
        'notacceptable', 'conflict', 'gone', 'preconditionfailed',
        'unsupportedmediatype', '_InternalError']:
    _json_wrap(getattr(webapi, cls))

class _NoMethod(webapi.HTTPError):
    '''A 405 Method Not Allowed error.'''
    def __init__(self, cls=None):
        status = '405 Method Not Allowed'
        headers = {'Content-Type': 'application/json'}
        methods = ['GET', 'HEAD', 'POST', 'PUT', 'DELETE']
        if cls:
            methods = [method for method in methods if hasattr(cls, method)]
        headers['Allow'] = ', '.join(methods)
        data = json.dumps({'error': 'method not allowed', 'allowed': methods})
        webapi.HTTPError.__init__(self, status, headers, data)
webapi.nomethod = _NoMethod

# Because webapi sends errors as html!
_real_header = webapi.header
def _fake_header(hdr, value, unique=False):
    if hdr == 'Content-Type':
        _real_header(hdr, 'application/json', True)
    else:
        _real_header(hdr, value, unique)
webapi.header = _fake_header
def response_is_html():
    _real_header('Content-Type', 'text/html')
def response_is_json():
    _real_header('Content-Type', 'application/json')
_real_debugerror = web.debugerror
def _fake_debugerror(*args, **kwargs):
    response_is_html()
    _real_debugerror(*args, **kwargs)
web.debugerror = _fake_debugerror


if __name__ == '__main__':
    class A(object):pass
    class B(object):pass
    class C(object):pass
    urlhs = {'/a':A, '/b':B, '/c':C}
    print(_mk_application_args(urlhs))
