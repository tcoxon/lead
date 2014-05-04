from __future__ import print_function
import web, json, sys
import psycopg2 as pg2
import webhelp
from leadutil import *

# Config stuff. You'll need to change this to make it work:
_DB_PASSWORD_PATH = '/home/tomc/.lead-db-pass'


class LeadUserError(Exception):
    def __init__(self, msg):
        super(LeadUserError,self).__init__(msg)
    def json(self):
        return json.dumps({'error': self.message})


class App(object):
    def __init__(self, appid):
        self.appid = appid
        self.db = pg2.connect(
            database='lead',
            user='lead',
            password=readf(_DB_PASSWORD_PATH).strip(),
            host='127.0.0.1')
        self.read_app_record()

    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.db.close()

    def cursor(self):
        db = self.db
        class WrappedCursor(object):
            def __init__(self, cur):
                self.cur = cur
            def __getattr__(self, name):
                return getattr(self.cur, name)
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.cur.close()
                db.cancel()
            def commit(self):
                db.commit()
        return WrappedCursor(db.cursor())

    def read_app_record(self):
        with self.cursor() as cur:
            cur.execute('SELECT writeKey,adminKey FROM app WHERE appid = %s',
                    [self.appid])
            if cur.rowcount < 1:
                raise LeadUserError('unrecognized app')
            assert cur.rowcount == 1

            row = cur.fetchone()
            self.writeKey, self.adminKey = row


class AppGenericHandler(object):
    def _generic_handler(self,appid):
        webhelp.response_is_json()
        try:
            with App(appid) as app:
                return json.dumps(self.run(app))
        except LeadUserError as e:
            return e.json()
    def run(self, app):
        return {'error': 'TODO'}

class AppGETHandler(AppGenericHandler):
    def GET(self, appid):
        return self._generic_handler(appid)

class AppPOSTHandler(AppGenericHandler):
    def POST(self, appid):
        return self._generic_handler(appid)


pages = web.template.render('templates/')
class ReadUsageHandler(object):
    def GET(self):
        webhelp.response_is_html()
        return pages.usage()


class ReadListHandler(AppGETHandler): pass
class WriteAddHandler(AppPOSTHandler): pass
class AdminAddFieldHandler(AppPOSTHandler): pass
class AdminDelFieldHandler(AppPOSTHandler): pass
class AdminDelScoreHandler(AppPOSTHandler): pass
class AdminRestoreScoreHandler(AppPOSTHandler): pass
class AdminDumpHandler(AppGETHandler): pass


urls = {
    '/':                        ReadUsageHandler,
    '/([^/]*)/list':            ReadListHandler,
    '/([^/]*)/add':             WriteAddHandler,
    '/([^/]*)/add-field':       AdminAddFieldHandler,
    '/([^/]*)/del-field':       AdminDelFieldHandler,
    '/([^/]*)/del-score':       AdminDelScoreHandler,
    '/([^/]*)/restore-score':   AdminRestoreScoreHandler,
    '/([^/]*)/dump':            AdminDumpHandler,
}

if __name__ == '__main__':
    web.config.debug = False
    app = webhelp.application(urls)
    app.run()
