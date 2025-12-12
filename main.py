import os
import sys
import config

from dotenv import load_dotenv
from fhandler import FileHandler

from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import QListView
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

from pathlib import Path

load_dotenv()

debug = True


class MainWidget(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        self.is_folder_chosen = os.getenv("IS_FOLDER_CHOSEN", "False") == "True"

        # create button
        self.button = QtWidgets.QPushButton("Выбрать папку")
        self.button.setMaximumSize(200, 50)

        # create a widget for the files list
        self.list = QtWidgets.QListWidget()
        self.list.setViewMode(QListView.IconMode)
        self.list.setIconSize(QSize(128, 128))
        self.list.setResizeMode(QListView.ResizeMode.Adjust)
        self.list.setGridSize(QSize(150, 150))

        # add the main layout and all items
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addSpacing(10)
        if not self.is_folder_chosen or debug:
            self.layout.addWidget(self.button, 0, QtCore.Qt.AlignHCenter)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.list)

        # connecting to the button click action
        self.button.clicked.connect(self.on_button_clicked)

    # button click event
    @QtCore.Slot()
    def on_button_clicked(self):

        files_list = []

        files_dlg = QtWidgets.QFileDialog()
        folder = files_dlg.getExistingDirectory()

        if folder:
            files_list = os.listdir(folder)
            files_list = FileHandler.clear_files_list(files_list)
            if files_list == []:
                QtWidgets.QMessageBox.information(
                    self,
                    "Ошибка!",
                    "Выбранная папка пуста или не содержит файлы поддерживаемых форматов.",
                )
            else:
                for f in files_list:
                    icon_path = Path(__file__).parent / "testicon.png"
                    item = QtWidgets.QListWidgetItem(f)
                    item.setIcon(QIcon(str(icon_path)))
                    self.list.addItem(item)

                if not debug:
                    self.button.deleteLater()

                config.save_to_env("IS_FOLDER_CHOSEN", "True")
                config.save_to_env("FOLDER_PATH", folder)


if __name__ == "__main__":
    icon_path = Path(__file__).parent / "icon.ico"
    app = QtWidgets.QApplication([])

    widget = MainWidget()
    widget.setWindowTitle(str("Media Manager v." + config.VERSION))
    widget.setWindowIcon(QtGui.QIcon(str(icon_path)))

    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())
