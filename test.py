from database import DB
from log import logger, log_object

from typing import Union, Tuple, Iterable

db = DB()


class Question:

    def __init__(self,
                 id: int,
                 text: str,
                 type: str,
                 correct: int,
                 variants: Iterable[str],
                 media: dict = None):
        self.id = id
        self.text = text
        self.type = type
        self.correct = correct
        self.variants = list(variants)
        self.media = dict(media)

    @classmethod
    def from_id(cls, id: int):
        data = db.get_question(id)
        if not data:
            raise IndexError("Incorrect question id \"%d\"" % (id,))
        return cls(data['id'], data['text'], data['type'],
                   data['correct'], data['variants'].split(';'),
                   dict(db.get_media(data['media'])) if data['media'] else {})

    def answer(self,
               k: Union[int, str]) -> Tuple[bool, Union[int, None]]:
        """
        Ответить на вопрос

        :param k: Индекс или текст ответа
        :return: is correct, user answer as index
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

    def answer(self,
               k: Union[int, str]) -> Tuple[bool, Union[int, None], Question]:
        """
        Ответить на вопрос теста

        :param k: Индекс или текст ответа
        :return: is correct, user answer as index, question object
        """
        if self.question:
            q = self.question
            self.next()
            correct, index = q.answer(k)
            self.stats['correct' if correct else 'incorrect'] += 1
            return correct, index, q
        else:
            raise RuntimeError("Test is already completed")


class CustomizableTest(Test):

    def __init__(self, n=50, **kwargs):
        super().__init__()
        self.question_ids = db.get_question_ids(n=n, **kwargs)


class ImageTest(CustomizableTest):
    """Тест по изображениям"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, type='image', **kwargs)


class VideoTest(CustomizableTest):
    """Тест по видеофайлам"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, type='video', **kwargs)
