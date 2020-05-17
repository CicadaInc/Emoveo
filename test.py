from database import DB
from log import logger, log_object

from typing import Union, Tuple

db = DB()


class Test:
    """
    Класс теста для работы со всеми платформами.
    Информация о текущем вопросе хранится в .question
    """

    def __init__(self):
        self.question_ids = []
        self.stats = {'total': 0, 'correct': 0, 'incorrect': 0, 'skipped': 0}
        self.question = None

    @property
    def completed(self):
        return not self.question_ids

    def next(self):
        """Переход к следующему вопросу, не для пропуска"""
        if self.question:
            self.question_ids.remove(self.question.id)
            self.question = None
        if not self.completed:
            self.question = Question.from_id(self.question_ids[0])
            self.stats['total'] += 1

    def skip(self):
        """Пропустить вопрос (Если будет реализовано)"""
        self.stats['skipped'] += 1
        self.next()

    def answer(self, k):
        """
        Ответить на вопрос теста

        Parameters
        ----------
        k : Union[int, str]
            Индекс или текст ответа

        Returns
        -------
        Tuple[bool, int, Question]
            is correct,
            user answer index,
            question object
        """
        if self.question:
            q = self.question
            self.next()
            correct, index = q.answer(k)
            self.stats['correct' if correct else 'incorrect'] += 1
            return correct, index, q
        else:
            raise RuntimeError("Test is already completed")


class CombinedTest(Test):
    """Тест по всем типам вопросов"""

    def __init__(self):
        super().__init__()
        self.question_ids = db.get_question_ids()
        self.next()


class ImageTest(Test):
    """Тест по изображениям"""

    def __init__(self):
        super().__init__()
        self.question_ids = db.get_question_ids(types=['image'])
        self.next()


class Question:

    def __init__(self, id, text, type, correct, variants, media=None):
        self.id = id
        self.text = text
        self.type = type
        self.correct = correct
        self.variants = variants
        self.media = media

    @classmethod
    def from_id(cls, id):
        data = db.get_question(id)
        if not data:
            raise IndexError("Incorrect question id \"%s\"" % (id,))
        return cls(data[0], data[1], data[2],
                   data[3], data[4].split(';'),
                   dict(db.get_media(data[5])) if data[5] else {})

    def answer(self, k):
        """
        Ответить на вопрос

        Parameters
        ----------
        k : Union[int, str]
            Индекс или текст ответа

        Returns
        -------
        Tuple[bool, int]
            is correct,
            user answer index or None
        """
        if isinstance(k, str) and k in self.variants:
            k = self.variants.index(k)
        if isinstance(k, str) or not (0 <= k < len(self.variants)):
            logger.warning(
                'User answer doesn\'t represent any of available variants\n'
                'User: "%s", Variants: "%s", QID: %d' % (k, self.variants, self.id)
            )
            return False, None
        return k == self.correct, k
