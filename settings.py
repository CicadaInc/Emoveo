from logging import DEBUG
import time
import traceback
import sys
import os

LOAD_RELATIVE = False
LOAD_MEIPASS = True


class PATH:
    EXECUTABLE = os.getcwd()
    RELATIVE = '.'
    MEIPASS = getattr(sys, '_MEIPASS', EXECUTABLE)
    ENGINE = os.path.dirname(os.path.abspath(__file__))
    WRITE = EXECUTABLE
    LOAD = RELATIVE if LOAD_RELATIVE else (MEIPASS if LOAD_MEIPASS and getattr(sys, 'frozen', False) else EXECUTABLE)


def get_path(path):
    return os.path.join(PATH.LOAD, path)


# def get_write_path(path):
#     return os.path.join(PATH.WRITE, path)


LOG_PATH_RELATIVE = 'Logs'
MEDIA_PATH_RELATIVE = 'Media'
MEDIA_AUTONAME_ADD_PATH_RELATIVE = os.path.join(MEDIA_PATH_RELATIVE, 'AUTONAME ADD')
DB_PATH_RELATIVE = 'database.db'

LOG_PATH = get_path(LOG_PATH_RELATIVE)
MEDIA_PATH = get_path(MEDIA_PATH_RELATIVE)
MEDIA_AUTONAME_ADD_PATH = get_path(MEDIA_AUTONAME_ADD_PATH_RELATIVE)
DB_PATH = get_path(DB_PATH_RELATIVE)

LOG_LEVEL = DEBUG
LOG_FILE_PATTERN = "{day}.{month}.{year} {hour}.{min} {sec}"

MEDIA_FORMAT = {'image': {'.jpg', '.png', '.jpeg'}, 'video': {'.mp4', '.mkv', '.avi'}}

EXCEPTION_FILE = None


def except_hook(cls, exception, c_traceback):
    if not getattr(sys, 'frozen', False):
        sys.__excepthook__(cls, exception, c_traceback)
    if EXCEPTION_FILE:
        with open(get_write_path(EXCEPTION_FILE),
                  mode='a') as error_file:
            error_file.write('\n' + time.asctime() + '\n')
            error_file.write(str(time.time()) + ' SSTE\n')
            error_file.write(str(cls) + '\n')
            error_file.write(str(exception) + '\n')
            error_file.write(''.join(traceback.format_tb(c_traceback)) + '\n')
