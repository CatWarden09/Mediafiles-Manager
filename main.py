import os
import sys
import config

from dotenv import load_dotenv
from fhandler import FileHandler, DatabaseHanlder


from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import QListView
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

from pathlib import Path

load_dotenv()

debug = True


class PreviewWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setMinimumWidth(300)

        # create placeholder for the preview
        self.image_preview = QtWidgets.QLabel()

        # create table for the file info
        self.table = QtWidgets.QFormLayout()
        self.table.addRow("Имя файла:", QtWidgets.QLabel("THIS IS A TEST TEXT!"))
        self.table.addRow("Путь к файлу:", QtWidgets.QLabel("THIS IS A TEST TEXT!"))

        # add the main layout for the window
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setSpacing(3)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # set the test image
        pixmap = QtGui.QPixmap(os.path.join(config.assign_script_dir(), "testicon.png")  )
        self.image_preview.setPixmap(pixmap)

        # add all the widgets
        self.layout.addWidget(self.image_preview)
        self.layout.addLayout(self.table)



class MainWidget(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        self.fhandler = FileHandler(db)

        self.is_folder_chosen = os.getenv("IS_FOLDER_CHOSEN", "False") == "True"

        # create button
        self.button = QtWidgets.QPushButton("Выбрать папку")
        self.button.setMaximumSize(200, 50)

        # create a widget for the files list
        self.list = QtWidgets.QListWidget()
        self.list.setViewMode(QListView.IconMode)
        self.list.setIconSize(QSize(128, 128))
        self.list.setResizeMode(QListView.ResizeMode.Adjust)
        self.list.setGridSize(QSize(150, 150))

        # create the file preview window
        self.preview_window = PreviewWindow()

        # add the files_list layout and all items
        self.list_layout = QtWidgets.QVBoxLayout()
        self.list_layout.addSpacing(10)
        if not self.is_folder_chosen or debug:
            self.list_layout.addWidget(self.button, 0, QtCore.Qt.AlignHCenter)
        self.list_layout.addSpacing(10)
        self.list_layout.addWidget(self.list)

        # create the main Hbox for all the widgets
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.addLayout(self.list_layout)
        self.layout.addWidget(self.preview_window)

        # connecting to the button click action
        self.button.clicked.connect(self.on_button_clicked)

    # button click event
    @QtCore.Slot()
    def on_button_clicked(self):
        db.connect_to_database()
        files_list = []

        files_dlg = QtWidgets.QFileDialog()
        folder = files_dlg.getExistingDirectory()
        # print(folder)
        if folder:
            # TODO make a separate function

            files_list = self.fhandler.clear_files_list(folder)
            if files_list == []:
                QtWidgets.QMessageBox.information(
                    self,
                    "Ошибка!",
                    "Выбранная папка пуста или не содержит файлы поддерживаемых форматов.",
                )
            else:
                self.fhandler.create_image_thumbnail(folder)
                self.fhandler.create_video_thumbnail(folder)
                # TODO: call a function with filename, which will go to the DB and get the thumbnail path via filename
                for file in files_list:

                    icon_path = db.get_previewpath(file["filename"])
                    # print("old icon path:", icon_path)

                    # convert the path to the first element of a tuple because SQLite returns a tuple with 1 element, and QIcon need string
                    icon_path = icon_path[0]

                    # print("new icon path:", icon_path)
                    item = QtWidgets.QListWidgetItem(file["filename"])
                    item.setIcon(QIcon(str(icon_path)))

                    self.list.addItem(item)

                if not debug:
                    self.button.deleteLater()

                config.save_to_env("IS_FOLDER_CHOSEN", "True")
                config.save_to_env("FOLDER_PATH", folder)
        db.save_changes()
        db.close_connection()


if __name__ == "__main__":

    db = DatabaseHanlder()

    icon_path = Path(__file__).parent / "icon.ico"
    app = QtWidgets.QApplication([])

    widget = MainWidget()
    widget.setWindowTitle(str("Media Manager v." + config.VERSION))
    widget.setWindowIcon(QtGui.QIcon(str(icon_path)))

    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())
