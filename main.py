import os
import sys
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import QListView
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

from pathlib import Path

allowed_types = [".jpeg", ".png", ".jpg", ".jfif"]


class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

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
        self.layout.addWidget(self.button, 0, QtCore.Qt.AlignHCenter)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.list)

        # connecting to the button click action
        self.button.clicked.connect(self.on_button_clicked)

    def clear_files_list(self, files_list):
        filtered = [
            f for f in files_list if os.path.splitext(f)[1].lower() in allowed_types
        ]
        return filtered

    # button click event
    @QtCore.Slot()
    def on_button_clicked(self):
        # QtWidgets.QMessageBox.information(self, "Внимание!", "Тестовое сообщение")
        files_dlg = QtWidgets.QFileDialog()
        files_list = []
        folder = files_dlg.getExistingDirectory()
        if folder:
            files_list = os.listdir(folder)
            files_list = self.clear_files_list(files_list)
            if files_list == []:
                QtWidgets.QMessageBox.information(
                    self,
                    "Ошибка!",
                    "Выбранная папка пуста или не содержит файлы поддерживаемых форматов.",
                )
            else:
                # self.list.addItems(files_list)
                for f in files_list:
                    icon_path = Path(__file__).parent / "testicon.png"
                    item = QtWidgets.QListWidgetItem(f)
                    item.setIcon(QIcon(str(icon_path)))
                    self.list.addItem(item)


if __name__ == "__main__":
    icon_path = Path(__file__).parent / "icon.ico"
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    widget.setWindowTitle("Media Manager")
    widget.setWindowIcon(QtGui.QIcon(str(icon_path)))

    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())
