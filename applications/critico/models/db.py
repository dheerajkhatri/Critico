# -*- coding: utf-8 -*-

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    db = DAL('sqlite://storage.sqlite',pool_size=1,check_reserved=['all'])
else:
    ## connect to Google BigTable (optional 'google:datastore://namespace')
    db = DAL('google:datastore+ndb')
    ## store sessions and tickets there
    session.connect(request, response, db=db)
    ## or store session in Memcache, Redis, etc.
    ## from gluon.contrib.memdb import MEMDB
    ## from google.appengine.api.memcache import Client
    ## session.connect(request, response, db = MEMDB(Client()))

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []

## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'
## (optional) static assets folder versioning
# response.static_version = '0.0.0'
#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Auth, Service, PluginManager

auth = Auth(db)
service = Service()
plugins = PluginManager()

## create all tables needed by auth if not custom tables

## ------------------------------
## Adding more fields to auth
## ------------------------------
auth.settings.extra_fields[auth.settings.table_user_name] = [
                                                            Field('user_type', requires=[IS_NOT_EMPTY(), IS_IN_SET(['a', 'b'])], readable=False, writable=False),
                                                            Field('gender', requires=[IS_EMPTY_OR(IS_IN_SET(['Male', 'Female', 'Other']))], widget=SQLFORM.widgets.radio.widget),
                                                            Field('date_of_birth', type='date', requires=[IS_EMPTY_OR(IS_DATE())], widget=SQLFORM.widgets.date.widget),
                                                            Field('country', requires=[IS_ALPHANUMERIC()], length=32, default=''),
                                                            Field('state_', requires=[IS_ALPHANUMERIC()], length=32, default=''),
                                                            Field('city', requires=[IS_ALPHANUMERIC()], length=32, default=''),
                                                            Field('display_picture_name', 'upload', uploadfield='display_picture_blob'),
                                                            Field('display_picture_blob', 'blob')]

## -------------------------------
## We require a username
## -------------------------------
auth.define_tables(username=True, signature=False)

## -----------------------------------------
## Configuring auth fields with validations etc.
## -----------------------------------------
## db[auth.settings.table_user_name].password.requires=[IS_STRONG(), CRYPT()]

## ADD RECAPTCHA IF NOT LOCAL
#from gluon.tools import Recaptcha
#if(not request.is_local):
#    auth.settings.captcha = Recaptcha(request, 'PUBLIC_KEY', 'PRIVATE_KEY')

## -------------------------------------
## Configurations end here
## -------------------------------------

## configure email
mail = auth.settings.mailer
mail.settings.server = 'logging' if request.is_local else 'smtp.gmail.com:587'
mail.settings.sender = 'you@gmail.com'
mail.settings.login = 'username:password'

## configure auth policy
auth.settings.registration_requires_verification = True
auth.settings.login_after_registration = False
auth.settings.registration_requires_approval = True ## Automatically approve if it's a user of type 'a'
auth.settings.reset_password_requires_verification = True

## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
from gluon.contrib.login_methods.janrain_account import use_janrain
use_janrain(auth, filename='private/janrain.key')

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)

MAX_RATING=11
MAX_VOTING=2
aspects = ['comedy', 'action', 'romance', 'drama', 'mystery']

## PRODUCT DATABASE
db.define_table('product',
                Field('admin_ref', type='reference auth_user', requires=[IS_NOT_EMPTY()], readable=False, writable=False, default=auth.user_id),
                Field('name', type='string', requires=[IS_NOT_IN_DB(db, 'product.name')], default=str(auth.user_id)),
                Field('display_picture_name', 'upload', uploadfield='display_picture_blob'),
                Field('display_picture_blob', 'blob'),
                Field('users_rated', type='list:integer', readable=False, writable=False),
                Field('users_rating', type='list:integer', readable=False, writable=False, requires=[IS_LIST_OF(IS_INT_IN_RANGE(1,MAX_RATING))]),
                Field('aspects_score', type='list:integer', readable=True, writable=False, default=[1 for a in aspects], represent=lambda x, record: plugin_wiki.widget('pie_chart',data=x, names=aspects, width=500,height=150,align='left')))

## EDITION DATABASE
db.define_table('edition',
                Field('product_ref', type='reference product', writable=False, readable=False),
                Field('name', default='Edition Name'),
                Field('number_', type='integer', requires=[IS_NOT_EMPTY(), IS_INT_IN_RANGE(1, 1e100)], default=1),
                Field('date_of_release', type='date', requires=[IS_EMPTY_OR(IS_DATE())], widget=SQLFORM.widgets.date.widget, default=request.now),
                Field('description', type='text', requires=[IS_NOT_EMPTY()], default='Description of Edition'),
                Field('display_picture_name', 'upload', uploadfield='display_picture_blob'),
                Field('display_picture_blob', 'blob'),
                Field('users_rated', type='list:integer', readable=False, writable=False),
                Field('users_rating', type='list:integer', readable=False, writable=False, requires=[IS_LIST_OF(IS_INT_IN_RANGE(1,MAX_RATING))]))

## SUB_EDITION DATABASE
db.define_table('sub_edition',
                Field('product_ref', type='reference product', writable=False, readable=False),
                Field('edition_ref', type='reference edition', writable=False, readable=False),
                Field('name', default='Sub Edition Name'),
                Field('number_', type='integer', requires=[IS_NOT_EMPTY(), IS_INT_IN_RANGE(1, 1e100)], default=1),
                Field('date_of_release', type='date', requires=[IS_EMPTY_OR(IS_DATE())], widget=SQLFORM.widgets.date.widget, default=request.now),
                Field('description', type='text', requires=[IS_NOT_EMPTY()], default='Description of Sub Edition'),
                Field('display_picture_name', 'upload', uploadfield='display_picture_blob'),
                Field('display_picture_blob', 'blob'),
                Field('users_rated', type='list:integer', readable=False, writable=False),
                Field('users_rating', type='list:integer', readable=False, writable=False, requires=[IS_LIST_OF(IS_INT_IN_RANGE(1,MAX_RATING))]))

## CONTRIBUTOR DATABASE
db.define_table('contributor',
                Field('product_ref', type='reference product', writable=False, readable=False),
                Field('real_name', requires=[IS_NOT_EMPTY()], default='Real Name'),
                Field('character_name', default='Character Name'),
                Field('role', default='Role'),
                Field('url', requires=[IS_EMPTY_OR(IS_URL())], represent=lambda x, record: A('url', _target = "_blank", _href = x)),
                Field('display_picture_name', 'upload', uploadfield='display_picture_blob'),
                Field('display_picture_blob', 'blob'))

## REVIEW DATABASE
db.define_table('review',
                Field('user_ref',type='reference auth_user', writable=False, readable=False, default=auth.user_id),
                Field('for_type', requires=[IS_NOT_EMPTY(), IS_IN_SET(['product', 'edition', 'sub_edition', 'reply'])], writable=False, readable=False),
                Field('product_ref', type='reference product', writable=False, readable=False),
                Field('edition_ref', type='reference edition', writable=False, readable=False),
                Field('sub_edition_ref', type='reference sub_edition', writable=False, readable=False),
                Field('review_ref', type='reference review', writable=False, readable=False),
                Field('title', requires=[IS_NOT_EMPTY()], default='my title'),
                Field('timestamp_', type='datetime', requires=[IS_NOT_EMPTY()], default=request.now, update=request.now, writable=False),
                Field('edited', type='boolean', requires=[IS_NOT_EMPTY()], default=False, update=True, writable=False, readable=False),
                Field('description', type='text', requires=[IS_NOT_EMPTY()], default='my review'),
                Field('users_rated', type='list:integer', readable=False, writable=False),
                Field('users_rating', type='list:integer', readable=False, writable=False, requires=[IS_LIST_OF(IS_INT_IN_RANGE(-1,MAX_VOTING))]),
                Field('analyzed', type='boolean', writable=False, readable=False, default=False))

## NEWS DATABASE
db.define_table('news',
                Field('product_ref', type='reference product', writable=False, readable=False),
                Field('title', requires=[IS_NOT_EMPTY()], default='news title'),
                Field('timestamp_', type='datetime', default=request.now, update=request.now, writable=False),
                Field('description', type='text', requires=[IS_NOT_EMPTY()], default='news description'),
                Field('url', requires=[IS_EMPTY_OR(IS_URL())], represent=lambda x, record: A('url', _target = "_blank", _href = x)),
                Field('display_picture_name', 'upload', uploadfield='display_picture_blob'),
                Field('display_picture_blob', 'blob'))


## VIDEO DATABSE
db.define_table('video',
                Field('for_type', requires=[IS_IN_SET('product', 'edition', 'sub_edition'), IS_NOT_EMPTY()], writable=False, readable=False),
                Field('product_ref', type='reference product', requires=[IS_NOT_EMPTY()], writable=False, readable=False),
                Field('edition_ref', type='reference edition', requires=[IS_NOT_EMPTY()], writable=False, readable=False),
                Field('sub_edition_ref', type='reference sub_edition', requires=[IS_NOT_EMPTY()], writable=False, readable=False),
                Field('name', requires=[IS_NOT_EMPTY()]),
                Field('url', requires=[IS_NOT_EMPTY(), IS_URL()], represent=lambda x, record: plugin_wiki.widget('youtube',code=x.split('/')[-1])))
