from ui import (
    ItemTagsSettingsWindow,
)  # need to import the window here because of the import loop that breaks the program

# (if the import would be inside ui>init.py)
from .file_description_dialog import FileDescriptionDialog

from PySide6 import QtCore, QtWidgets


class PreviewWindow(QtWidgets.QWidget):
    def __init__(self, main_window, tags_list, db, error_window):

        super().__init__()

        self.db = db
        self.error_window = error_window
        self.main_window = main_window

        self.tags_settings_window = ItemTagsSettingsWindow(
            self.main_window, self, tags_list, self.db, self.error_window
        )

        self.setFixedWidth(300)

        # create tags settings button
        self.tags_settings_button = QtWidgets.QPushButton("Изменить теги")
        self.item_description_button = QtWidgets.QPushButton("Изменить описание")

        # create placeholder for the preview
        self.image_preview = QtWidgets.QLabel()
        self.image_preview.setFixedSize(256, 256)
        self.image_preview.setAlignment(QtCore.Qt.AlignCenter)

        # create table for the file info
        self.table = QtWidgets.QFormLayout()
        self.table_filename = QtWidgets.QTextEdit()
        self.table_filepath = QtWidgets.QTextEdit()
        self.table_filetags = QtWidgets.QTextEdit()
        self.table_description = QtWidgets.QTextEdit()

        self.table_filename.setReadOnly(True)
        self.table_filename.setMaximumHeight(100)

        self.table_filepath.setReadOnly(True)
        self.table_filepath.setMaximumHeight(100)

        self.table_filetags.setReadOnly(True)
        self.table_filetags.setMaximumHeight(100)

        self.table_description.setReadOnly(True)
        self.table_description.setMaximumHeight(100)

        self.table.addRow("Имя файла:", self.table_filename)
        self.table.addRow("Путь к файлу:", self.table_filepath)
        self.table.addRow("Список тегов:", self.table_filetags)
        self.table.addRow("Описание файла:", self.table_description)

        # add the main layout for the window
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(3)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # add all the widgets
        self.layout.addWidget(self.image_preview)
        self.layout.addLayout(self.table)
        self.layout.addWidget(self.tags_settings_button)
        self.layout.addWidget(self.item_description_button)

        # connect to the buttons clicked signals
        self.tags_settings_button.clicked.connect(self.on_tags_settings_button_clicked)
        self.item_description_button.clicked.connect(
            self.on_item_description_button_clicked
        )

    def apply_preview_data(self, icon, filename, filepath):

        pixmap = icon.pixmap(256, 256)

        # update the tags list for the current selected item
        self.update_item_tags_list(filename)
        self.table_description.setText(self.db.get_file_description(filename))

        self.table_filename.setText(filename)
        self.table_filepath.setText(filepath)

        self.image_preview.setPixmap(pixmap)

    def update_item_tags_list(self, file):

        tags_list = [tag for tag in self.db.get_current_item_tags(file)]
        list_unpacked = ", ".join(tags_list)
        self.table_filetags.setText(list_unpacked)

    def update_item_description(self, description):
        self.table_description.setText(description)

    @QtCore.Slot()
    def on_tags_settings_button_clicked(self):
        if self.main_window.get_current_item() is not None:
            self.tags_settings_window.show()
            self.tags_settings_window.set_tags_list()

    @QtCore.Slot()
    def on_item_description_button_clicked(self):
        current_item = self.main_window.get_current_item()
        if current_item:
            current_item_name = current_item.text()

            current_item_description = self.db.get_file_description(current_item_name)

            if current_item_name:
                self.dialog = FileDescriptionDialog(
                    current_item_name,
                    current_item_description,
                    self.db,
                    self.error_window,
                )
                self.dialog.description_updated.connect(self.on_description_updated)
                self.dialog.exec()

    @QtCore.Slot()
    def on_description_updated(self, description):
        self.update_item_description(description)

