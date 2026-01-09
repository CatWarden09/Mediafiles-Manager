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


class ErrorWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QtGui.QIcon(str(icon_path)))

        self.message_box = QtWidgets.QMessageBox(self)
        self.message_box.setIcon(QtWidgets.QMessageBox.Warning)

    def show_error_message(self, message: str):
        self.message_box.setWindowTitle("Ошибка")
        self.message_box.setText(message)
        self.message_box.exec()


class TagsSettingsWindow(QtWidgets.QWidget):
    # TODO add confirm window when deleting a tag
    def __init__(self, tags_list):
        super().__init__()

        self.main_tags_list = tags_list

        self.setWindowIcon(QtGui.QIcon(str(icon_path)))
        self.setWindowTitle("Настройки тегов")
        self.resize(600, 400)

        # create the window layout
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.tags_list = QtWidgets.QListWidget()

        # create manage buttons
        self.add_button = QtWidgets.QPushButton("Добавить тег")
        self.delete_button = QtWidgets.QPushButton("Удалить тег")

        # add widgets to the layouts
        self.buttons_layout.addWidget(self.add_button)
        self.buttons_layout.addWidget(self.delete_button)
        self.main_layout.addLayout(self.buttons_layout)
        self.main_layout.addWidget(self.tags_list)

        # connect to buttons click
        self.add_button.clicked.connect(self.on_add_button_clicked)
        self.delete_button.clicked.connect(self.on_delete_button_clicked)

    def add_tags_to_list(self, tag):
        item = QtWidgets.QListWidgetItem(tag)

        self.tags_list.addItem(item)

    def update_tags_list(self):
        self.tags_list.clear()

        tags_list = db.get_all_tagnames()

        for tag in tags_list:
            item = QtWidgets.QListWidgetItem(tag[0])

            self.tags_list.addItem(item)

    # button click events
    @QtCore.Slot()
    def on_add_button_clicked(self):
        tag_name, ok = QtWidgets.QInputDialog.getText(
            self, "Новый тег", "Введите название тега"
        )

        if ok:
            if tag_name.strip():
                if not db.tag_exists(tag_name):
                    db.save_tag_to_database(tag_name)
                    self.add_tags_to_list(tag_name)
                    self.main_tags_list.update_tags_list()
                else:
                    error_window.show_error_message(
                        "Тег с таким названием уже добавлен!"
                    )
            else:
                error_window.show_error_message("Укажите название тега!")

    @QtCore.Slot()
    def on_delete_button_clicked(self):
        item = self.tags_list.currentItem()

        if item is None:
            error_window.show_error_message("Выберите тег для удаления!")
        else:
            tag = item.text()
            db.delete_tag_from_database(tag)
            self.update_tags_list()
            self.main_tags_list.update_tags_list()


class ItemTagsSettingsWindow(TagsSettingsWindow):
    def __init__(self, main_window, preview_window, tags_list):
        super().__init__(tags_list)
        self.setWindowTitle("Изменить теги")
        self.main_window = main_window
        self.preview_window = preview_window

        self.common_tags_list_label = QtWidgets.QLabel("Доступные теги:")
        self.current_tags_list_label = QtWidgets.QLabel("Теги выбранного файла:")

        # hide the parent's tags list because here we need 2 separate tag lists
        self.tags_list.hide()

        # create a VBox to separate lists labels and the lists themselves
        self.main_vbox = QtWidgets.QVBoxLayout()

        # create an HBox for lists labels
        self.labels_hbox = QtWidgets.QHBoxLayout()

        # add the lists labels to their Hbox
        self.labels_hbox.addWidget(self.common_tags_list_label)
        self.labels_hbox.addWidget(self.current_tags_list_label)

        # create a Hbox for 2 tags lists
        self.list_hbox = QtWidgets.QHBoxLayout()
        self.common_tags_list = QtWidgets.QListWidget()
        self.current_tags_list = QtWidgets.QListWidget()
        self.common_tags_list.setSelectionMode(
            QtWidgets.QAbstractItemView.MultiSelection
        )
        self.current_tags_list.setSelectionMode(
            QtWidgets.QAbstractItemView.MultiSelection
        )

        # add common and current tags lists to the tags list layout
        self.list_hbox.addWidget(self.common_tags_list)
        self.list_hbox.addWidget(self.current_tags_list)

        # place the Hboxes inside the main Vbox
        self.main_vbox.addLayout(self.labels_hbox)
        self.main_vbox.addLayout(self.list_hbox)

        # add the tags list layout to the main layout
        self.main_layout.addLayout(self.main_vbox)

    def set_tags_list(self):
        # prepare both tags list for display
        # define current selected item, then get tags_list from the DB and make 2 tuples for current item tags and available tags accordinly
        # clear both lists to avoid tags duplication on next settings window openings
        # after lists are ready, call update_lists function to display both lists in the current item tags settings window
        current_item = self.main_window.get_current_item().text()

        self.common_tags_list.clear()
        self.current_tags_list.clear()

        self.current_tags_tuple = db.get_current_item_tags(current_item)
        self.common_tags_tuple = [
            tag for tag in db.get_all_tagnames() if tag not in self.current_tags_tuple
        ]

        self.update_lists(self.current_tags_list, self.current_tags_tuple)
        self.update_lists(self.common_tags_list, self.common_tags_tuple)

    # update both lists using the same method to avoid code duplication
    def update_lists(self, target_list, tags_list):
        for tag in tags_list:
            item = QtWidgets.QListWidgetItem(tag[0])

            target_list.addItem(item)

    @QtCore.Slot()
    def on_add_button_clicked(self):
        # get current selected item from the main window and current selected tags from available tags list
        # and save the selected tags for the selected file in the DB
        # also update tags list in the file preview window
        current_item = self.main_window.get_current_item().text()
        selected_tags_list = self.common_tags_list.selectedItems()

        if selected_tags_list != []:
            selected_tags = [tag.text() for tag in selected_tags_list]
            db.save_current_item_tags(current_item, selected_tags)
            self.set_tags_list()
            self.preview_window.update_item_tags_list(current_item)
        else:
            error_window.show_error_message("Не выбран ни один тег для добавления!")

    @QtCore.Slot()
    def on_delete_button_clicked(self):
        current_item = self.main_window.get_current_item().text()
        selected_tags_list = self.current_tags_list.selectedItems()

        if selected_tags_list != []:
            selected_tags = [tag.text() for tag in selected_tags_list]
            db.delete_current_item_tags(current_item, selected_tags)
            self.set_tags_list()
            self.preview_window.update_item_tags_list(current_item)
        else:
            error_window.show_error_message("Не выбран ни один тег для удаления!")


class TagsList(QtWidgets.QWidget):
    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window

        # create the main tags layout
        self.tags_layout = QtWidgets.QVBoxLayout(self)

        self.tags_widget = QtWidgets.QListWidget()

        self.tags_layout.addWidget(self.tags_widget)

        self.changed_items = []

        self.tags_widget.itemChanged.connect(self.on_item_changed)

    def update_tags_list(self):
        self.tags_widget.clear()

        tags_list = db.get_all_tagnames()

        for tag in tags_list:

            checkbox = QtWidgets.QListWidgetItem(tag[0])

            # | is a bitwise OR to add the item flag without changing all the existing flags
            # it compares every bit in flags() and assigns 1 to the byte at ItemIsUserCheckable position
            # flags() returns a combination of all the item flags enum constants as an int (bit mask)
            checkbox.setFlags(checkbox.flags() | QtCore.Qt.ItemIsUserCheckable)

            checkbox.setCheckState(QtCore.Qt.Unchecked)
            self.tags_widget.addItem(checkbox)

    @QtCore.Slot()
    def on_item_changed(self, item: QtWidgets.QListWidgetItem):

        if item.checkState() == QtCore.Qt.Checked:
            if item.text() not in self.changed_items:
                self.changed_items.append(item.text())
        else:
            if item.text() in self.changed_items:
                self.changed_items.remove(item.text())
        if len(self.changed_items) >= 1:
            self.search_files = db.get_files_by_tags(self.changed_items)
        else:
            self.search_files = ["Null"]

        self.main_window.display_files_list(self.search_files)


class PreviewWindow(QtWidgets.QWidget):
    def __init__(self, main_window, tags_list):

        super().__init__()

        self.tags_settings_window = ItemTagsSettingsWindow(main_window, self, tags_list)
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
        self.table_filename = QtWidgets.QLabel()
        self.table_filepath = QtWidgets.QLabel()
        self.table_filetags = QtWidgets.QLabel()

        self.table.addRow("Имя файла:", self.table_filename)
        self.table.addRow("Путь к файлу:", self.table_filepath)
        self.table.addRow("Список тегов:", self.table_filetags)

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
        # TODO add files description and search by it

        pixmap = icon.pixmap(256, 256)

        # update the tags list for the current selected item
        self.update_item_tags_list(filename)

        filename = filename[0:35] + "..." if len(filename) > 35 else filename
        filepath = filepath[0:35] + "..." if len(filepath) > 35 else filepath

        self.table_filename.setText(filename)
        self.table_filepath.setText(filepath)

        self.image_preview.setPixmap(pixmap)

    def update_item_tags_list(self, file):

        tags_list = [tag[0] for tag in db.get_current_item_tags(file)]
        list_unpacked = ", ".join(tags_list)
        self.table_filetags.setText(list_unpacked)

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
                self, "Изменить описание", "Введите описание файла"
            )
            if ok:
                if description.strip():
                    db.update_file_description(current_item.text(), description)

                else:
                    error_window.show_error_message("Укажите описание файла!")
        else:
            return


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.tags_list = TagsList(self)
        self.preview_window = PreviewWindow(self, self.tags_list)

        # create the tags settings window
        self.tags_settings_window = TagsSettingsWindow(self.tags_list)

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
        self.list_layout.addWidget(self.tags_list)
        self.list_layout.addSpacing(10)
        self.list_layout.addWidget(self.list)

        self.tags_button.hide()
        self.tags_list.hide()

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
            self.tags_list.show()
            self.tags_list.update_tags_list()
            self.display_files_list(["Null"])

    def get_current_item(self):
        current_item = self.list.currentItem()
        if current_item:
            return self.list.currentItem()
        else:
            error_window.show_error_message("Не выбран ни один файл!")

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
        preview_filepath = db.get_filepath(preview_filename)
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
                    self.tags_list.show()

                config.save_to_env("IS_FOLDER_CHOSEN", "True")
                config.save_to_env("FOLDER_PATH", folder)
        db.save_changes()

    def display_files_list(self, search_list):
        self.list.clear()

        if search_list == ["Null"]:
            files_list = db.get_all_filenames()
        elif search_list:
            files_list = search_list
        else:
            files_list = []

        for file in files_list:

            icon_path = db.get_previewpath(file[0])

            # convert the path to the first element of a tuple because SQLite returns a tuple with 1 element, and QIcon need string
            icon_path = icon_path[0]

            item = QtWidgets.QListWidgetItem(file[0])
            item.setIcon(QIcon(str(icon_path)))

            self.list.addItem(item)


if __name__ == "__main__":

    icon_path = Path(__file__).parent / "icon.ico"
    app = QtWidgets.QApplication([])

    db = DatabaseHandler()
    db.connect_to_database()

    fhandler = FileHandler(db)
    error_window = ErrorWindow()

    # create the main program window
    main_window = MainWindow()
    main_window.setWindowTitle(str("Media Manager v." + config.VERSION))
    main_window.setWindowIcon(QtGui.QIcon(str(icon_path)))
    main_window.resize(800, 600)

    main_window.show()

    sys.exit(app.exec())
