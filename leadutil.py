import random, datetime, time, re


def readf(fname):
    with open(fname) as fp:
        return fp.read()

def randstr():
    domain = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    result = ''
    for i in xrange(32):
        result += random.choice(domain)
    return result

def isinty(x):
    return isinstance(x,int) or isinstance(x,long)

def fromtimestamp(ts):
    assert isinty(ts)
    return datetime.datetime.fromtimestamp(long(ts)*1000L)

def totimestamp(dt):
    assert isinstance(dt, datetime.datetime)
    return long(time.mktime(dt.timetuple()))*1000L + dt.microsecond/1000L

def isodate(dt):
    assert isinstance(dt, datetime.datetime)
    return dt.isoformat().replace('T',' ')

def isotime(time):
    assert isinty(time)
    millis = time % 1000
    s = time / 1000 % 60
    m = time / (60*1000) % 60
    h = time / (60*60*1000)
    return '{h:02d}:{m:02d}:{s:02d}.{millis:03d}'.format(
        h=h, m=m, s=s, millis=millis)

def valid_field_name(name):
    return re.match('^[a-zA-Z][0-9a-zA-Z_]*$',name) and len(name) < 64
