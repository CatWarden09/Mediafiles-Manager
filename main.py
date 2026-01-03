import os
import sys
import config

from dotenv import load_dotenv
from fhandler import FileHandler, DatabaseHandler


from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import QListView
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

from pathlib import Path

load_dotenv()

debug = False


class TagsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # create the main tags layout
        self.tags_group = QtWidgets.QButtonGroup(self)
        self.tags_group.setExclusive(False)

        self.tags_layout = QtWidgets.QGridLayout(self)

    def add_tag(self, tag_name: str):

        checkbox = QtWidgets.QCheckBox(tag_name)

        self.tags_layout.addWidget(checkbox)
        self.tags_group.addButton(checkbox)


class PreviewWindow(QtWidgets.QWidget):
    def __init__(self):

        super().__init__()

        self.setFixedWidth(300)

        # create placeholder for the preview
        self.image_preview = QtWidgets.QLabel()
        self.image_preview.setFixedSize(256, 256)
        self.image_preview.setAlignment(QtCore.Qt.AlignCenter)

        # create table for the file info
        self.table = QtWidgets.QFormLayout()
        self.table_filename = QtWidgets.QLabel()
        self.table_filepath = QtWidgets.QLabel()

        self.table.addRow("Имя файла:", self.table_filename)
        self.table.addRow("Путь к файлу:", self.table_filepath)

        # add the main layout for the window
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(3)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # set the test image
        # pixmap = QtGui.QPixmap(os.path.join(config.assign_script_dir(), "testicon.png"))
        # self.image_preview.setPixmap(pixmap)

        # add all the widgets
        self.layout.addWidget(self.image_preview)
        self.layout.addLayout(self.table)

    def apply_preview_data(self, icon, filename, filepath):
        pixmap = icon.pixmap(256, 256)
        filename = filename[0:35] + "..." if len(filename) > 35 else filename
        filepath = filepath[0:35] + "..." if len(filepath) > 35 else filepath

        self.table_filename.setText(filename)
        self.table_filepath.setText(filepath)

        self.image_preview.setPixmap(pixmap)


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.preview_window = PreviewWindow()
        self.tags_window = TagsWindow()

        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.is_folder_chosen = os.getenv("IS_FOLDER_CHOSEN", "False") == "True"

        # create add folder button
        self.button = QtWidgets.QPushButton("Выбрать папку")
        self.button.setMaximumSize(200, 50)

        # create tags settings button
        self.tags_button = QtWidgets.QPushButton("Настройка тегов")
        self.tags_button.setMaximumSize(200, 50)

        # create a widget for the files list
        self.list = QtWidgets.QListWidget()
        self.list.setViewMode(QListView.IconMode)
        self.list.setIconSize(QSize(128, 128))
        self.list.setResizeMode(QListView.ResizeMode.Adjust)
        self.list.setGridSize(QSize(150, 150))

        self.list.setDragEnabled(True)
        self.list.setDragDropMode(QtWidgets.QAbstractItemView.DragOnly)

        # add the files_list layout and all items, hide tags button and window
        self.list_layout = QtWidgets.QVBoxLayout()
        self.list_layout.addSpacing(10)
        self.list_layout.addWidget(self.button, 0, QtCore.Qt.AlignHCenter)
        self.list_layout.addWidget(self.tags_button, 0, QtCore.Qt.AlignHCenter)
        self.list_layout.addWidget(self.tags_window)
        self.list_layout.addSpacing(10)
        self.list_layout.addWidget(self.list)

        self.tags_button.hide()
        self.tags_window.hide()
        # create the Hbox for files list and file preview widgets and put it into the main Vbox

        self.files_layout = QtWidgets.QHBoxLayout()
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
            self.button.hide()
            self.tags_button.show()
            self.tags_window.show()
            self.display_files_list()

    # tags button click event
    @QtCore.Slot()
    def on_tags_button_clicked(self):
        pass

    # item click event
    @QtCore.Slot()
    def on_current_item_selected(self):
        preview_icon = self.list.currentItem().icon()
        preview_filename = self.list.currentItem().text()
        preview_filepath = db.get_previewpath(preview_filename)
        preview_filepath = preview_filepath[0]

        self.preview_window.apply_preview_data(
            preview_icon, preview_filename, preview_filepath
        )

    # button click event
    @QtCore.Slot()
    def on_button_clicked(self):

        files_list = []

        files_dlg = QtWidgets.QFileDialog()
        folder = files_dlg.getExistingDirectory()
        # print(folder)
        if folder:
            # TODO make a separate function

            files_list = fhandler.clear_files_list(folder)
            if files_list == []:
                QtWidgets.QMessageBox.information(
                    self,
                    "Ошибка!",
                    "Выбранная папка пуста или не содержит файлы поддерживаемых форматов.",
                )
            else:
                fhandler.create_image_thumbnail(folder)
                fhandler.create_video_thumbnail(folder)

                for file in files_list:

                    icon_path = db.get_previewpath(file["filename"])

                    # convert the path to the first element of a tuple because SQLite returns a tuple with 1 element, and QIcon need string
                    icon_path = icon_path[0]

                    item = QtWidgets.QListWidgetItem(file["filename"])
                    item.setIcon(QIcon(str(icon_path)))

                    self.list.addItem(item)
                # hide add folder button and show tags button and window
                if not debug:
                    self.button.hide()
                    self.tags_button.show()
                    self.tags_window.show()

                config.save_to_env("IS_FOLDER_CHOSEN", "True")
                config.save_to_env("FOLDER_PATH", folder)
        db.save_changes()

    def display_files_list(self):
        files_list = db.get_all_filenames()
        # print(files_list)
        for file in files_list:

            icon_path = db.get_previewpath(file[0])

            # convert the path to the first element of a tuple because SQLite returns a tuple with 1 element, and QIcon need string
            icon_path = icon_path[0]

            item = QtWidgets.QListWidgetItem(file[0])
            item.setIcon(QIcon(str(icon_path)))

            self.list.addItem(item)


if __name__ == "__main__":

    db = DatabaseHandler()
    db.connect_to_database()
    fhandler = FileHandler(db)

    icon_path = Path(__file__).parent / "icon.ico"
    app = QtWidgets.QApplication([])

    main_window = MainWindow()
    main_window.setWindowTitle(str("Media Manager v." + config.VERSION))
    main_window.setWindowIcon(QtGui.QIcon(str(icon_path)))

    main_window.resize(800, 600)
    main_window.show()

    sys.exit(app.exec())
