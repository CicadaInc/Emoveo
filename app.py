from test import *

from settings import *

from PyQt5 import QtCore, QtWidgets, QtGui
import sys


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

        self.count_label = QtWidgets.QSpinBox()
        self.count_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)

        self.count_label.setMinimum(0)
        self.count_label.valueChanged.connect(self.count_slider.setValue)
        self.count_label.valueChanged.connect(lambda n: self.start_button.setDisabled(n < 1))
        self.count_label.setMinimumWidth(50)
        self.count_label.setMaximumWidth(150)

        self.count_slider.setMinimum(0)
        self.count_slider.setTickInterval(10)
        self.count_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.count_slider.valueChanged.connect(self.count_label.setValue)

        count_layout.addWidget(self.count_slider, 9)
        count_layout.addWidget(self.count_label, 1)
        # --
        layout.addRow('Количество вопросов', count_menu)
        # --Настройка типов
        db.cursor.execute("SELECT DISTINCT type FROM Questions")
        self.types = [e[0] for e in db.fetchall()]

        self.type_check = QtWidgets.QGroupBox()
        type_layout = QtWidgets.QFormLayout(self.type_check)
        for type in self.types:
            checkbox = QtWidgets.QCheckBox()
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(
                lambda allowed, type=type: self.types.append(type) if allowed else self.types.remove(type)
            )
            checkbox.stateChanged.connect(self.update_count_menu)
            type_layout.addRow(checkbox, QtWidgets.QLabel(type))
        # --
        layout.addRow('Типы вопросов', self.type_check)
        #

        self.count_label.setValue(25)
        self.update_count_menu()

        u_layout.addLayout(layout)
        u_layout.addLayout(buttons_layout)

    def update_count_menu(self):
        db.cursor.execute("SELECT COUNT(*) FROM Questions WHERE type IN (%s)" % (', '.join('?' for _ in self.types),),
                          self.types)
        self.maximum = db.fetchone()[0]
        self.count_label.setMaximum(self.maximum)
        self.count_label.setValue(min(self.count_label.value(), self.maximum))

        self.count_slider.setMaximum(min(100, self.maximum))

    def start_test(self):
        self.main.question_tab
        self.main.set_tab(self.main.question_tab)

    def end_test(self):
        self.main.set_tab(self.main.stats_tab)


class QuestionTab(Tab):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class StatsTab(Tab):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


if __name__ == '__main__':
    main = Main()
    main.start()
    main.exit()
