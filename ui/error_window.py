import config
from PySide6 import QtWidgets, QtGui

class ErrorWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QtGui.QIcon(str(config.get_app_icon_path())))

        self.message_box = QtWidgets.QMessageBox(self)
        self.message_box.setIcon(QtWidgets.QMessageBox.Warning)

    def show_error_message(self, message: str):
        self.message_box.setWindowTitle("Ошибка")
        self.message_box.setText(message)
        self.message_box.exec()
