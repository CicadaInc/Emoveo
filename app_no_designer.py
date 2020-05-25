from test import *

from settings import *

from PyQt5 import QtCore, QtWidgets, QtGui, QtMultimedia, QtMultimediaWidgets
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


class MainMenu(Tab):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QVBoxLayout(self)

        self.tutorial_button = QtWidgets.QPushButton()
        self.tutorial_button.setText('Обучение')
        self.tutorial_button.clicked.connect(
            lambda: self.main.set_tab(self.main.tutorial_tab)
        )
        layout.addWidget(self.tutorial_button)

        self.training_button = QtWidgets.QPushButton()
        self.training_button.setText('Тренировка')
        self.training_button.clicked.connect(
            lambda: self.main.set_tab(self.main.training_tab)
        )
        layout.addWidget(self.training_button)


class TutorialTab(Tab):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QVBoxLayout(self)

        self.image = QtWidgets.QLabel()
        self.image.setScaledContents(True)
        self.image.setPixmap(QtGui.QPixmap(get_media_path(db.find_media('emotions.jpg')['path'])))

        layout.addWidget(self.image)

        button_layout = QtWidgets.QHBoxLayout()
        self.back_button = QtWidgets.QPushButton()
        self.back_button.setText('Назад')
        self.back_button.clicked.connect(self.main.back)
        button_layout.addStretch(3)
        button_layout.addWidget(self.back_button, 1)
        layout.addLayout(button_layout)


class TrainingTab(Tab):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maximum = 0
        u_layout = QtWidgets.QVBoxLayout(self)

        # Кнопки
        buttons_layout = QtWidgets.QHBoxLayout()

        self.back_button = QtWidgets.QPushButton()
        self.back_button.setText('Назад')
        self.back_button.clicked.connect(self.main.back)
        buttons_layout.addWidget(self.back_button, 1)

        buttons_layout.addStretch(2)

        self.start_button = QtWidgets.QPushButton()
        self.start_button.setText('Начать')
        self.start_button.clicked.connect(self.start_test)
        buttons_layout.addWidget(self.start_button, 1)
        #

        # Настройки
        layout = QtWidgets.QFormLayout()
        # --Настройка количества
        count_menu = QtWidgets.QWidget()
        count_layout = QtWidgets.QHBoxLayout(count_menu)

        self.count_box = QtWidgets.QSpinBox()
        self.count_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)

        self.count_box.setMinimum(0)
        self.count_box.valueChanged.connect(self.count_slider.setValue)
        self.count_box.valueChanged.connect(lambda n: self.start_button.setDisabled(n < 1))
        self.count_box.setMinimumWidth(50)
        self.count_box.setMaximumWidth(150)

        self.count_slider.setMinimum(0)
        self.count_slider.setTickInterval(10)
        self.count_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.count_slider.valueChanged.connect(self.count_box.setValue)

        count_layout.addWidget(self.count_slider, 9)
        count_layout.addWidget(self.count_box, 1)
        # --
        layout.addRow('Количество вопросов', count_menu)
        # --Настройка типов
        db.cursor.execute("SELECT DISTINCT type FROM Questions")
        self.types = [e[0] for e in db.fetchall()]

        self.type_menu = QtWidgets.QGroupBox()
        type_layout = QtWidgets.QFormLayout(self.type_menu)
        for type in self.types:
            checkbox = QtWidgets.QCheckBox()
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(
                lambda allowed, type=type: self.types.append(type) if allowed else self.types.remove(type)
            )
            checkbox.stateChanged.connect(self.update_count_menu)
            type_layout.addRow(checkbox, QtWidgets.QLabel(type))
        # --
        layout.addRow('Типы вопросов', self.type_menu)
        #

        self.count_box.setValue(25)
        self.update_count_menu()

        u_layout.addLayout(layout)
        u_layout.addLayout(buttons_layout)

    def update_count_menu(self):
        db.cursor.execute("SELECT COUNT(*) FROM Questions WHERE type IN (%s)" % (', '.join('?' for _ in self.types),),
                          self.types)
        self.maximum = db.fetchone()[0]
        self.count_box.setMaximum(self.maximum)
        self.count_box.setValue(min(self.count_box.value(), self.maximum))

        self.count_slider.setMaximum(min(100, self.maximum))

    def start_test(self):
        self.main.question_tab.test = CustomizableTest(n=self.count_box.value(), type=self.types)
        self.main.set_tab(self.main.question_tab)


class QuestionTab(Tab):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._test = None
        self._question = None

        u_layout = QtWidgets.QVBoxLayout(self)

        layout = QtWidgets.QHBoxLayout()
        # data
        data_layout = QtWidgets.QVBoxLayout()
        # --image
        self.image_group = QtWidgets.QGroupBox()
        self.image_group.setLayout(QtWidgets.QVBoxLayout())

        self.image_label = QtWidgets.QLabel()
        self.image_label.setScaledContents(True)
        self.image_group.layout().addWidget(self.image_label)

        data_layout.addWidget(self.image_group, 1)
        self.image_group.hide()
        # --
        # --video
        self.video_group = QtWidgets.QGroupBox()
        self.video_group.setLayout(QtWidgets.QVBoxLayout())

        self.video_label = VideoPlayer()
        self.video_group.layout().addWidget(self.video_label)

        data_layout.addWidget(self.video_group, 1)
        self.video_group.hide()
        # --
        # --text
        self.text_group = QtWidgets.QGroupBox()
        self.text_group.setLayout(QtWidgets.QVBoxLayout())

        self.text_label = QtWidgets.QLabel()
        self.text_group.layout().addWidget(self.text_label)

        data_layout.addWidget(self.text_group)
        self.text_group.hide()
        # --
        layout.addLayout(data_layout, 3)
        #
        # answers
        answer_group = QtWidgets.QGroupBox()
        self.answer_layout = QtWidgets.QVBoxLayout(answer_group)
        self.answer_widgets: List[QtWidgets.QWidget] = []
        layout.addWidget(answer_group, 1)
        #

        u_layout.addLayout(layout)

        # buttons
        buttons_layout = QtWidgets.QHBoxLayout()

        self.end_button = QtWidgets.QPushButton()
        self.end_button.setText("Завершить")
        self.end_button.clicked.connect(self.end_test)
        buttons_layout.addWidget(self.end_button)

        self.skip_button = QtWidgets.QPushButton()
        self.skip_button.setText("Пропустить")
        self.skip_button.clicked.connect(self.skip)
        buttons_layout.addWidget(self.skip_button)

        self.next_button = QtWidgets.QPushButton()
        self.next_button.setText("Далее")
        self.next_button.clicked.connect(self.next)
        self.next_button.setDisabled(True)
        buttons_layout.addWidget(self.next_button)

        u_layout.addLayout(buttons_layout)

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
            var.setText(text)
            var.clicked.connect(lambda *args, n=n: self.answer(n))
            self.answer_widgets.append(var)
        for i in random.sample(self.answer_widgets, len(self.answer_widgets)):
            self.answer_layout.addWidget(i)

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
        self.text_label.setText(txt)
        self.text_group.show()

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


class StatsTab(Tab):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stats = {}
        self.patterns = {
            'total': "Total {total}",
            'correct': "Correct: {correct} {correct_percent:.2f}%",
            'skipped': "Skipped: {skipped} {skipped_percent:.2f}%",
            'incorrect': "Incorrect: {incorrect} {incorrect_percent:.2f}%"
        }
        layout = QtWidgets.QVBoxLayout(self)

        stats_layout = QtWidgets.QVBoxLayout()
        self.stat_widgets = {
            'total': QtWidgets.QLabel(),
            'correct': QtWidgets.QLabel(),
            'skipped': QtWidgets.QLabel(),
            'incorrect': QtWidgets.QLabel()
        }
        for v in self.stat_widgets.values():
            stats_layout.addWidget(v)
        layout.addLayout(stats_layout)

        back_button = QtWidgets.QPushButton()
        back_button.setText("Главное меню")
        back_button.clicked.connect(lambda: self.main.set_tab(self.main.main_menu))
        layout.addWidget(back_button)

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


class VideoPlayer(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QtWidgets.QVBoxLayout(self)

        self.video_player = QtMultimedia.QMediaPlayer(None,
                                                      QtMultimedia.QMediaPlayer.VideoSurface)
        self.video_player.error.connect(self.error)
        self.video_player.stateChanged.connect(self.media_state_changed)

        video_widget = QtMultimediaWidgets.QVideoWidget()
        self.video_player.setVideoOutput(video_widget)
        layout.addWidget(video_widget)

        control_layout = QtWidgets.QHBoxLayout()

        self.play_button = QtWidgets.QPushButton()
        self.play_button.setText("Play")
        self.play_button.clicked.connect(self.play)
        control_layout.addWidget(self.play_button)

        self.video_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.video_slider.setMinimum(0)
        self.video_slider.sliderMoved.connect(self.video_player.setPosition)
        self.video_player.durationChanged.connect(self.video_slider.setMaximum)
        self.video_player.positionChanged.connect(self.video_slider.setValue)
        control_layout.addWidget(self.video_slider)

        layout.addLayout(control_layout)

    @property
    def video(self):
        return self.video_player.media()

    @video.setter
    def video(self, path: str):
        if path and os.path.isfile(path):
            self.video_player.setMedia(
                QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(path))
            )
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
        from PyQt5 import QtNetwork
        logger.error("MediaPlayer error: " +
                     codes[code] + " " +
                     str(self.video_player.media().request().url()))


if __name__ == '__main__':
    main = Main()
    main.start()
    main.exit()
