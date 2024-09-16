import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

load_dotenv(override=True)
loggerFile = os.environ.get('LOGGING_FILE')

fileDir = Path(str(os.path.abspath(str(loggerFile)))).parent

if not os.path.exists(fileDir):
    os.makedirs(os.path.dirname(loggerFile), exist_ok=True)

_maxBytes = os.environ.get('LOGGING_MAXBYTES')

if (_maxBytes == None):
    _maxBytes = 3698000
else:
    _maxBytes = int(_maxBytes)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

logging.basicConfig(
    handlers=[stream_handler, RotatingFileHandler(
        loggerFile, maxBytes=_maxBytes, backupCount=10)],
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt='%Y-%m-%dT%H:%M:%S')

# Creating an object
log = logging.getLogger()


def message(msg):
    log.info(f'\n----------- {msg} -----------')


def debug(msg):
    log.debug(msg)


def info(msg):
    log.info(msg)


def warning(msg):
    log.warning(msg)


def error(msg):
    log.error(msg)


def critical(msg):
    log.critical(msg, exc_info=True)


def exception(msg):
    log.exception(msg)
