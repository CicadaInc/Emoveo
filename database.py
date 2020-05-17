from log import logger, log_object
from settings import *

import os
from typing import Union, Iterable, Tuple
import sqlite3 as sql


class DB:
    """Связующий класс для работы с базой данных"""

    def __init__(self):
        if not os.path.isdir(MEDIA_PATH):
            os.mkdir(MEDIA_PATH)
        if not os.path.isdir(MEDIA_AUTONAME_ADD_PATH):
            os.mkdir(MEDIA_AUTONAME_ADD_PATH)

        self.con = sql.connect(DB_PATH)
        self._cursor = None
        self.con.row_factory = sql.Row
        self.con.execute("CREATE TABLE IF NOT EXISTS Media "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, "
                         "type TEXT, "
                         "path TEXT)")
        self.con.execute("CREATE TABLE IF NOT EXISTS Questions "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, "
                         "text TEXT, "
                         "type TEXT DEFAULT text, "
                         "correct INTEGER DEFAULT 0, "
                         "variants TEXT, "
                         "media INTEGER DEFAULT NULL)")
        self.con.commit()

    @property
    def cursor(self):
        if not self._cursor:
            self._cursor = self.con.cursor()
        return self._cursor

    @cursor.deleter
    def cursor(self):
        if self._cursor:
            self._cursor.close()
            self._cursor = None

    def get_table_list(self):
        """Список всех таблиц в базе данных"""
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")
        res = self.cursor.fetchall()
        del self.cursor
        return [e[0] for e in res]

    @staticmethod
    def auto_media_name():
        return max(map(
            lambda e:
            int(e.split('.')[0])
            if e.rsplit('.', 1)[0].isdigit() and os.path.isfile(os.path.join(MEDIA_PATH, e))
            else 0,
            os.listdir(MEDIA_PATH)
        )) + 1

    def add_media(self, path, force_type=None):
        """
        Добавление медиа файла.
        Путь указывается относительно
        MEDIA_AUTONAME_ADD_PATH для автоматического присвоения имени файла и перемещения в папку MEDIA_PATH,
        MEDIA_PATH для добавления под старым именем.
        """
        path = os.path.normcase(os.path.normpath(path))
        ext = '.' + path.rsplit('.', 1)[-1].lower()

        for type, formats in MEDIA_FORMAT.items():
            if ext in formats:
                break
        else:
            type = None
            logger.warn('Unidentified file is about to be added to database "%s"\n"%s" extension' % (path, ext))

        if force_type:
            if type and type != force_type:
                logger.warn("Forced file type \"%s\" does not match autodetermined \"%s\"" % (force_type, type))
            else:
                logger.warn("Adding file with forced type \"%s\"" % (force_type,))
            type = force_type

        if os.path.isfile(os.path.join(MEDIA_AUTONAME_ADD_PATH, path)):
            old_path, path = path, str(self.auto_media_name()) + ext
            os.rename(os.path.join(MEDIA_AUTONAME_ADD_PATH, old_path), os.path.join(MEDIA_PATH, path))
        elif os.path.isfile(os.path.join(MEDIA_PATH, path)):
            path = os.path.normcase(os.path.normpath(path))
        else:
            raise FileNotFoundError("Media file not found, database unchanged")

        self.con.execute(
            "INSERT INTO Media (type, path) VALUES (?, ?)",
            (type, os.path.normcase(os.path.normpath(path))))
        self.con.commit()
        return path

    def get_media(self, id):
        self.cursor.execute("SELECT * FROM Media WHERE id = ? LIMIT 1", (id,))
        res = self.cursor.fetchone()
        del self.cursor
        return res

    def find_media(self, media):
        """Найти в базе данных информацию о медиа файле по id или пути относительно папки MEDIA_PATH"""
        if isinstance(media, int) or isinstance(media, str) and media.isdigit():
            return self.get_media(int(media))
        elif os.path.isfile(os.path.join(MEDIA_PATH, media)):
            self.cursor.execute(
                "SELECT * FROM Media WHERE path = ?",
                (os.path.normcase(os.path.normpath(media)),))
            res = self.cursor.fetchone()
            del self.cursor
            return res
        else:
            logger.debug('Can\'t find media file by "%s"' % (media,))
            return None

    def add_question(self, text, variants, type='text', correct=0, media=None):
        """
        Добавление вопроса в базу данных
        variants - список вариантов или разделённые ";" варианты ответов,
        correct - индекс правильного,
        media - id или путь к файлу в базе данных относительно MEDIA_PATH

        Parameters
        ----------
        text : str
            Текст вопроса
        variants : Union[Iterable[str], str]
            Варианты ответа, список или разделённые ";" варианты в одной строке
        type : str
        correct : int
            Индекс правильного
        media : Union[int, str]
            id или путь к файлу в базе данных относительно MEDIA_PATH
        """
        if media:
            media_data = self.find_media(media)
            if not media_data:
                logger.warning("Trying to add question with media. Media not found by \"%s\"" % (media,))
            else:
                media = media_data[0]
        if not isinstance(variants, str):
            variants = ';'.join(variants)
        self.con.execute(
            "INSERT INTO Questions (text, type, correct, variants, media) VALUES (?, ?, ?, ?, ?)",
            (text, type, correct, variants, media))
        self.con.commit()

    def get_question(self, id):
        self.cursor.execute("SELECT * FROM Questions WHERE id = ? LIMIT 1", (id,))
        res = self.cursor.fetchone()
        del self.cursor
        return res

    def get_question_ids(self, n=50, types=None):
        """
        Получение id вопросов для теста.
        """
        if not types:
            self.cursor.execute(
                "SELECT id FROM Questions ORDER BY RANDOM() LIMIT ?",
                (n,))
        else:
            logger.debug(
                "SELECT id FROM Questions WHERE type IN "
                "(%s) "
                "ORDER BY RANDOM() LIMIT ?)" % ('?, ' * (len(types) - 1) + '?',))
            logger.debug(list(types) + [n])
            self.cursor.execute(
                "SELECT id FROM Questions WHERE type IN "
                "(%s) "
                "ORDER BY RANDOM() LIMIT ?" % ('?, ' * (len(types) - 1) + '?',),
                list(types) + [n])
        res = self.cursor.fetchall()
        del self.cursor
        return [e[0] for e in res]

    def __del__(self):
        self.con.commit()
        self.con.close()
