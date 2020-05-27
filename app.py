from testing import Test, db, CustomizableTest, Question
from log import logger
from settings import *

from PyQt5 import QtCore, QtWidgets, QtGui, QtMultimedia, QtMultimediaWidgets, uic
from typing import List, Union
import sys
import random


class Main:

    def __init__(self, app: QtWidgets.QApplication = None):
        if app is None:
            app = QtWidgets.QApplication(sys.argv)
            app.setApplicationName(APP_NAME)
            app.setOrganizationName(ORG_NAME)
        self.app = app

        self.main_window = QtWidgets.QMainWindow()
        self.main_window.setWindowTitle(APP_NAME)
        self.main_window.setGeometry(300, 300, 300, 300)
        self.main_window.setMinimumSize(300, 300)

        self.stack = QtWidgets.QStackedWidget()
        self.main_window.setCentralWidget(self.stack)

        self.main_menu = MainMenu(self)
        self.tutorial_tab = TutorialTab(self)
        self.training_tab = TrainingTab(self)
        self.question_tab = QuestionTab(self)
        self.stats_tab = StatsTab(self)

        self.stack.addWidget(self.main_menu)
        self.stack.addWidget(self.tutorial_tab)
        self.stack.addWidget(self.training_tab)
        self.stack.addWidget(self.question_tab)
        self.stack.addWidget(self.stats_tab)
        self.stack.setCurrentWidget(self.main_menu)

        self.history = []

    def back(self):
        if self.history:
            self._set_tab(self.history.pop(-1))

    def get_tab(self):
        return self.stack.currentWidget()

    def _set_tab(self, widget: QtWidgets.QWidget):
        self.stack.setCurrentWidget(widget)

    def set_tab(self, widget: QtWidgets.QWidget):
        if widget is not self.get_tab():
            self.history.append(self.get_tab())
            self._set_tab(widget)

    def start(self):
        self.main_window.show()

    def exit(self):
        sys.exit(self.app.exec())


class Tab(QtWidgets.QWidget):

    def __init__(self, main: Main, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main = main
        self.setupUi(self)


class MainMenu(Tab, uic.loadUiType(get_path("UI\\MainMenu.ui"))[0]):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tutorial_button.clicked.connect(
            lambda: self.main.set_tab(self.main.tutorial_tab)
        )
        self.training_button.clicked.connect(
            lambda: self.main.set_tab(self.main.training_tab)
        )


class TutorialTab(Tab, uic.loadUiType(get_path('UI\\TutorialTab.ui'))[0]):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image.setPixmap(QtGui.QPixmap(get_media_path(db.find_media('emotions.jpg')['path'])))
        self.back_button.clicked.connect(self.main.back)


class TrainingTab(Tab, uic.loadUiType(get_path("UI\\TrainingTab.ui"))[0]):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maximum = 0

        self.back_button.clicked.connect(self.main.back)
        self.start_button.clicked.connect(self.start_test)

        self.count_box.valueChanged.connect(self.count_slider.setValue)
        self.count_box.valueChanged.connect(lambda n: self.start_button.setDisabled(n < 1))

        self.count_slider.valueChanged.connect(self.count_box.setValue)

        db.cursor.execute("SELECT DISTINCT type FROM Questions")
        self.types = [e[0] for e in db.fetchall()]
        for type in self.types:
            checkbox = QtWidgets.QCheckBox()
            checkbox.setStyle(self.type_checkbox.style())
            checkbox.setText(type)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(
                lambda allowed, type=type: self.types.append(type) if allowed else self.types.remove(type)
            )
            checkbox.stateChanged.connect(self.update_count_menu)
            self.type_menu.layout().addWidget(checkbox)

        db.cursor.execute("SELECT DISTINCT difficulty FROM Questions WHERE difficulty > 0")
        self.difficulty = [e[0] for e in db.fetchall()]
        for difficulty in self.difficulty:
            checkbox = QtWidgets.QCheckBox()
            checkbox.setStyle(self.difficulty_checkbox.style())
            checkbox.setText(str(difficulty))
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(
                lambda allowed, difficulty=difficulty:
                self.difficulty.append(difficulty) if allowed else self.difficulty.remove(difficulty)
            )
            checkbox.stateChanged.connect(self.update_count_menu)
            self.difficulty_menu.layout().addWidget(checkbox)

        self.count_box.setValue(25)
        self.update_count_menu()

        self.type_checkbox.hide()
        self.difficulty_checkbox.hide()

    def update_count_menu(self):
        db.cursor.execute(
            "SELECT COUNT(*) FROM Questions WHERE type IN (%s) AND difficulty IN (%s)" %
            (', '.join('?' for _ in self.types), ', '.join('?' for _ in self.difficulty)),
            self.types + self.difficulty
        )
        self.maximum = db.fetchone()[0]
        self.count_box.setMaximum(self.maximum)
        self.count_box.setValue(min(self.count_box.value(), self.maximum))

        self.count_slider.setMaximum(min(100, self.maximum))

    def start_test(self):
        self.main.question_tab.test = CustomizableTest(n=self.count_box.value(),
                                                       type=self.types,
                                                       difficulty=self.difficulty)
        self.main.set_tab(self.main.question_tab)


class QuestionTab(Tab, uic.loadUiType(get_path("UI\\QuestionTab.ui"))[0]):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._test = None
        self._question = None
        self.answer_widgets: List[QtWidgets.QWidget] = []

        video_label = VideoPlayer()
        video_label.setStyle(self.video_label.style())
        self.video_label.parent().layout().replaceWidget(self.video_label, video_label)
        self.video_label.deleteLater()
        self.video_label = video_label

        self.image_group.layout().addWidget(self.image_label)

        self.video_group.hide()
        self.image_group.hide()
        self.text_group.hide()

        self.end_button.clicked.connect(self.end_test)
        self.skip_button.clicked.connect(self.skip)
        self.next_button.clicked.connect(self.next)
        self.next_button.setDisabled(True)

        self.answer_button.hide()

    def answer(self, n: int):
        for i in self.answer_widgets:
            i.setDisabled(True)
        if not self.test.answer(n):
            self.answer_widgets[n].setStyleSheet("background-color: red")
        self.answer_widgets[self.question.correct].setStyleSheet("background-color: green")
        self.skip_button.setDisabled(True)
        self.next_button.setDisabled(False)

    def next(self):
        if self.test:
            self.test.next()
            if not self.test.completed:
                self.question = self.test.question
            else:
                self.complete()
        else:
            raise RuntimeError("Test is not set")

    def skip(self):
        if self.test:
            m_box = QtWidgets.QMessageBox
            m_box.question(self, "Подтверждение", "Вы уверены, что хотите пропустить вопрос?",
                           m_box.Yes | m_box.No)
            if m_box.Yes:
                self.test.skip()
                if not self.test.completed:
                    self.question = self.test.question
                else:
                    self.complete()
        else:
            raise RuntimeError("Test is not set")

    def end_test(self):
        """
        Преждевременное завершение
        """
        m_box = QtWidgets.QMessageBox
        m_box.question(self, "Подтверждение", "Вы уверены, что хотите завершить тест?",
                       m_box.Yes | m_box.No)
        if m_box.Yes:
            self.complete()

    def complete(self):
        self.main.stats_tab.stats = self.test.stats
        self.main.set_tab(self.main.stats_tab)

    @property
    def test(self) -> Test:
        return self._test

    @test.setter
    def test(self, test_obj: Test):
        self._test = test_obj
        self.question = test_obj.question

    @property
    def question(self) -> Question:
        return self._question

    @question.setter
    def question(self, question_obj: Question):
        self._question = question_obj

        self.skip_button.setDisabled(False)
        self.next_button.setDisabled(True)

        self.text = question_obj.text
        if question_obj.media:
            media_type = question_obj.media['type']
            if media_type == 'video':
                del self.image
                self.video = get_media_path(question_obj.media['path'])
            elif media_type == 'image':
                self.image = get_media_path(question_obj.media['path'])
                del self.video
            else:
                logger.warning("Unrecognized media type in question %d" % (question_obj.id,))
        else:
            del self.image
            del self.video

        for i in self.answer_widgets:
            i.deleteLater()
        self.answer_widgets.clear()
        for n, text in enumerate(question_obj.variants):
            var = QtWidgets.QPushButton()
            var.setStyle(self.answer_button.style())
            var.setText(text)
            var.clicked.connect(lambda *args, n=n: self.answer(n))
            self.answer_widgets.append(var)
        for i in random.sample(self.answer_widgets, len(self.answer_widgets)):
            self.answer_group.layout().addWidget(i)

    @property
    def image(self) -> QtGui.QPixmap:
        return self.image_label.pixmap()

    @image.setter
    def image(self, path: str):
        if path and os.path.isfile(path):
            self.image_label.setPixmap(QtGui.QPixmap(path))
            self.image_group.show()
        else:
            raise FileNotFoundError("File not found \"%s\"" % (path,))

    @image.deleter
    def image(self):
        self.image_label.clear()
        self.image_group.hide()

    @property
    def text(self) -> str:
        return self.text_label.text()

    @text.setter
    def text(self, txt: str):
        if txt:
            self.text_label.setText(txt)
            self.text_group.show()
        else:
            del self.text

    @text.deleter
    def text(self):
        self.text_label.clear()
        self.text_group.hide()

    @property
    def video(self):
        return self.video_label.video

    @video.setter
    def video(self, path: str):
        self.video_label.video = path
        self.video_group.show()

    @video.deleter
    def video(self):
        del self.video_player.video
        self.video_group.hide()


class StatsTab(Tab, uic.loadUiType(get_path("UI\\StatsTab.ui"))[0]):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stats = {}
        self.patterns = {
            'total': "Total {total}",
            'correct': "Correct: {correct} {correct_percent:.2f}%",
            'skipped': "Skipped: {skipped} {skipped_percent:.2f}%",
            'incorrect': "Incorrect: {incorrect} {incorrect_percent:.2f}%"
        }
        self.stat_widgets = {
            'total': self.total_label,
            'correct': self.correct_label,
            'skipped': self.skipped_label,
            'incorrect': self.incorrect_label
        }

        self.back_button.clicked.connect(lambda: self.main.set_tab(self.main.main_menu))

    @property
    def stats(self):
        return self._stats

    @stats.setter
    def stats(self, st: dict):
        self._stats = st.copy()
        total = self._stats.get('total', 0)
        self._stats['correct_percent'] = (self._stats.get('correct', 0) / total * 100) if total else 0
        self._stats['skipped_percent'] = (self._stats.get('skipped', 0) / total * 100) if total else 0
        self._stats['incorrect_percent'] = (self._stats.get('incorrect', 0) / total * 100) if total else 0
        for k, v in self.stat_widgets.items():
            v.setText(self.patterns[k].format(**self._stats))


class VideoPlayer(QtWidgets.QWidget, uic.loadUiType(get_path("UI\\VideoPlayer.ui"))[0]):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        video_widget = QtMultimediaWidgets.QVideoWidget()
        video_widget.setStyle(self.video_widget.style())
        self.video_widget.parent().layout().replaceWidget(self.video_widget, video_widget)
        self.video_widget.deleteLater()
        self.video_widget = video_widget

        self.video_player = QtMultimedia.QMediaPlayer(None,
                                                      QtMultimedia.QMediaPlayer.VideoSurface)
        self.video_player.error.connect(self.error)
        self.video_player.stateChanged.connect(self.media_state_changed)

        self.video_player.setVideoOutput(self.video_widget)

        self.play_button.clicked.connect(self.play)

        self.video_slider.sliderMoved.connect(self.video_player.setPosition)
        self.video_player.durationChanged.connect(self.video_slider.setMaximum)
        self.video_player.positionChanged.connect(self.video_slider.setValue)

    @property
    def video(self):
        return self.video_player.media()

    @video.setter
    def video(self, path: Union[str, QtMultimedia.QMediaContent]):
        if isinstance(path, str) and path and os.path.isfile(path):
            self.video_player.setMedia(
                QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(path))
            )
        elif isinstance(path, QtMultimedia.QMediaContent):
            self.video_player.setMedia(path)
        else:
            raise FileNotFoundError("File not found \"%s\"" % (path,))

    @video.deleter
    def video(self):
        self.video_player.setMedia(QtMultimedia.QMediaContent())

    def play(self):
        if self.video_player.state() == QtMultimedia.QMediaPlayer.PlayingState:
            self.video_player.pause()
        else:
            self.video_player.play()

    def media_state_changed(self, state):
        if state == QtMultimedia.QMediaPlayer.PlayingState:
            self.play_button.setText("Pause")
        elif state == QtMultimedia.QMediaPlayer.StoppedState:
            # В StoppedState перемотка происходит без "превью"
            self.video_player.pause()
            self.play_button.setText("Play")
        else:
            self.play_button.setText("Play")

    def error(self, code):
        codes = ['NoError', 'ResourceError', 'FormatError',
                 'NetworkError', 'AccessDeniedError', 'ServiceMissingError']
        request = self.video_player.media().request()
        logger.error("MediaPlayer error: " +
                     codes[code] + " " +
                     str(request.url()))
        del self.video
        self.video = QtMultimedia.QMediaContent(request)


if __name__ == '__main__':
    main = Main()
    main.start()
    main.exit()
