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
    TagsList,
    PreviewWindow,
)

load_dotenv()

debug = False


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
