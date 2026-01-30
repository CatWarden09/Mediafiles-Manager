import os
import config

from dotenv import load_dotenv

from fhandler import FileHandler, FileScanner
from database import DatabaseHandler

from PySide6 import QtCore, QtWidgets
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


class ThumbCreationThread(QThread):
    def __init__(self, fhandler, filepaths):
        super().__init__()
        
        self.fhandler = fhandler
        self.filepaths = filepaths

        self.folder = config.get_files_folder_path()
        self.thumb_folder = config.get_thumb_folder_path()

    def run(self):
        self.fhandler.create_thumbnails(self.filepaths)


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
        self.button.clicked.connect(self.on_choose_folder_button_clicked)

        # connecting to the item click
        self.list.itemClicked.connect(self.on_current_item_selected)

        # connecting to the tags button click
        self.tags_button.clicked.connect(self.on_tags_button_clicked)

        # connect to the searchbar clicked signal
        self.searchbar.clicked.connect(self.on_searchbar_clicked)

        # connect to file scanner signal which emits when the new files are found
        self.fscanner.files_scanned.connect(self.on_files_scanned) 

        # if the folder is already chosen on program launch, hide the folder and show the tags button and window
        if self.is_folder_chosen:
            folder = os.getenv("FOLDER_PATH")
            self.button.hide()
            self.tags_button.show()
            self.tags_list.show()
            self.searchbar.show()
            self.tags_list.update_tags_list()

            difference_found = []
            difference_found = self.fscanner.compare_files_count()
            # need a timer to avoid the case when the info message is shown before the program main window
            if "new_files" in difference_found:
                QtCore.QTimer.singleShot(200, lambda: self.error_window.show_info_message(
                    "Обнаружены новые файлы! Выполняется создание превью"
                ))

            if "deleted_files" in difference_found:
                QtCore.QTimer.singleShot(200, lambda: self.error_window.show_info_message(
                    "Обнаружены удаленные файлы! Выполняется удаление данных из программы"
                ))

            elif len(difference_found) == 2:
                QtCore.QTimer.singleShot(200, lambda: self.error_window.show_info_message(
                    "Обнаружена разница в количестве файлов. Выполняется удаление старых и создание превью для новых файлов"
                ))


            self.display_files_list(folder, "program_launch")
            self.folder_list_window.display_folder_list(folder)

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

    # choose folder button click event
    @QtCore.Slot()
    def on_choose_folder_button_clicked(self):
        files_dialog = QtWidgets.QFileDialog()
        folder = files_dialog.getExistingDirectory()
        folder = os.path.abspath(os.path.normpath(folder))
        
        if folder:
            thumbs_dialog = QtWidgets.QFileDialog()
            thumb_folder = thumbs_dialog.getExistingDirectory()
            thumb_folder = os.path.abspath(os.path.normpath(thumb_folder))

            
            if thumb_folder:
                files_list = self.fhandler.clear_files_list(folder)
                if files_list:
                    config.save_to_env("IS_FOLDER_CHOSEN", "True")
                    config.save_to_env("FOLDER_PATH", folder)
                    config.save_to_env("THUMB_FOLDER_PATH", thumb_folder)
                    self.create_thumbnail_thread(files_list)
                else:
                    self.error_window.show_error_message("Выбранная папка пуста или не содержит файлы поддерживаемых форматов.")

    # create the separate thread for thumbnail creation
    def create_thumbnail_thread(self, files_list):
        self.thumb_thread = ThumbCreationThread(self.fhandler, files_list)
        self.thumb_thread.start()
        self.progress_bar.show()




    @QtCore.Slot(str, str, str, list)
    def on_thumb_created(self, filename, filepath, thumb_filepath, tags):
        self.db.save_to_database(filename, filepath, thumb_filepath)
        self.db.save_current_item_tags(filename, tags)
        self.db.save_changes()


    @QtCore.Slot(int,int)
    def on_progress(self, counter, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(counter)

    @QtCore.Slot(str)
    def on_finished(self, folder):
        self.display_files_list(folder, "program_launch")
        # folder here is passed since the display_files_list method signature needs an argument for the file list source, but in this case the folder is never used in the method
        self.folder_list_window.display_folder_list(folder)
        self.progress_bar.hide()


        # load the .env after updating for file scanner to get the correct folder (in case of first program launch)
        load_dotenv()
        self.fscanner.compare_files_count()

        if not config.DEBUG:
            self.button.hide()
            self.tags_button.show()
            self.tags_list.show()
            self.searchbar.show()
            self.tags_list.update_tags_list()
    
    @QtCore.Slot(set)
    # create a thumbnail creation thread for the new files found on next program launches
    def on_files_scanned(self, files_list):
        self.create_thumbnail_thread(files_list)


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

    # clear the folder list selection when the searchbar actions are made
    def on_searchbar_clicked(self):
        self.folder_list_window.clear_selection()
