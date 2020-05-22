from log import logger, log_object
from settings import *

import os
from typing import Union, Iterable, Tuple, Dict, Any, List, Optional
import sqlite3 as sql


class BaseDB:

    def __init__(self, db_path: str):
        self.con = sql.connect(db_path)
        self._cursor = None
        self.con.row_factory = sql.Row

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

    def fetchall(self):
        res = self.cursor.fetchall()
        del self.cursor
        return res

    def fetchdict(self):
        return [dict(e) for e in self.fetchall()]

    def fetchone(self):
        res = self.cursor.fetchone()
        del self.cursor
        return res

    def get_table_list(self):
        """List of all tables in database"""
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")
        return [e[0] for e in self.fetchall()]

    def get(self,
            table: str,
            select: Union[str, Iterable[str]] = None,
            values: Dict[str, Union[Any, Iterable[Any]]] = None,
            append="") -> List[sql.Row]:
        """
        Get rows from database

        :param table: table name
        :param select: columns to fetch
        :param values: column name: value or iterable of possible values
        :param append: added to end of sql query
        :return: matching rows
        """
        if select is None:
            select = ('*',)
        elif isinstance(select, str):
            select = (select,)
        else:
            select = tuple(select)

        if values:
            sql_values = []
            expanded = []
            for k, v in values.items():
                m = False
                if hasattr(v, '__iter__') and not isinstance(v, str):
                    v = tuple(v)
                    if len(v) > 1:
                        m = True
                    else:
                        v = v[0]
                if m:
                    if None in v:
                        sql_values.append('(%s IN (%s) OR %s IS NULL)' % (k, ', '.join('?' for _ in v), k))
                    else:
                        sql_values.append('%s IN (%s)' % (k, ', '.join('?' for _ in v)))
                    expanded.extend(v)
                else:
                    if v is not None:
                        sql_values.append('%s = ?' % (k,))
                        expanded.append(v)
                    else:
                        sql_values.append('%s IS NULL')
            self.cursor.execute(
                "SELECT %s FROM %s WHERE (%s)"
                % (', '.join(select),
                   table,
                   ' AND '.join(sql_values)) + append,
                expanded)
        else:
            self.cursor.execute(
                "SELECT %s FROM %s" % (', '.join(select), table) + append)

        return self.fetchall()

    def add(self, table: str, values: Union[List[Any], Dict[str, Any]] = None):
        """
        Add row to database

        :param table: Table name
        :param values: values or dict column name: value
        """
        for k, v in values.items():
            if not isinstance(v, str) and hasattr(v, '__iter__'):
                values[k] = ';'.join(v)
        if values:
            if hasattr(values, 'keys'):
                self.con.execute(
                    "INSERT INTO %s (%s) VALUES (%s)"
                    % (table,
                       ', '.join(values.keys()),
                       ', '.join('?' for _ in values)),
                    tuple(values.values()))
            else:
                self.con.execute("INSERT INTO %s VALUES (%s)" % (table, ', '.join('?' for _ in values)),
                                 values)
        else:
            self.con.execute("INSERT INTO %s DEFAULT VALUES" % (table,))
        self.con.commit()

    def __del__(self):
        self.con.commit()
        self.con.close()


class DB(BaseDB):
    """Связующий класс для работы с базой данных"""

    def __init__(self):
        super().__init__(DB_PATH)
        if not os.path.isdir(MEDIA_PATH):
            os.mkdir(MEDIA_PATH)
        if not os.path.isdir(MEDIA_AUTONAME_ADD_PATH):
            os.mkdir(MEDIA_AUTONAME_ADD_PATH)

        self.con.execute("CREATE TABLE IF NOT EXISTS Media "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, "
                         "type TEXT, "
                         "path TEXT, "
                         "difficulty INTEGER DEFAULT 0, "
                         "tags TEXT, "
                         "emotion TEXT)")
        self.con.execute("CREATE TABLE IF NOT EXISTS Questions "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, "
                         "text TEXT, "
                         "type TEXT DEFAULT 'text', "
                         "correct INTEGER DEFAULT 0, "
                         "variants TEXT, "
                         "difficulty INTEGER DEFAULT 0, "
                         "media INTEGER DEFAULT NULL)")
        self.con.commit()

    @staticmethod
    def auto_media_name():
        return max(map(
            lambda e:
            int(e.split('.')[0])
            if e.rsplit('.', 1)[0].isdigit() and os.path.isfile(os.path.join(MEDIA_PATH, e))
            else 0,
            os.listdir(MEDIA_PATH)
        )) + 1

    def add_media(self, path: str, **kwargs):
        """
        Добавление медиа файла.

        :param path: путь относительно
            MEDIA_AUTONAME_ADD_PATH для автоматического присвоения имени файла и перемещения в папку MEDIA_PATH,
            MEDIA_PATH для добавления под старым именем.
        :param kwargs: Значения остальных колонок
        """
        path = os.path.normcase(os.path.normpath(path))
        ext = '.' + path.rsplit('.', 1)[-1].lower()

        for type, formats in MEDIA_FORMAT.items():
            if ext in formats:
                break
        else:
            type = None
            logger.warn('Unidentified file is about to be added to database "%s"\n"%s" extension' % (path, ext))

        force_type = kwargs.get('type', type)
        if type != force_type:
            logger.warning("Forced file type \"%s\" does not match autodetermined \"%s\"" % (force_type, type))
            logger.warning("Adding file with forced type \"%s\"" % (force_type,))
        kwargs['type'] = force_type

        if os.path.isfile(os.path.join(MEDIA_AUTONAME_ADD_PATH, path)):
            old_path, path = path, str(self.auto_media_name()) + ext
            os.rename(os.path.join(MEDIA_AUTONAME_ADD_PATH, old_path), os.path.join(MEDIA_PATH, path))
        elif os.path.isfile(os.path.join(MEDIA_PATH, path)):
            pass
        else:
            raise FileNotFoundError("Media file \"%s\" not found, database unchanged" % (path,))

        # self.con.execute(
        #     "INSERT INTO Media (type, path) VALUES (?, ?)",
        #     (type, os.path.normcase(os.path.normpath(path))))
        # self.con.commit()
        kwargs['path'] = os.path.normcase(os.path.normpath(path))
        self.add('Media', kwargs)
        return path

    def get_media(self, id: int):
        self.cursor.execute("SELECT * FROM Media WHERE id = ? LIMIT 1", (id,))
        res = self.cursor.fetchone()
        del self.cursor
        return res

    def find_media(self, media: Union[int, str]):
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

    def add_question(self,
                     text: str, variants: Union[List[str], str],
                     media: Union[int, str] = None,
                     **kwargs):
        """
        Добавление вопроса в базу данных

        :param text: Текст вопроса
        :param variants: Список вариантов ответа или строка с разделёнными ";" вариантами
        :param media: as .find_media() argument
        :param kwargs: Значения остальных колонок таблицы Questions
        """
        if media:
            media_data = self.find_media(media)
            if not media_data:
                logger.warning("Trying to add question with media. Media not found by \"%s\"" % (media,))
            else:
                media = media_data[0]
        # if not isinstance(variants, str):
        #     variants = ';'.join(variants)
        # self.con.execute(
        #     "INSERT INTO Questions (text, type, correct, variants, media) VALUES (?, ?, ?, ?, ?)",
        #     (text, type, correct, variants, media))
        # self.con.commit()
        kwargs['text'] = text
        kwargs['variants'] = variants
        kwargs['media'] = media
        self.add('Questions', kwargs)

    def get_question(self, id: int):
        self.cursor.execute("SELECT * FROM Questions WHERE id = ? LIMIT 1", (id,))
        res = self.cursor.fetchone()
        del self.cursor
        return res

    def get_question_ids(self, n: int = 50, **kwargs: Union[Any, Iterable[Any]]) -> List[int]:
        """
        Получение id вопросов для теста

        :param n: Количество вопросов
        :param kwargs: as .get() argument
        :return: Список id
        """
        # if not types:
        #     self.cursor.execute(
        #         "SELECT id FROM Questions ORDER BY RANDOM() LIMIT ?",
        #         (n,))
        # else:
        #     self.cursor.execute(
        #         "SELECT id FROM Questions WHERE type IN "
        #         "(%s) "
        #         "ORDER BY RANDOM() LIMIT ?" % ('?, ' * (len(types) - 1) + '?',),
        #         list(types) + [n])
        return [e[0] for e in self.get('Questions',
                                       select='id', values=kwargs,
                                       append=" ORDER BY RANDOM() LIMIT %d" % (n,))]
        # res = self.cursor.fetchall()
        # del self.cursor
        # return [e[0] for e in res]
