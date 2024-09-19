import os
from sqlalchemy import text
from flask import Flask
from sqlalchemy import create_engine
from flask_sqlalchemy import SQLAlchemy
import util.logger as log
from dotenv import load_dotenv
import pdb

load_dotenv(override=True)
app = Flask(__name__)
db = None
env = os.environ.get("ENV")

user = os.getenv("DATABASE_USER")
password = os.getenv("DATABASE_PASSWORD")
hostname = os.getenv("DB_HOSTNAME")

port = os.getenv("DATABASE_PORT")
database_name = os.getenv("DATABASE_NAME")
database_schema = os.environ.get('DATABASE_SCHEMA')
debug = os.environ.get('DATA_DEBUG')
if debug == 'True' or debug == 'False':
    debug = eval(debug)

if database_name != None and user != None and password != None and hostname != None and port != None and database_schema != None and debug != None:
    app.config['DEBUG'] = debug
    app.config['SQLALCHEMY_ECHO'] = debug
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{user}:{password}@{hostname}:{port}/{database_name}?options=-csearch_path%3Ddbo,{database_schema}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    SQLALCHEMY_POOL_RECYCLE = 35  # value less than backend’s timeout
    SQLALCHEMY_POOL_TIMEOUT = 7  # value less than backend’s timeout
    SQLALCHEMY_PRE_PING = True
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': SQLALCHEMY_POOL_RECYCLE,
                                                'pool_timeout': SQLALCHEMY_POOL_TIMEOUT,
                                                'pool_pre_ping': SQLALCHEMY_PRE_PING,
                                                'pool_pre_ping': SQLALCHEMY_PRE_PING,
                                                'insertmanyvalues_page_size' : 1000}
    db = SQLAlchemy(app)
else:
    log.error(
        f'\n____Error____: Environ variables [ DATA_INGEST_USER, DATA_INGEST_PASSWORD, DEV_or_PROD_DATABASE_HOSTNAME, DATABASE_PORT, DATABASE_NAME, DATABASE_SCHEMA ] does not exist')
    exit()

def insert_engine():
    return db.engine

app.app_context().push()
db.create_all()

with db.engine.connect() as conn:
    try:
        result = conn.scalar(text('SELECT 1'))
        log.message(f'Connection to DB: {database_name} @ {hostname}:{port} successful !!!!')
        conn.close()
    except Exception as e:
        log.error('\n----------- Connection failed !!!! ERROR : ',
                  e, ' -----------')
        exit()
