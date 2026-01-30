import config
from PySide6 import QtWidgets, QtGui

# TODO rename to InfoWindow or smth like that (now it's used not only for errors)
class ErrorWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QtGui.QIcon(str(config.get_app_icon_path())))

        self.message_box = QtWidgets.QMessageBox(self)

    def show_error_message(self, message: str):
        self.message_box.setIcon(QtWidgets.QMessageBox.Warning)
        self.message_box.setWindowTitle("Ошибка")
        self.message_box.setText(message)
        self.message_box.exec()

    def show_info_message(self, message: str):
        self.message_box.setIcon(QtWidgets.QMessageBox.Information)
        self.message_box.setWindowTitle("Внимание")
        self.message_box.setText(message)
        self.message_box.exec()
