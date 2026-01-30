import config

from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Signal


class FileDescriptionDialog(QtWidgets.QDialog):
    description_updated = Signal(str)

    def __init__(self, current_item, current_item_description, db, error_window):
        super().__init__()

        self.current_item = current_item
        self.current_item_description = current_item_description
        self.db = db
        self.error_window = error_window

        self.setWindowTitle("Изменить описание файла")
        self.setWindowIcon(QtGui.QIcon(str(config.get_app_icon_path())))
        self.dialog_window_layout = QtWidgets.QVBoxLayout()

        self.text_edit = QtWidgets.QTextEdit()
        self.text_edit.setText(current_item_description)

        self.setLayout(self.dialog_window_layout)

        self.buttons_box = QtWidgets.QHBoxLayout()
        self.confirm_button = QtWidgets.QPushButton("Сохранить")
        self.cancel_button = QtWidgets.QPushButton("Отменить")
        self.buttons_box.addWidget(self.confirm_button)
        self.buttons_box.addWidget(self.cancel_button)

        self.dialog_window_layout.addWidget(self.text_edit)
        self.dialog_window_layout.addLayout(self.buttons_box)

        self.confirm_button.clicked.connect(self.on_confirm_button_clicked)
        self.cancel_button.clicked.connect(self.on_cancel_button_clicked)


    def on_confirm_button_clicked(self):
        new_text = self.text_edit.toPlainText()
        current_text = self.current_item_description

        if new_text != current_text:
            self.db.update_file_description(self.current_item, new_text)
            self.description_updated.emit(new_text)
            self.close()
        else:
            self.close()

    def on_cancel_button_clicked(self):
        self.close()
