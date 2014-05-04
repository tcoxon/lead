import web

import webhelp


pages = web.template.render('templates/')

class ReadUsageHandler(object):
    def GET(self):
        return pages.usage()

class ReadListHandler(object):
    def GET(self,appid):
        # TODO
        return 'hello world appid={}'.format(appid)

class WriteAddHandler(object):
    def POST(self,appid):
        # TODO
        return 'hello world'

urls = {
    '/':                        ReadUsageHandler,
    '/([^/]*)/list':            ReadListHandler,
    '/([^/]*)/add':             WriteAddHandler,
}

if __name__ == '__main__':
    app = webhelp.application(urls)
    app.run()
