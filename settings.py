from logging import DEBUG
import os

LOG_PATH = 'Logs'
LOG_LEVEL = DEBUG
LOG_FILE_PATTERN = "{day}.{month}.{year} {hour}.{min} {sec}"

DB_PATH = 'database.db'
MEDIA_FORMAT = {'image': {'.jpg', '.png', '.jpeg'}, 'video': {'.mp4', '.mkv', '.avi'}}
MEDIA_PATH = 'Media'
MEDIA_AUTONAME_ADD_PATH = os.path.join(MEDIA_PATH, 'AUTONAME ADD')
