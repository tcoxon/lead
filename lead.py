import web

import webhelp


pages = web.template.render('templates/')

class UsageHandler(object):
    def GET(self):
        return pages.usage()

class GetHandler(object):
    def GET(self):
        # TODO
        i = web.input('id')
        return 'id was {}'.format(i.id)

class ListHandler(object):
    def GET(self):
        # TODO
        return "hello world"

urls = {
    '/':                        UsageHandler,
    '/get':                     GetHandler,
    '/list':                    ListHandler,
}

if __name__ == '__main__':
    app = webhelp.application(urls)
    app.run()
