#!/usr/bin/env python
import hashlib
import random

from copy import deepcopy
from datetime import datetime
from w3lib.html import replace_tags
from flask import Flask, g, request, redirect, url_for, flash, jsonify
from flask_admin import Admin, AdminIndexView
from flask_admin.base import expose
from flask_admin.helpers import validate_form_on_submit
from flask_admin.form import Select2Widget
from wtforms import form, fields, validators
from jinja2 import Markup
from flask_login import (LoginManager, UserMixin, current_user,
                         login_required, login_user, logout_user)
from werkzeug.contrib.fixers import ProxyFix

from vanko.flask.utils import setup_flask_logger, as_choices
from vanko.utils import getenv

from pymongo import MongoClient
from vanko.flask.admin_pymongo import (PyMongoModelFilter,
                                       PyMongoModelChoices, PyMongoModelView)

CAN_EXPORT = True
EXPORT_PRODUCER = 'csv'
SECRET_KEY = getenv('SECRET_KEY', 'kLIuJ_dvoznak2016_v3')
DEBUG = getenv('DEBUG', False)
PORT = getenv('PORT', 8000)
MONGODB_URL = getenv('MONGODB_URL', 'mongodb://localhost/test')
SPIDER_LOG_LEVEL = getenv('SPIDER_LOG_LEVEL', 'INFO')
APP_PREFIX = 'dvoznak'
SQLALCHEMY_TRACK_MODIFICATIONS = True


app = Flask(__name__)
app.config.from_object(__name__)
app.debug = app.config['DEBUG']
app.wsgi_app = ProxyFix(app.wsgi_app)
setup_flask_logger(app)

logman = LoginManager(app)
logman.login_view = 'admin.login_view'
# logman.session_protection = 'strong'


def cut_str(text, length):
    text = text or ''
    if len(text) > length:
        text = text[:length] + '...'
    return text


def fix_query(query):
    def _check(q):
        for op, val in q.items():
            if isinstance(val, list):
                for sub in val:
                    _check(sub)
            elif op == 'archived':
                _check.found = True
                if val == 'all':
                    q['archived'] = {'$in': ['archived', 'fresh']}

    try:
        query = deepcopy(query)
    except TypeError:
        # Raised during free text search:
        # TypeError: cannot deepcopy this pattern object
        pass
    else:
        _check.found = False
        _check(query)
        if _check.found:
            return query
    arch = {'archived': 'fresh'}
    return {'$and': [query, arch]} if query else arch


class ArchivingCollection(object):
    def __init__(self, coll):
        self._coll = coll

    def find(self, query, *args, **kwargs):
        return self._coll.find(fix_query(query), *args, **kwargs)

    def __getattr__(self, attr):
        return getattr(self._coll, attr)


class NewsForm(form.Form):
    url = fields.StringField('Link to News')
    section = fields.SelectField('Sport', widget=Select2Widget())
    subsection = fields.SelectField('Liga', widget=Select2Widget())
    updated = fields.DateTimeField('Updated')
    short_title = fields.StringField('Participants')
    title = fields.StringField('Title')
    published = fields.DateTimeField('Published')
    preamble = fields.TextAreaField('Preamble')
    content = fields.TextAreaField('Content')
    image1_filename = fields.StringField('Image 1')
    crawled = fields.DateTimeField('Fetched At (GMT+0)')
    archived = fields.SelectField(
        'Archived', widget=Select2Widget(),
        choices=as_choices(['archived', 'fresh']))

    def __init__(self, *args, **kw):
        super(NewsForm, self).__init__(*args, **kw)
        self.section.choices = \
            PyMongoModelChoices(g.mongo_db.dvoznak_news, 'section')
        self.subsection.choices = \
            PyMongoModelChoices(g.mongo_db.dvoznak_news, 'subsection')


class NewsView(PyMongoModelView):
    list_template = 'news_list.html'
    form = NewsForm
    edit_modal = True
    can_export = CAN_EXPORT
    export_producer = EXPORT_PRODUCER
    case_insensitive_search = True
    page_size = 50

    can_create = False

    @property
    def can_edit(self):
        return getattr(current_user, 'is_admin', False)

    @property
    def can_delete(self):
        return self.can_edit

    def is_accessible(self):
        return current_user.is_authenticated

    column_list = ['pk', 'published', 'section', 'subsection',
                   'short_title', 'title', 'content_cut',
                   'updated', 'crawled', 'url',
                   'has_image', 'archived']
    column_sortable_list = ['pk', 'url', 'section', 'subsection', 'crawled',
                            'updated', 'published', 'short_title', 'title',
                            'content_cut', 'archived', 'has_image']
    column_searchable_list = ['short_title', 'title', 'preamble', 'content']
    column_default_sort = ('published', True)
    column_labels = dict(
        pk='ID',
        url='Link',
        section='Sport',
        subsection='Liga',
        updated='Updated',
        short_title='Participants',
        title='Title',
        published='Published',
        content_cut='Content',
        has_image='Has Image',
        crawled='Fetched',
        archived='Archived',
        )
    column_formatters = dict(
        # url=LinkFormatter(rel='noreferrer')
        )

    column_format_excel = dict(
        title=dict(width=12, type='string', label='Title'),
        )

    @property
    def column_filters(self):
        return [
            PyMongoModelFilter(int, '==')('pk', 'By ID'),
            PyMongoModelFilter('Date', '==')('published', 'By Published Date'),
            PyMongoModelFilter('Date', 'between')('published',
                                                  'By Published Date'),
            PyMongoModelFilter('Date', '==')('updated', 'By Updated Date'),
            PyMongoModelFilter('Date', 'between')('updated',
                                                  'By Updated Date'),
            PyMongoModelFilter(str, '==')(
                'section', 'By Sport',
                PyMongoModelChoices(self.coll, 'section')),
            PyMongoModelFilter(str, '==')(
                'subsection', 'By Liga',
                PyMongoModelChoices(self.coll, 'subsection')),
            PyMongoModelFilter(str, '==')(
                'archived', 'By Archived',
                as_choices(['archived', 'fresh', 'all'])),
        ]

    def __init__(self, *args, **kwargs):
        super(NewsView, self).__init__(*args, **kwargs)
        self.coll = ArchivingCollection(self.coll)

    def get_list(self, *args, **kwargs):
        count, data = super(NewsView, self).get_list(*args, **kwargs)
        for item in data:
            item['content_cut'] = Markup(
                u'<div class="dz_pre">{pre}</div> <div class="dz_body"><span>'
                u'{text}</span> <a href="{url}" target="_blank">(more...)</a>'
                u'</div>'.format(
                    pre=cut_str(replace_tags(item.get('preamble', '')), 60),
                    text=cut_str(replace_tags(item.get('content', '')), 100),
                    url=self.get_url('.show_stub', id=item['_id'])))
            item['has_image'] = bool(item.get('image1_filename', ''))
        return count, data

    @expose('/show_stub/<id>')
    @login_required
    def show_stub(self, id):
        item = self.get_one(id)
        return self.render('stub_view.html', **item)

    @expose('/action/crawl/news/', methods=['POST'])
    @login_required
    def crawl_news(self, domain=None):
        runner.run('news')
        return self.redirect_back()

    @expose('/action/crawl/stop/', methods=['POST'])
    @login_required
    def stop_all(self):
        runner.stop(verbose=True, killdynos=True)
        return self.redirect_back()


class TipsForm(form.Form):
    pk = fields.IntegerField('Tip Id')
    place = fields.StringField('Liga')
    title = fields.StringField('Title')
    tip = fields.StringField('Tip')
    published = fields.DateTimeField('Published (Objavljeno)')
    updated = fields.DateTimeField('Updated At')
    text = fields.TextAreaField('Primary Text')
    result = fields.StringField('Result (Rezultat)')
    tipster = fields.StringField('Tipster')
    coeff = fields.StringField('Coeff. (Koeficijent)')
    min_coeff = fields.StringField('Min Coeff.')
    stake = fields.StringField('Stake (Ulog)')
    due = fields.StringField('Earnings Due (Zarada)')
    spread = fields.StringField('Spread (Is. Margina)')
    betting = fields.StringField('Betting (Kladionica)')
    success = fields.StringField(u'Success (Uspje\u0161nost)')
    details_url = fields.StringField('Link to Details Page')
    crawled = fields.DateTimeField('Fetched At (GMT+0)')
    archived = fields.SelectField(
        'Archived', widget=Select2Widget(),
        choices=as_choices(['archived', 'fresh']))


class TipsView(PyMongoModelView):
    list_template = 'tips_list.html'
    form = TipsForm
    edit_modal = True
    can_export = CAN_EXPORT
    export_producer = EXPORT_PRODUCER
    case_insensitive_search = True
    page_size = 50

    can_create = False

    @property
    def can_edit(self):
        return getattr(current_user, 'is_admin', False)

    @property
    def can_delete(self):
        return self.can_edit

    def is_accessible(self):
        return current_user.is_authenticated

    column_list = ['pk', 'published', 'place', 'title', 'tip',
                   'result', 'tipster', 'coeff', 'min_coeff',
                   'stake', 'due', 'spread', 'betting', 'success',
                   'text_cut', 'updated', 'crawled',
                   'details_url', 'archived']
    column_sortable_list = column_list
    column_searchable_list = ['title', 'tip', 'text']
    column_default_sort = ('published', True)
    column_labels = dict(
        pk='ID',
        place='Liga',
        title='Participants',
        tip='Tip',
        published='Published (Objavljeno)',
        updated='Updated At',
        result='Result (Rezultat)',
        tipster='Tipster',
        coeff='Coeff. (Koeficijent)',
        min_coeff='Min Coeff.',
        stake='Stake (Ulog)',
        due='Earnings Due (Zarada)',
        spread='Spread (Is. Margina)',
        betting='Betting (Kladionica)',
        success=u'Success (Uspje\u0161nost)',
        details_url='Link',
        crawled='Fetched At',
        )
    column_formatters = dict(
        # details_url=LinkFormatter(rel='noreferrer'),
        )

    column_format_excel = dict(
        title=dict(width=12, type='string', label='Title'),
        )

    @property
    def column_filters(self):
        return [
            PyMongoModelFilter(int, '==')('pk', 'By ID'),
            PyMongoModelFilter('Date', '==')('pubished', 'By Published Date'),
            PyMongoModelFilter('Date', 'between')('published', 'By Published Date'),
            PyMongoModelFilter('Date', '==')('updated', 'By Updated Date'),
            PyMongoModelFilter('Date', 'between')('updated', 'By Updated Date'),
            PyMongoModelFilter(str, '==')(
                'place', 'By Liga',
                PyMongoModelChoices(self.coll, 'place')),
            PyMongoModelFilter(str, '==')(
                'tipster', 'By Tipster',
                PyMongoModelChoices(self.coll, 'tipster')),
            PyMongoModelFilter(str, '==')(
                'archived', 'By Archived',
                as_choices(['archived', 'fresh', 'all'])),
        ]

    def __init__(self, *args, **kwargs):
        super(TipsView, self).__init__(*args, **kwargs)
        self.coll = ArchivingCollection(self.coll)

    def get_list(self, *args, **kwargs):
        count, data = super(TipsView, self).get_list(*args, **kwargs)
        for item in data:
            item['tip'] = Markup(
                u'<div class="dz_title">{tip}</div>'
                u'<div class="dz_body"><span>{cut}</span> '
                u'<a data-toggle="modal" href="{url}" title="Show text" '
                u'data-target="#fa_modal_window">(more...)</a></div>'.format(
                    cut=cut_str(replace_tags(item.get('text', '')), 80),
                    url=self.get_url('.show_tip', id=item['_id']),
                    tip=item['tip']))
        return count, data

    @expose('/show_tip/<id>')
    @login_required
    def show_tip(self, id):
        item = self.get_one(id)
        return self.render('tips_text.html', **item)

    @expose('/action/crawl/tips/', methods=['POST'])
    @login_required
    def crawl_tips(self, domain=None):
        runner.run('tips')
        return self.redirect_back()

    @expose('/action/crawl/stop/', methods=['POST'])
    @login_required
    def stop_all(self):
        runner.stop(verbose=True, killdynos=True)
        return self.redirect_back()


class CrawlsForm(form.Form):
    pk = fields.IntegerField('Id')
    host = fields.StringField('Host')
    ipaddr = fields.StringField('IP Address')
    action = fields.StringField('Action')
    type = fields.StringField('Type')
    status = fields.StringField('Status')
    started = fields.StringField('Started At')
    ended = fields.StringField('Ended At')
    news = fields.IntegerField('News Returned')
    tips = fields.IntegerField('Tips Returned')


class CrawlsView(PyMongoModelView):
    form = CrawlsForm
    can_export = can_edit = can_create = False
    can_edit = True

    def is_accessible(self):
        return getattr(current_user, 'is_admin', False)

    column_list = ['pk', 'action', 'type', 'status', 'started', 'ended',
                   'news', 'tips', 'host', 'ipaddr', 'pid']
    column_sortable_list = column_list
    column_default_sort = ('pk', True)
    column_labels = dict(
        pk='Job Id',
        host='Hostname',
        ipaddr='IP Address',
        pid='PID',
        action='Target',
        status='Status',
        started='Started At',
        ended='Ended At',
        news='No. Of News',
        tips='No. Of Tips',
        )


class Runner(object):
    def __init__(self):
        pass

    def run(self, action):
        utc = datetime.utcnow().replace(microsecond=0)
        crawl_table = g.mongo_db.dvoznak_crawls
        query = dict(action=action, status='waiting')
        result = crawl_table.update_one(query, {'$set': dict(started=utc)})
        if result.matched_count == 0:
            mpk = (crawl_table.find_one(sort=[('pk', -1)]) or {'pk': 0})['pk']
            data = dict(pk=mpk+1, action=action, status='waiting',
                        type='manual', started=str(utc), ended=None,
                        host=None, ipaddr=None, pid=None, news=None, tips=None)
            crawl_table.insert_one(data)

    def stop(self, sig=None, tb=None, verbose=False, killdynos=False):
        pass


runner = Runner()


@app.route('/api/spider/run', methods=['POST'])
def api_spider_run():
    utc = datetime.utcnow().replace(microsecond=0)
    my_meta = dict(utc=str(utc), rand=str(random.randint(1, 99)))
    digest = '|'.join([str(my_meta[key]) for key in sorted(my_meta.keys())])
    my_meta['digest'] = hashlib.sha1(digest + SECRET_KEY).hexdigest()

    try:
        res = request.json
        meta = res['meta']
        ref_digest = meta.pop('digest', '')
        digest = '|'.join([str(meta[key]) for key in sorted(meta.keys())])
        assert hashlib.sha1(digest + SECRET_KEY).hexdigest() == ref_digest

        crawl_table = g.mongo_db.dvoznak_crawls
        type_ = meta.get('type', '') or 'manual'
        action = ''
        env = {}
        data = dict(host=meta['host'], ipaddr=meta['ipaddr'], pid=meta['pid'],
                    status='started', started=str(utc), news=0, tips=0)

        if type_ == 'auto':
            action = data['action'] = meta['action']
            mpk = (crawl_table.find_one(sort=[('pk', -1)]) or {'pk': 0})['pk']
            data['pk'] = mpk+1
            data['type'] = 'auto'
            crawl_table.insert_one(data)
        else:
            c = crawl_table.find_one(dict(status='waiting'), sort=[('pk', 1)])
            if c:
                action = c['action']
                data['type'] = 'manual'
                crawl_table.update_one({'_id': c['_id']}, {'$set': data})

        if action:
            with_images = False
            # all news without images
            if with_images:
                query = {'$and': [{'image1_filename': {'$exists': True}},
                                  {'image1_filename': {'$ne': ''}}]}
            else:
                query = {}
            seen_news_pk = g.mongo_db.dvoznak_news.find(
                query, sort=[('pk', 1)]).distinct('pk')
            seen_news_str = ','.join(str(pk) for pk in seen_news_pk)
            env = dict(NEWS_TO_SKIP=seen_news_str, STARTTIME=data['started'],
                       WITH_IMAGES=0, DOWNLOAD_DELAY=30,
                       LOG_LEVEL=SPIDER_LOG_LEVEL)

        return jsonify(okay=True, action=action, env=env, meta=my_meta)
    except Exception as err:
        return jsonify(okay=False, error=repr(err), meta=my_meta)


@app.route('/api/spider/results', methods=['POST'])
def api_spider_results():
    utc = str(datetime.utcnow().replace(microsecond=0))
    my_meta = dict(utc=str(utc), rand=str(random.randint(1, 99)))
    digest = '|'.join([str(my_meta[key]) for key in sorted(my_meta.keys())])
    my_meta['digest'] = hashlib.sha1(digest + SECRET_KEY).hexdigest()

    try:
        res = request.json
        meta = res['meta']
        ref_digest = meta.pop('digest', '')
        digest = '|'.join([str(meta[key]) for key in sorted(meta.keys())])
        assert hashlib.sha1(digest + SECRET_KEY).hexdigest() == ref_digest, \
            'Invalid digest'

        num = dict(tips=0, news=0)
        action = meta.get('action', '') or 'unnamed'
        status = res.get('status', 'unknown')

        for name in ('tips', 'news'):
            data_table = g.mongo_db['dvoznak_%s' % name]
            pk_set = set()
            for item in res.get(name, []):
                for date in ('crawled', 'updated', 'published'):
                    if date in item:
                        if item[date]:
                            item[date] = datetime.strptime(
                                item[date], '%Y-%m-%d %H:%M:%S')
                        else:
                            item[date] = None
                can_insert = ('url' in item or 'details_url' in item)
                item['archived'] = 'fresh'
                data_table.update_one({'pk': item['pk']}, {'$set': item},
                                      upsert=can_insert)
                pk_set.add(item['pk'])
                num[name] += 1
            if num[name] > 1:
                data_table.update_many({'pk': {'$nin': sorted(pk_set)}},
                                       {'$set': {'archived': 'archived'}})

        crawl_table = g.mongo_db.dvoznak_crawls
        query = dict(host=meta['host'], action=action,
                     started=str(meta['starttime']))
        updater = dict(ipaddr=meta['ipaddr'], pid=meta['pid'], status=status)
        counts = dict(news=num['news'], tips=num['tips'])
        ops = {'$set': updater}
        if status == 'partial':
            ops['$inc'] = counts
        else:
            updater.update(counts)
            updater['ended'] = datetime.utcnow().replace(microsecond=0)
        result = crawl_table.update_one(query, ops)

        if result.matched_count == 0:
            mpk = (crawl_table.find_one(sort=[('pk', -1)]) or {'pk': 0})['pk']
            insert = dict(pk=mpk+1)
            insert.update(query)
            insert.update(updater)
            insert.update(counts)
            insert['type'] = 'auto'
            crawl_table.insert_one(insert)

        return jsonify(okay=True, meta=my_meta)
    except Exception as err:
        app.logger.info('Invalid message from spider: %s', err)
        return jsonify(okay=False, error=repr(err), meta=my_meta)


class UsersForm(form.Form):
    username = fields.StringField('Username')
    password = fields.StringField('Password')
    is_admin = fields.BooleanField('Is Administrator')


class UsersView(PyMongoModelView):
    form = UsersForm
    can_create = can_edit = can_delete = True
    create_modal = edit_modal = True
    can_export = False

    column_list = ['username', 'is_admin']
    column_sortable_list = column_list
    column_searchable_list = ['username']
    column_default_sort = 'username'
    column_labels = dict(username='Username', is_admin='Is Administrator')

    def is_accessible(self):
        return getattr(current_user, 'is_admin', False)


class User(UserMixin):
    def __init__(self, userdic=None):
        userdic = userdic or {}
        self.username = userdic.get('username', '')
        self.password = userdic.get('password', '')
        self.is_admin = bool(userdic.get('is_admin', False))

    def get_id(self):
        return self.username


class LoginForm(form.Form):
    username = fields.TextField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

    def validate_password(self, field):
        user = self.get_user()
        if user is not None and user.password == self.password.data:
            return
        message = 'Invalid username or password'
        flash(message, category='error')
        raise validators.ValidationError(message)

    def get_user(self):
        return load_user(self.username.data)


class AppIndexView(AdminIndexView):

    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        return super(AppIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        form = LoginForm(request.form)
        if validate_form_on_submit(form):
            user = form.get_user()
            login_user(user)
        if current_user.is_authenticated:
            return redirect(url_for('.index'))
        return self.render('login_view.html', form=form)

    @expose('/logout/')
    def logout_view(self):
        logout_user()
        return redirect(url_for('.index'))


admin = Admin(app, name='DZ', index_view=AppIndexView(),
              base_template='app_master.html', template_mode='bootstrap3')

mongo_db = MongoClient(app.config['MONGODB_URL']).get_default_database()

admin.add_view(NewsView(mongo_db.dvoznak_news,
                        'News', endpoint='news'))
admin.add_view(TipsView(mongo_db.dvoznak_tips,
                        'Tips', endpoint='tips'))
admin.add_view(CrawlsView(mongo_db.dvoznak_crawls,
                          'Crawls', endpoint='crawls'))
admin.add_view(UsersView(mongo_db.dvoznak_users,
                         'Users', endpoint='users'))


@app.before_request
def before_request():
    g.user = current_user
    g.mongo_db = mongo_db


@logman.user_loader
def load_user(unicode_uid):
    username = unicode_uid

    userdic = g.mongo_db.dvoznak_users.find_one({'username': unicode_uid})
    if not userdic and username == 'admin':
        userdic = dict(username='admin', password='admin', is_admin=True)
    return User(userdic) if userdic else None


@app.route('/')
def index():
    return redirect('/admin/')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, use_reloader=False)
