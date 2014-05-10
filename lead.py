#!/usr/bin/env python
from __future__ import print_function
import web, json, sys, datetime
import psycopg2 as pg2
import webhelp
from leadutil import *


# Read the server configuration file:
config = json.loads(readf('config.json'))


class LeadUserError(Exception):
    def __init__(self, msg):
        super(LeadUserError,self).__init__(msg)
    def json(self):
        return json.dumps({'error': self.message})


class Field(object):
    def __init__(self, name, type, hidden):
        super(Field,self).__init__()
        self.name = name
        self.type = type
        self.hidden = hidden

class NativeField(Field):
    def __init__(self, name, type):
        super(NativeField,self).__init__(name, type, False)

        self.is_native = True
        self.select_as = 'score.{name}'.format(name=name)
        self.join = None
        self.where_name = self.select_as
        self.order_name = self.select_as
    def value_to_db(self, value):
        assert isinstance(value, FieldType)
        return value.to_db()

class AuxiliaryField(Field):
    def __init__(self, name, type, hidden, appid):
        super(AuxiliaryField,self).__init__(name, type, hidden)
        self.appid = appid

        self.is_native = False
        self.select_as = 'field_{name}.value AS {name}'.format(name=name)
        self.join = '''LEFT JOIN score_field AS field_{name}
                        ON field_{name}.appid = score.appid AND
                           field_{name}.id = score.id AND
                           field_{name}.name = '{name}' '''.format(name=name)
        self.where_name = 'field_{name}.value'.format(name=name)
        self.order_name = 'CAST(field_{name}.value AS {type})'.format(
                name=name, type=type.sql_type)
    def value_to_db(self, value):
        assert isinstance(value, FieldType)
        return value.to_db_varchar()


class FieldType(object):
    sql_type = None
    def __init__(self, source, value):
        super(FieldType,self).__init__()
        assert source in ('db','http')
        if source == 'db':
            self.value = self.from_db(value)
        else:
            assert source == 'http'
            self.value = self.from_http(value)
        self.post_convert()
    def post_convert(self): pass
    def from_db(self, value):
        return value
    def from_http(self, value):
        return value
    def to_json(self):
        return value
    def to_db(self):
        return value
    def to_db_varchar(self):
        return value

def basic_field_type(python_type,_sql_type):
    class BasicFieldType(FieldType):
        sql_type = _sql_type
        def __init__(self, *args):
            super(BasicFieldType,self).__init__(*args)
        def is_valid(self,value):
            return isinstance(value, python_type)
        def from_db(self,value):
            if value is None: return None
            if self.is_valid(value):
                return value
            assert isinstance(value,basestring)
            return python_type(value)
        def from_http(self, value):
            if value is None or value == 'null': return None
            if self.is_valid(value):
                return value
            assert isinstance(value,basestring)
            return python_type(value)
        def to_json(self):
            return self.value
        def to_db(self):
            return self.value
        def to_db_varchar(self):
            if self.value is None: return None
            return str(self.value)
    return BasicFieldType

class BoolFieldType(basic_field_type(bool,'BOOLEAN')): pass
class IntFieldType(basic_field_type(int,'INT')):
    def is_valid(self, value):
        return isinty(value)
class LongFieldType(basic_field_type(long,'BIGINT')):
    def is_valid(self, value):
        return isinty(value)
class DoubleFieldType(basic_field_type(float,'DOUBLE PRECISION')): pass
class StrFieldType(basic_field_type(str,'VARCHAR')):
    def is_valid(self,value):
        return isinstance(value,basestring)
    def post_convert(self):
        if self.value is not None:
            self.value = self.value[:256]

class DateFieldType(FieldType):
    sql_type = 'TIMESTAMP WITH TIME ZONE'
    def from_db(self,value):
        if value is None: return None
        if isinstance(value,datetime.datetime):
            return value
        return fromtimestamp(long(value))
    def from_http(self, value):
        if value is None: return None
        if isinstance(value,basestring):
            value = long(value)
        assert isinstance(value,int) or isinstance(value,long)
        return fromtimestamp(value)
    def to_json(self):
        if self.value is None: return None
        return [isodate(self.value), totimestamp(self.value)]
    def to_db_varchar(self):
        if self.value is None: return None
        return str(totimestamp(self.value))

class TimeFieldType(LongFieldType):
    def to_json(self):
        if self.value is None: return None
        return [isotime(self.value), self.value]

field_types = {
    'bool': BoolFieldType,
    'int': IntFieldType,
    'long': LongFieldType,
    'double': DoubleFieldType,
    'str': StrFieldType,
    'Date': DateFieldType,
    'Time': TimeFieldType,
}


class App(object):
    def __init__(self, appid):
        self.appid = appid
        assert config['database']['kind'] == 'postgres'
        self.db = pg2.connect(
            database=config['database']['dbname'],
            user=config['database']['user'],
            password=config['database']['password'],
            host=config['database']['host'])
        self.read_app_record()
        self._fields = None

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
    
    def get_fields(self):
        if self._fields is not None:
            return self._fields
        self._fields = [
            NativeField('id', LongFieldType),
            NativeField('submission', DateFieldType),
            NativeField('win', BoolFieldType),
            NativeField('board', StrFieldType),
            NativeField('mods', StrFieldType),
            NativeField('cheats', StrFieldType),
        ]
        with self.cursor() as cur:
            cur.execute(
                'SELECT appid,name,type,hidden FROM field WHERE appid = %s '+
                    'AND NOT hidden',
                [self.appid])
            for row in cur.fetchall():
                appid,name,type,hidden = row
                self._fields.append(AuxiliaryField(name, field_types[type], hidden,
                        appid))
        return self._fields

    def get_field(self, field_name):
        fields = self.get_fields()
        for field in fields:
            if field.name == field_name:
                return field
        return None

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
        webhelp.allow_cross_origin()
        try:
            with App(appid) as app:
                self.check_keys(app)
                return json.dumps(self.run(app))
        except LeadUserError as e:
            return e.json()
    def check_keys(self,app): pass
    def run(self, app):
        return {'error': 'TODO'}

class AppGETHandler(AppGenericHandler):
    def GET(self, appid):
        return self._generic_handler(appid)

class AppPOSTHandler(AppGenericHandler):
    def POST(self, appid):
        return self._generic_handler(appid)

class RequireWriteKey(object):
    def check_keys(self, app):
        i = web.input('writeKey')
        if i.writeKey != app.writeKey:
            raise LeadUserError('invalid writeKey')

class RequireAdminKey(object):
    def check_keys(self, app):
        i = web.input('adminKey')
        if i.adminKey != app.adminKey:
            raise LeadUserError('invalid adminKey')


pages = web.template.render('templates/')
class ReadUsageHandler(object):
    def GET(self):
        webhelp.response_is_html()
        return pages.usage(config['misc']['admin_email'])


class ReadListHandler(AppGETHandler):
    def run(self, app):
        i = web.input(filter=[], order='desc', sort='submission', count=20)
        filters = [(val.split(',',1)[0],val.split(',',1)[1])
                for val in i.filter]
        filters = [(app.get_field(f),v) for (f,v) in filters]
        filters = [(f, f.type('http', v)) for (f,v) in filters]
        sort_field = app.get_field(i.sort)
        order = i.order
        count = int(i.count)
        return run_search(app, filters, order, sort_field, count)

def run_search(app, filters, order, sort_field, count):
        '''
        Example giant query:

        SELECT score.id,
               submission,
               win,
               board,
               mods,
               field_coins.value AS coins
        FROM score
            LEFT JOIN score_field AS field_coins 
                ON field_coins.appid = score.appid AND
                   field_coins.id = score.id AND
                   field_coins.name = 'coins' 
        WHERE score.appid = 'lenna1' AND
              score.board = 'foobar' AND
              NOT score.hidden AND
              field_coins.value IS NOT NULL AND
              TRUE
        ORDER BY CAST(field_coins.value AS BIGINT) DESC;
        '''

        fields = app.get_fields()
        query = 'SELECT '
        query_args = []
        for (j,field) in enumerate(fields):
            if j != 0: query += ', '
            query += field.select_as + ' '

        query += 'FROM score '
        for field in fields:
            if field.join is not None:
                query += field.join + ' '

        query += 'WHERE score.appid = %s AND NOT score.hidden AND '
        query_args.append(app.appid)
        for (field,value) in filters:
            query += field.where_name + ' = %s AND '
            query_args.append(field.value_to_db(value))

        assert sort_field is not None
        query += sort_field.where_name + ' IS NOT NULL '
        query += 'ORDER BY '+sort_field.order_name
        assert order in ('asc','desc')
        if order == 'asc':
            query += ' ASC'
        else:
            query += ' DESC'

        print(query, file=sys.stderr)
        print(query_args, file=sys.stderr)
        results = []
        with app.cursor() as cur:
            cur.execute(query, query_args)
            rows = cur.fetchmany(count)
            for row in rows:
                obj = {}
                for (field,column) in zip(fields,row):
                    obj[field.name] = field.type('db', column).to_json()
                results.append(obj)
        return results

class WriteAddHandler(RequireWriteKey,AppPOSTHandler):
    def run(self,app):
        i = web.input('win','board','mods', win=False,board='',mods='')
        fields = app.get_fields()
        natfvals = {}
        auxfvals = []
        for field in fields:
            if field.name in i:
                if field.is_native:
                    natfvals[field.name] = field.type('http',i[field.name])
                else:
                    auxfvals.append((field, field.type('http',i[field.name])))
        with app.cursor() as cur:
            cur.execute('''
                INSERT INTO score (appid, submission, win, ip, board, hidden, mods)
                VALUES (%s, now(), %s, %s, %s, false, %s)''',
                [app.appid, natfvals['win'].to_db(), web.ctx['ip'],
                    natfvals['board'].to_db(), natfvals['mods'].to_db()])
            cur.execute('SELECT lastval()')
            score_id = cur.fetchone()[0]
            for (field,value) in auxfvals:
                cur.execute('''
                    INSERT INTO score_field (id, appid, name, value)
                    VALUES (%s,%s,%s,%s)''',
                    [score_id, app.appid, field.name, field.value_to_db(value)])
            cur.commit()

        id_field = app.get_field('id')
        results = run_search(app, [(id_field, id_field.type('db', score_id))],
            'desc', id_field, 20)
        assert len(results) == 1
        return results[0]

class AdminAddFieldHandler(RequireAdminKey,AppPOSTHandler):
    def run(self,app):
        i = web.input('name','type',name='',type='')
        if not valid_field_name(i.name):
            raise LeadUserError('invalid field name "'+i.name+'"')
        if i.type not in field_types:
            raise LeadUserError('invalid field type "'+i.type+'"')
        with app.cursor() as cur:
            cur.execute('SELECT * FROM field WHERE appid = %s AND name = %s',
                [app.appid, i.name])
            if cur.rowcount > 0:
                cur.execute('''
                    UPDATE field
                    SET type = %s, hidden = FALSE
                    WHERE appid = %s AND name = %s''',
                    [i.type, app.appid, i.name])
            else:
                cur.execute('''
                    INSERT INTO field (appid, name, type, hidden)
                    VALUES (%s, %s, %s, FALSE)''',
                    [app.appid, i.name, i.type])
            cur.commit()
        return {}

class AdminDelFieldHandler(RequireAdminKey,AppPOSTHandler):
    def run(self,app):
        i = web.input('name',name='')
        if not valid_field_name(i.name):
            raise LeadUserError('invalid field name "'+i.name+'"')
        with app.cursor() as cur:
            cur.execute('''
                UPDATE field SET hidden = TRUE
                WHERE appid = %s AND name = %s''',
                [app.appid, i.name])
            cur.commit()
        return {}

class AdminDelScoreHandler(RequireAdminKey,AppPOSTHandler):
    def run(self,app):
        i = web.input('id',id=0L)
        with app.cursor() as cur:
            cur.execute('''
                UPDATE score SET hidden = TRUE
                WHERE appid = %s AND id = %s''',
                [app.appid, i.id])
            cur.commit()
        return {}

class AdminRestoreScoreHandler(RequireAdminKey,AppPOSTHandler):
    def run(self,app):
        i = web.input('id',id=0L)
        with app.cursor() as cur:
            cur.execute('''
                UPDATE score SET hidden = FALSE
                WHERE appid = %s AND id = %s''',
                [app.appid, i.id])
            cur.commit()
        return {}

def _filter_timestamps(rows):
    for (i,row) in enumerate(rows):
        rows[i] = row = list(row)
        for (j,val) in enumerate(row):
            if isinstance(val,datetime.datetime):
                row[j] = totimestamp(val)
    return rows

def _dictify_results(description, results):
    return [dict(zip([c.name for c in description], row))
                for row in results]

class AdminDumpHandler(RequireAdminKey,AppGETHandler):
    def run(self,app):
        results = {}
        with app.cursor() as cur:
            cur.execute('SELECT * FROM score WHERE appid = %s', [app.appid])
            results['score'] = _dictify_results(cur.description,
                    _filter_timestamps(cur.fetchall()))
            cur.execute('SELECT * FROM field WHERE appid = %s', [app.appid])
            results['field'] = _dictify_results(cur.description, cur.fetchall())
            cur.execute('SELECT * FROM score_field WHERE appid = %s', [app.appid])
            results['score_field'] = _dictify_results(cur.description,cur.fetchall())
        return results


urls = {
    '/([^/]*)/list':            ReadListHandler,
    '/([^/]*)/add':             WriteAddHandler,
    '/([^/]*)/add-field':       AdminAddFieldHandler,
    '/([^/]*)/del-field':       AdminDelFieldHandler,
    '/([^/]*)/del-score':       AdminDelScoreHandler,
    '/([^/]*)/restore-score':   AdminRestoreScoreHandler,
    '/([^/]*)/dump':            AdminDumpHandler,
}

if config['misc']['show_usage']:
    urls['/'] = ReadUsageHandler


if __name__ == '__main__':
    web.config.debug = False
    app = webhelp.application(urls)
    app.run()
