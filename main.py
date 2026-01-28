import os, sys
import config

from dotenv import load_dotenv
from fhandler import FileHandler, FileScanner
from database import DatabaseHandler


from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import QListView, QProgressBar
from PySide6.QtCore import QSize
from PySide6.QtCore import QThread
from PySide6.QtGui import QIcon

from ui import (
    FoldersListWindow,
    SearchBar,
    FileDragList,
    ErrorWindow,
    TagsSettingsWindow,
    ItemTagsSettingsWindow,
)

load_dotenv()

debug = False


# TODO add "select all" and "deselect all" buttons
class TagsList(QtWidgets.QWidget):
    def __init__(self, main_window, db):
        super().__init__()

        self.main_window = main_window
        self.db = db

        # create the main tags layout
        self.tags_layout = QtWidgets.QVBoxLayout(self)

        self.tags_widget = QtWidgets.QListWidget()

        self.tags_layout.addWidget(self.tags_widget)

        self.changed_items = []

        # self.tags_widget.itemChanged.connect(self.on_item_changed)

    def update_tags_list(self):
        self.tags_widget.clear()

        tags_list = self.db.get_all_tagnames()

        for tag in tags_list:

            checkbox = QtWidgets.QListWidgetItem(tag)

            # | is a bitwise OR to add the item flag without changing all the existing flags
            # it compares every bit in flags() and assigns 1 to the byte at ItemIsUserCheckable position
            # flags() returns a combination of all the item flags enum constants as an int (bit mask)
            checkbox.setFlags(checkbox.flags() | QtCore.Qt.ItemIsUserCheckable)

            checkbox.setCheckState(QtCore.Qt.Unchecked)
            self.tags_widget.addItem(checkbox)

    def get_selected_tags(self):
        selected_tags = []

        for i in range(self.tags_widget.count()):
            item = self.tags_widget.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                selected_tags.append(item.text())

        return selected_tags

    def deselect_all_tags(self):
        for i in range(self.tags_widget.count()):
            item = self.tags_widget.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                item.setCheckState(QtCore.Qt.Unchecked)


class PreviewWindow(QtWidgets.QWidget):
    def __init__(self, main_window, tags_list, db, error_window):

        super().__init__()

        self.db = db
        self.error_window = error_window
        self.tags_settings_window = ItemTagsSettingsWindow(
            main_window, self, tags_list, self.db, self.error_window
        )
        self.main_window = main_window

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
            description, ok = QtWidgets.QInputDialog.getText(
                self, "Изменить описание", "Введите новое описание файла"
            )
            if ok:
                if description.strip():
                    self.db.update_file_description(current_item.text(), description)
                    self.update_item_description(description)
                else:
                    self.error_window.show_error_message("Укажите описание файла!")
        else:
            return


class ThumbCreationThread(QThread):
    def __init__(self, fhandler, folder):
        super().__init__()
        self.fhandler = fhandler
        self.folder = folder

    def run(self):
        self.fhandler.clear_files_list(self.folder)


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # create the database object
        self.db = DatabaseHandler()
        self.db.connect_to_database()

        # create the error window
        self.error_window = ErrorWindow()

        # create the progress bar
        self.progress_bar = QProgressBar()

        # create the file handler
        self.fhandler = FileHandler(self.db)
        self.fhandler.progress.connect(self.on_progress)
        self.fhandler.finished.connect(self.on_finished)
        self.fhandler.thumb_created.connect(self.on_thumb_created)

        # create the file scanner
        self.fscanner = FileScanner(self.db, self.fhandler)

        # IoC for the dependent classes which use tags list, db and error window
        self.tags_list = TagsList(self, self.db)
        self.preview_window = PreviewWindow(
            self, self.tags_list, self.db, self.error_window
        )
        self.searchbar = SearchBar(self, self.tags_list, self.db)

        # create the main folders list window
        self.folder_list_window = FoldersListWindow(self)

        # create the tags settings window
        self.tags_settings_window = TagsSettingsWindow(
            self.tags_list, self.db, self.error_window
        )

        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.is_folder_chosen = os.getenv("IS_FOLDER_CHOSEN", "False") == "True"

        # create add folder button
        self.button = QtWidgets.QPushButton("Выбрать папку")
        self.button.setMaximumSize(200, 50)

        # create tags settings button
        self.tags_button = QtWidgets.QPushButton("Настройка тегов")
        self.tags_button.setMaximumSize(200, 50)

        # create a widget for the files list
        self.list = FileDragList(self.db)
        self.list.setViewMode(QListView.IconMode)
        self.list.setIconSize(QSize(128, 128))
        self.list.setResizeMode(QListView.ResizeMode.Adjust)
        self.list.setGridSize(QSize(150, 150))
        self.list.setDragEnabled(True)
        self.list.setDragDropMode(QtWidgets.QAbstractItemView.DragOnly)

        # add the files_list layout and all items
        self.list_layout = QtWidgets.QVBoxLayout()
        self.list_layout.addSpacing(10)
        self.list_layout.addWidget(self.button, 0, QtCore.Qt.AlignHCenter)
        self.list_layout.addWidget(self.tags_button, 0, QtCore.Qt.AlignHCenter)
        self.list_layout.addWidget(self.searchbar)
        self.list_layout.addWidget(self.tags_list)
        self.list_layout.addSpacing(10)
        self.list_layout.addWidget(self.list)
        self.list_layout.addSpacing(10)
        self.list_layout.addWidget(self.progress_bar)
        # hide tags button, window and searchbar
        self.tags_button.hide()
        self.tags_list.hide()
        self.searchbar.hide()
        self.progress_bar.hide()

        # create the Hbox for files list and file preview widgets and put it into the main Vbox
        self.files_layout = QtWidgets.QHBoxLayout()
        self.files_layout.addWidget(self.folder_list_window)
        self.files_layout.addLayout(self.list_layout)
        self.files_layout.addWidget(self.preview_window)

        self.main_layout.addLayout(self.files_layout)

        # connecting to the button click action
        self.button.clicked.connect(self.on_button_clicked)

        # connecting to the item click
        self.list.itemClicked.connect(self.on_current_item_selected)

        # connecting to the tags button click
        self.tags_button.clicked.connect(self.on_tags_button_clicked)

        # if the folder is already chosen on program launch, hide the folder and show the tags button and window
        if self.is_folder_chosen:
            folder = os.getenv("FOLDER_PATH")
            self.button.hide()
            self.tags_button.show()
            self.tags_list.show()
            self.searchbar.show()
            self.tags_list.update_tags_list()
            self.display_files_list(folder, "program_launch")
            self.folder_list_window.display_folder_list(folder)

            difference_found = []
            difference_found = self.fscanner.compare_files_count()
            if "new_files" in difference_found:
                self.error_window.show_error_message(
                    "Обнаружены новые файлы! Выполняется создание превью"
                )
            if "deleted_files" in difference_found:
                self.error_window.show_error_message(
                    "Обнаружены удаленные файлы! Выполняется удаление данных из программы"
                )
            elif len(difference_found) == 2:
                self.error_window.show_error_message(
                    "Обнаружена разница в количестве файлов. Выполняется удаление старых и создание превью для новых файлов"
                )

    def get_current_item(self):
        current_item = self.list.currentItem()
        if current_item:
            return self.list.currentItem()
        else:
            self.error_window.show_error_message("Не выбран ни один файл!")

    # tags button click event
    @QtCore.Slot()
    def on_tags_button_clicked(self):
        self.tags_settings_window.show()
        self.tags_settings_window.update_tags_list()

    # item click event
    @QtCore.Slot()
    def on_current_item_selected(self):
        preview_icon = self.list.currentItem().icon()
        preview_filename = self.list.currentItem().text()
        preview_filepath = self.db.get_filepath(preview_filename)
        preview_filepath = preview_filepath

        self.preview_window.apply_preview_data(
            preview_icon, preview_filename, preview_filepath
        )

    # button click event
    @QtCore.Slot()
    def on_button_clicked(self):

        filepaths_list = []

        files_dlg = QtWidgets.QFileDialog()
        folder = files_dlg.getExistingDirectory()
        folder = os.path.abspath(os.path.normpath(folder))

        self.thumb_thread = ThumbCreationThread(self.fhandler, folder)
        if folder:

            filepaths_list = self.thumb_thread.start()
            self.progress_bar.show()

            if filepaths_list == []:
                QtWidgets.QMessageBox.information(
                    self,
                    "Ошибка!",
                    "Выбранная папка пуста или не содержит файлы поддерживаемых форматов.",
                )

                # hide add folder button and show tags button and window
                # if not debug:

    @QtCore.Slot(str, str, str, list)
    def on_thumb_created(self, filename, filepath, thumb_filepath, tags):
        self.db.save_to_database(filename, filepath, thumb_filepath)
        self.db.save_current_item_tags(filename, tags)
        self.db.save_changes()

    def on_progress(self, counter, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(counter)

    def on_finished(self, folder):
        self.display_files_list(folder, "program_launch")
        self.folder_list_window.display_folder_list(folder)
        self.progress_bar.hide()
        config.save_to_env("IS_FOLDER_CHOSEN", "True")
        config.save_to_env("FOLDER_PATH", folder)

        # load the .env after updating for file scanner to get the correct folder (in case of first program launch)
        load_dotenv()
        self.fscanner.compare_files_count()

        if not debug:
            self.button.hide()
            self.tags_button.show()
            self.tags_list.show()
            self.searchbar.show()
            self.tags_list.update_tags_list()

    def display_files_list(self, files_list_source, keyword: str):
        # define the files list source depending on where this method is called from
        match keyword:
            case "program_launch" | "searchbar_canceled":
                files_list = self.db.get_all_filenames()
            case "searchbar_clicked":
                files_list = files_list_source
            case "folder_tree":
                files_list = self.db.get_files_by_filepath(files_list_source)
            case _:
                files_list = []

        self.list.clear()

        for file in files_list:

            icon_path = self.db.get_previewpath_by_filename(file)

            item = QtWidgets.QListWidgetItem(file)
            item.setIcon(QIcon(str(icon_path)))

            self.list.addItem(item)


if __name__ == "__main__":

    app = QtWidgets.QApplication([])

    # create the main program window
    main_window = MainWindow()
    main_window.setWindowTitle(str("Media Manager v." + config.VERSION))
    main_window.setWindowIcon(QtGui.QIcon(str(config.get_app_icon_path())))
    main_window.resize(1280, 720)

    main_window.show()

    sys.exit(app.exec())
