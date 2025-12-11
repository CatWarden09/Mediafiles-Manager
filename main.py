import os
import sys
from PySide6 import QtCore, QtWidgets, QtGui

allowed_types = [".jpeg", ".png", ".jpg"]


class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.button = QtWidgets.QPushButton("Выбрать папку")
        self.button.setMaximumSize(200, 50)

        self.list = QtWidgets.QListWidget()

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.button, 0, QtCore.Qt.AlignHCenter)
        self.layout.addSpacing(10)

        self.layout.addWidget(self.list)

        self.button.clicked.connect(self.magic)

    def clear_files_list(self, files_list):
        filtered = [
            f for f in files_list if os.path.splitext(f)[1].lower() in allowed_types
        ]
        return filtered

    @QtCore.Slot()
    def magic(self):
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
                self.list.addItems(files_list)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    widget.setWindowTitle("Media Manager")
    # widget.setWindowIcon(QtGui.QIcon("icon.ico"))

    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())
