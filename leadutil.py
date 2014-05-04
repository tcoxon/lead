import random


def readf(fname):
    with open(fname) as fp:
        return fp.read()

def randstr():
    domain = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    result = ''
    for i in xrange(32):
        result += random.choice(domain)
    return result
