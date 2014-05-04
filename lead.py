import web, json
import webhelp


pages = web.template.render('templates/')
class ReadUsageHandler(object):
    def GET(self):
        webhelp.response_is_html()
        return pages.usage()

class ReadListHandler(object):
    def GET(self,appid):
        webhelp.response_is_json()
        # TODO
        return json.dumps({'msg': 'hello world appid={}'.format(appid)})

class WriteAddHandler(object):
    def POST(self,appid):
        webhelp.response_is_json()
        # TODO
        return 'hello world'


urls = {
    '/':                        ReadUsageHandler,
    '/([^/]*)/list':            ReadListHandler,
    '/([^/]*)/add':             WriteAddHandler,
}

if __name__ == '__main__':
    web.config.debug = False
    app = webhelp.application(urls)
    app.run()
