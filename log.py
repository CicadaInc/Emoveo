from settings import *

import time
import os
import logging
import json

FORMATTER = logging.Formatter('%(asctime)s %(name)s:%(levelname)s - %(message)s')

logging.basicConfig()
logger = logging.getLogger()
logger.handlers.clear()
logger.setLevel(LOG_LEVEL)

if not os.path.isdir(PATH.LOG):
    os.mkdir(PATH.LOG)

last_handler = logging.FileHandler(os.path.join(PATH.LOG, 'last.log'), mode='w')
last_handler.setFormatter(FORMATTER)
logger.addHandler(last_handler)

session_time = time.localtime()
form = {
    "day": session_time.tm_mday,
    "month": session_time.tm_mon,
    "year": session_time.tm_year,
    "hour": session_time.tm_hour,
    "min": session_time.tm_min,
    "sec": session_time.tm_sec
}
session_handler = logging.FileHandler(
    os.path.join(PATH.LOG, 'session ' + LOG_FILE_PATTERN.format(**form) + '.log'),
    mode='w')
session_handler.setFormatter(FORMATTER)
logger.addHandler(session_handler)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(FORMATTER)
logger.addHandler(stream_handler)

sys.excepthook = except_hook


class LogEncoder(json.JSONEncoder):
    def encode(self, o):
        try:
            return super().encode(o)
        except TypeError:
            return super().encode(str(o))


def log_object(dct):
    return str(dct)[:15000]


logging.info('LOGGING SET UP')

if __name__ == '__main__':
    def f():
        return None

    logging.info(log_object({'functions': {'a': lambda: None, 'b': lambda: None, 'c': [f, 'слова, функции', {'functions': {'a': lambda: None, 'b': lambda: None, 'c': [f, 'слова, функции', {'functions': {'a': lambda: None, 'b': lambda: None, 'c': [f, 'слова, функции', {'functions': {'a': lambda: None, 'b': lambda: None, 'c': [f, 'слова, функции']}}]}}]}}]}}))
